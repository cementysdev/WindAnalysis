from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
import pandas as pd
from src.logger_config import get_logger
import numpy as np

logger = get_logger(__name__)


class TbaCutInCutOutVisualizer(BaseVisualizer):
    """
    Visualiseur pour la disponibilité temporelle (TBA - Time Based Availability).

    Génère un graphique en lignes avec:
    - Axe X: Périodes mensuelles
    - Axe Y: Disponibilité temporelle (0-100%)
    - Une ligne par turbine
    - Une ligne pour la moyenne du parc éolien (pointillés)
    - Support PNG + JSON pour dashboard web futur
    """

    def __init__(self, output_dir=None):
        super().__init__(chart_name="tba_cut_in_cut_out_chart", use_plotly=True, output_dir=output_dir)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        """
        Crée la figure Plotly avec toutes les turbines sur le même graphe.

        Args:
            result: Résultat de TbACutInCutOutAnalyzer contenant:
                - availability_pct: float (disponibilité globale en %)
                - monthly_availability: list[dict] avec 'month' et 'availability_pct'

        Returns:
            Figure Plotly avec lignes
        """
        if not result.detailed_results:
            logger.warning("Aucune donnée détaillée pour générer le graphique TBA")
            return self._create_empty_figure()

        turbine_ids = list(result.detailed_results.keys())

        # Créer la figure
        fig = go.Figure()

        # Palette de couleurs pour les turbines
        colors = [
            "#1f77b4",  # Bleu
            "#ff7f0e",  # Orange
            "#2ca02c",  # Vert
            "#d62728",  # Rouge
            "#9467bd",  # Violet
            "#8c564b",  # Marron
            "#e377c2",  # Rose
            "#7f7f7f",  # Gris
            "#bcbd22",  # Olive
            "#17becf",  # Cyan
        ]

        # Collecter toutes les périodes uniques pour la moyenne du parc
        all_months = set()
        monthly_data_by_turbine = {}
        all_months_sorted = []  # Initialiser pour éviter UnboundLocalError
        wind_farm_avg = []  # Initialiser pour éviter UnboundLocalError

        # Ajouter une ligne pour chaque turbine
        for idx, turbine_id in enumerate(turbine_ids):
            turbine_data = result.detailed_results[turbine_id]

            # Vérifier si on a un résultat valide
            if "error" in turbine_data:
                logger.warning(
                    f"Erreur dans les données de {turbine_id}: {turbine_data.get('error')}"
                )
                continue

            # Récupérer les données mensuelles
            monthly_data = turbine_data.get("monthly_availability", [])

            if not monthly_data:
                logger.warning(f"Pas de données mensuelles pour {turbine_id}")
                continue

            # Convertir en DataFrame
            df_monthly = pd.DataFrame(monthly_data)

            if (
                "month" not in df_monthly.columns
                or "availability_pct" not in df_monthly.columns
            ):
                logger.warning(f"Colonnes manquantes pour {turbine_id}")
                continue

            # Convertir les périodes en strings
            df_monthly["month_str"] = df_monthly["month"].astype(str)

            # Stocker pour calcul de moyenne
            monthly_data_by_turbine[turbine_id] = df_monthly
            all_months.update(df_monthly["month_str"].tolist())

            # Ajouter la ligne de la turbine
            color = colors[idx % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=df_monthly["month_str"],
                    y=df_monthly["availability_pct"],
                    mode="lines+markers",
                    name=turbine_id,
                    line=dict(color=color, width=2),
                    marker=dict(size=6, color=color),
                    hovertemplate=(
                        f"<b>{turbine_id}</b><br>"
                        "Période: %{x}<br>"
                        "Disponibilité: %{y:.2f}%<br>"
                        "<extra></extra>"
                    ),
                )
            )

        # Calculer et ajouter la moyenne du parc éolien
        if monthly_data_by_turbine:
            # Trier les mois chronologiquement
            all_months_sorted = sorted(list(all_months))

            # Calculer la moyenne pour chaque mois
            wind_farm_avg = []
            for month in all_months_sorted:
                availabilities = []
                for turbine_id, df in monthly_data_by_turbine.items():
                    month_data = df[df["month_str"] == month]
                    if not month_data.empty:
                        availabilities.append(month_data["availability_pct"].iloc[0])

                if availabilities:
                    wind_farm_avg.append(np.mean(availabilities))
                else:
                    wind_farm_avg.append(None)

            # Ajouter la ligne de moyenne du parc
            fig.add_trace(
                go.Scatter(
                    x=all_months_sorted,
                    y=wind_farm_avg,
                    mode="lines",
                    name="Wind farm",
                    line=dict(color="black", width=2.5, dash="dash"),
                    marker=dict(size=0),
                    hovertemplate=(
                        "<b>Moyenne Parc</b><br>"
                        "Période: %{x}<br>"
                        "Disponibilité: %{y:.2f}%<br>"
                        "<extra></extra>"
                    ),
                )
            )

        # Mise en page
        fig.update_layout(
            title={
                "text": "Time-based Availability (TbA) - Cut-in / Cut-out period<br>"
                "<sub>Monthly evolution per WTG and wind farm average</sub>",
                "font": {"size": 14},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis=dict(
                title="Period (Month)",
                showgrid=True,
                gridcolor="lightgray",
                tickangle=-45,
                tickmode="array",
                tickvals=all_months_sorted,
                ticktext=all_months_sorted,
            ),
            yaxis=dict(
                title="",  # Pas de titre sur Y, juste les valeurs
                showgrid=True,
                gridcolor="lightgray",
                range=[0, 105],  # Plage 0-105%
                ticksuffix="%",
            ),
            height=600,
            width=1100,
            template="plotly_white",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
            ),
            hovermode="x unified",  # Afficher toutes les valeurs pour un mois donné
        )

        return fig

    def _create_empty_figure(self) -> go.Figure:
        """Crée une figure vide en cas de données manquantes."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for TBA analysis",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="red"),
        )
        fig.update_layout(
            title="Time Based Availability Analysis",
            height=400,
            width=600,
            template="plotly_white",
        )
        return fig
