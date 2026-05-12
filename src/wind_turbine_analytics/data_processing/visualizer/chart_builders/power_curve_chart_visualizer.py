from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
from typing import Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from src.logger_config import get_logger

logger = get_logger(__name__)


class PowerCurveChartVisualizer(BaseVisualizer):
    """
    Visualiseur de courbe de puissance.

    Génère un graphique avec grid layout (1 subplot par turbine):
    - Axe X: Wind Speed [m/s]
    - Axe Y: Active Power [kW]
    - Points scatter avec les données réelles
    - Ligne horizontale pour le seuil de puissance nominale
    """

    def __init__(self):
        super().__init__(chart_name="power_curve_chart", use_plotly=True)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        """
        Crée la figure Plotly avec grid layout pour toutes les turbines.

        Args:
            result: Résultat de NominalPowerAnalyzer

        Returns:
            Figure Plotly avec subplots
        """
        if not result.detailed_results:
            logger.warning("Aucune donnée détaillée pour générer la courbe de puissance")
            return self._create_empty_figure()

        # Nombre de turbines
        turbine_ids = list(result.detailed_results.keys())
        n_turbines = len(turbine_ids)

        # Calculer la disposition du grid: maximum 2 colonnes
        n_cols = min(n_turbines, 2)  # Max 2 colonnes
        n_rows = (n_turbines + n_cols - 1) // n_cols  # Arrondi supérieur

        # Créer les subplots
        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            subplot_titles=[f"WTG {tid}" for tid in turbine_ids],
            x_title="Wind Speed [m/s]",
            y_title="Active Power [kW]",
            vertical_spacing=0.12,
            horizontal_spacing=0.1,
        )

        # Ajouter les données pour chaque turbine
        for idx, turbine_id in enumerate(turbine_ids):
            turbine_data = result.detailed_results[turbine_id]

            # Position dans le grid
            row = (idx // n_cols) + 1
            col = (idx % n_cols) + 1

            # Récupérer les données chart_data (DataFrame avec wind_speed et power)
            chart_data = turbine_data.get("chart_data")

            if chart_data is None or chart_data.empty:
                logger.warning(f"Pas de données pour {turbine_id}")
                continue

            # Scatter plot des données réelles
            fig.add_trace(
                go.Scattergl(
                    x=chart_data["wind_speed"],
                    y=chart_data["power"],
                    mode="markers",
                    marker=dict(size=3, color="rgba(31, 119, 180, 0.6)"),
                    name=f"{turbine_id} - Data",
                    showlegend=(idx == 0),  # Légende seulement pour le premier
                ),
                row=row,
                col=col,
            )

            # Ligne horizontale pour le seuil de puissance nominale
            power_threshold = turbine_data.get("power_threshold_kW", 0)
            nominal_power = turbine_data.get("nominal_power_kW", 0)

            if power_threshold > 0:
                # Ligne du seuil
                fig.add_trace(
                    go.Scatter(
                        x=[chart_data["wind_speed"].min(), chart_data["wind_speed"].max()],
                        y=[power_threshold, power_threshold],
                        mode="lines",
                        line=dict(color="red", dash="dash", width=2),
                        name=f"Threshold ({turbine_data.get('power_threshold_percent', 97)}%)",
                        showlegend=(idx == 0),
                    ),
                    row=row,
                    col=col,
                )

            # Ligne de puissance nominale
            if nominal_power > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[chart_data["wind_speed"].min(), chart_data["wind_speed"].max()],
                        y=[nominal_power, nominal_power],
                        mode="lines",
                        line=dict(color="green", dash="dot", width=2),
                        name="Nominal Power (100%)",
                        showlegend=(idx == 0),
                    ),
                    row=row,
                    col=col,
                )

        # Mise en page globale
        fig.update_layout(
            title="Power Curve Analysis - All Turbines",
            height=400 * n_rows,
            width=1200,
            template="plotly_white",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
        )

        # Mettre à jour les axes
        fig.update_xaxes(title_text="Wind Speed [m/s]", showgrid=True)
        fig.update_yaxes(title_text="Active Power [kW]", showgrid=True)

        return fig

    def _create_empty_figure(self) -> go.Figure:
        """Crée une figure vide en cas de données manquantes."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for power curve",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="red"),
        )
        fig.update_layout(
            title="Power Curve Analysis",
            height=400,
            width=600,
            template="plotly_white",
        )
        return fig
