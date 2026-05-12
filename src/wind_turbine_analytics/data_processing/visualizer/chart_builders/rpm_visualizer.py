import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import plotly.express as px  # Pour générer une palette de couleurs facilement
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class RPMVisualizer(BaseVisualizer):
    def __init__(self):
        super().__init__(chart_name="rpm_chart", use_plotly=True)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            return self._create_empty_figure()

        turbine_ids = sorted(result.detailed_results.keys())
        n_turbines = len(turbine_ids)

        # Récupérer la liste de tous les mois pour créer une palette de couleurs cohérente
        all_months = set()
        for tid in turbine_ids:
            df = result.detailed_results[tid].get("chart_data")
            if df is not None and not df.empty and "month" in df.columns:
                all_months.update(df["month"].unique())
        all_months = sorted(list(all_months))

        # Création d'une palette de couleurs fixe pour les mois
        # (ex: Janvier sera toujours de la même couleur sur tous les subplots)
        colors = px.colors.qualitative.Plotly
        month_color_map = {
            month: colors[i % len(colors)] for i, month in enumerate(all_months)
        }

        # Grille de subplots: maximum 2 colonnes par ligne
        n_cols = min(2, n_turbines)
        n_rows = (n_turbines + n_cols - 1) // n_cols  # Division arrondie vers le haut

        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            subplot_titles=[f"<b>Turbine {tid}</b>" for tid in turbine_ids],
            shared_yaxes=False,
            horizontal_spacing=0.12,
            vertical_spacing=0.15,
        )

        for t_idx, turbine_id in enumerate(turbine_ids):
            row = (t_idx // n_cols) + 1
            col = (t_idx % n_cols) + 1
            turbine_data = result.detailed_results[turbine_id]
            df = turbine_data.get("chart_data")

            if df is None or df.empty:
                continue

            # On boucle sur chaque mois pour créer une trace séparée (indispensable pour la légende)
            # mais on les ajoute au même subplot (même col)
            for month in all_months:
                df_month = df[df["month"] == month].copy()
                if df_month.empty:
                    continue

                # Nettoyage et conversion
                x_col = (
                    "active_power"
                    if "active_power" in df_month.columns
                    else "activation_power"
                )
                df_month[x_col] = pd.to_numeric(df_month[x_col], errors="coerce")
                df_month["rpm"] = pd.to_numeric(df_month["rpm"], errors="coerce")
                df_month = df_month.dropna(subset=[x_col, "rpm"])

                if len(df_month) > 1000:
                    df_month = df_month.sample(n=1000, random_state=42)

                fig.add_trace(
                    go.Scatter(
                        x=df_month[x_col],
                        y=df_month["rpm"],
                        mode="markers",
                        name=str(month),
                        marker=dict(
                            size=3,
                            color=month_color_map[month],
                            opacity=0.6,  # Opacité réduite pour mieux voir la superposition
                        ),
                        # On affiche la légende seulement pour le premier subplot
                        # pour éviter d'avoir N fois chaque mois dans la légende
                        showlegend=(t_idx == 0),
                        legendgroup=str(
                            month
                        ),  # Groupe pour cliquer sur un mois et l'isoler partout
                        hovertemplate=(
                            f"Mois: {month}<br>"
                            "Puissance: %{x:.1f} kW<br>"
                            "RPM: %{y:.1f}<extra></extra>"
                        ),
                    ),
                    row=row,
                    col=col,
                )

        # Configuration des axes et du layout
        height = 400 + (n_rows * 350)  # Hauteur dynamique selon nombre de lignes
        fig.update_layout(
            title={
                "text": "<b>Analyse RPM par Turbine - Comparaison Mensuelle Superposée</b>",
                "x": 0.5,
            },
            height=height,
            template="plotly_white",
            legend_title_text="Mois",
            margin=dict(t=100, b=50, l=80, r=50),
        )

        # Mise à jour des axes pour tous les subplots
        fig.update_xaxes(title_text="Puissance (kW)", gridcolor="#f0f0f0")
        fig.update_yaxes(title_text="RPM (tr/min)", gridcolor="#f0f0f0")

        return fig

    def _create_empty_figure(self) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", showarrow=False)
        return fig
