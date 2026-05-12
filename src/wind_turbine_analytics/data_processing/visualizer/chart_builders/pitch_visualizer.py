import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class PitchVisualizer(BaseVisualizer):
    """
    Visualiseur de l'angle de pitch des 3 pales en fonction de la vitesse du vent.

    Génère un scatter plot avec:
    - Axe X: Vitesse du vent (m/s)
    - Axe Y: Angle de pitch (°)
    - 3 traces par turbine (une par pale) avec couleurs distinctes

    Permet d'identifier:
    - Le comportement du pitch à différentes vitesses de vent
    - La synchronisation entre les 3 pales
    - La stabilité du pitch en production (faibles vitesses)
    - La régulation du pitch à hautes vitesses
    - Les anomalies et désynchronisations
    """

    def __init__(self):
        super().__init__(chart_name="pitch_chart", use_plotly=True)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            return self._create_empty_figure()

        turbine_ids = sorted(result.detailed_results.keys())
        n_turbines = len(turbine_ids)

        # Grille de subplots: maximum 2 colonnes par ligne
        n_cols = min(2, n_turbines)
        n_rows = (n_turbines + n_cols - 1) // n_cols

        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            subplot_titles=[f"<b>Turbine {tid}</b>" for tid in turbine_ids],
            shared_yaxes=False,
            horizontal_spacing=0.12,
            vertical_spacing=0.15,
        )

        # Couleurs fixes pour les 3 pales
        blade_colors = {
            "pitch1": "#1f77b4",  # Bleu
            "pitch2": "#ff7f0e",  # Orange
            "pitch3": "#2ca02c",  # Vert
        }
        blade_names = {
            "pitch1": "Blade 1",
            "pitch2": "Blade 2",
            "pitch3": "Blade 3",
        }

        for t_idx, turbine_id in enumerate(turbine_ids):
            row = (t_idx // n_cols) + 1
            col = (t_idx % n_cols) + 1
            turbine_data = result.detailed_results[turbine_id]
            df = turbine_data.get("chart_data")

            if df is None or df.empty:
                continue

            # Nettoyage et conversion
            df = df.copy()
            df["wind_speed"] = pd.to_numeric(df["wind_speed"], errors="coerce")
            df["pitch1"] = pd.to_numeric(df["pitch1"], errors="coerce")
            df["pitch2"] = pd.to_numeric(df["pitch2"], errors="coerce")
            df["pitch3"] = pd.to_numeric(df["pitch3"], errors="coerce")
            df = df.dropna(subset=["wind_speed", "pitch1", "pitch2", "pitch3"])

            # Échantillonnage si trop de données
            if len(df) > 1000:
                df = df.sample(n=1000, random_state=42)

            # Ajouter une trace pour chaque pale
            for blade_col, blade_color in blade_colors.items():
                fig.add_trace(
                    go.Scatter(
                        x=df["wind_speed"],
                        y=df[blade_col],
                        mode="markers",
                        name=blade_names[blade_col],
                        marker=dict(
                            size=3,
                            color=blade_color,
                            opacity=0.5,
                        ),
                        showlegend=(
                            t_idx == 0
                        ),  # Légende seulement pour la première turbine
                        legendgroup=blade_col,
                        hovertemplate=(
                            f"{blade_names[blade_col]}<br>"
                            "Vitesse vent: %{x:.1f} m/s<br>"
                            "Pitch: %{y:.1f}°<extra></extra>"
                        ),
                    ),
                    row=row,
                    col=col,
                )

        # Configuration des axes et du layout
        height = 400 + (n_rows * 350)
        fig.update_layout(
            title={
                "text": "<b>Analyse Pitch par Turbine - 3 Pales</b>",
                "x": 0.5,
            },
            height=height,
            template="plotly_white",
            legend_title_text="Pales",
            margin=dict(t=100, b=50, l=80, r=50),
        )

        # Mise à jour des axes pour tous les subplots
        fig.update_xaxes(title_text="Vitesse du vent (m/s)", gridcolor="#f0f0f0")
        fig.update_yaxes(title_text="Pitch (°)", gridcolor="#f0f0f0")

        return fig

    def _create_empty_figure(self) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", showarrow=False)
        return fig
