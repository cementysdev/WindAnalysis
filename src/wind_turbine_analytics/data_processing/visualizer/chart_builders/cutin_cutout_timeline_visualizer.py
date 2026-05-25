from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.logger_config import get_logger

logger = get_logger(__name__)


class CutInCutoutTimelineVisualizer(BaseVisualizer):
    """
    Visualiseur de timeline amélioré pour les tests Cut-in/Cut-out.
    Affiche RUN, STOP et UNAUTHORIZED STOP par turbine.
    """

    def __init__(self, output_dir=None):
        super().__init__(
            chart_name="cutin_cutout_timeline_chart",
            use_plotly=True,
            output_dir=output_dir
        )

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            logger.warning("Aucune donnée détaillée pour la timeline")
            return self._create_empty_figure()

        # Configuration des couleurs
        color_map = {
            "RUN": "#2ecc71",  # Vert
            "STOP": "#e74c3c",  # Rouge
            "UNAUTHORIZED STOP": "#f39c12",  # Orange
            "DATA GAP": "#bdc3c7",  # Gris
        }

        fig = go.Figure()

        # Pour ne pas répéter les légendes
        added_labels = set()

        for turbine_id, turbine_data in result.detailed_results.items():
            all_periods = turbine_data.get("all_periods", [])

            if not all_periods:
                continue

            for period in all_periods:
                start = period.get("start")
                end = period.get("end")
                if start is None or end is None:
                    continue

                # Détermination du statut précis
                is_available = period.get("is_available", False)
                unauthorized_hours = period.get("unauthorized_stop_hours", 0)

                if is_available:
                    status = "RUN"
                elif unauthorized_hours > 0:
                    status = "UNAUTHORIZED STOP"
                else:
                    status = "STOP"

                # Calcul de la durée
                duration_ms = (end - start).total_seconds() * 1000

                # ✅ ASTUCE : Si durée nulle (même timestamp), on met 10min
                # pour qu'un trait soit visible sur le graphique
                display_duration = max(duration_ms, 10 * 60 * 1000)

                alarm_codes = period.get("alarm_codes", [])
                alarm_text = ", ".join(alarm_codes) if alarm_codes else "None"

                # Construction de la barre
                fig.add_trace(
                    go.Bar(
                        base=start,
                        x=[display_duration],
                        y=[turbine_id],
                        orientation="h",
                        marker_color=color_map.get(status, "#34495e"),
                        name=status,
                        showlegend=(status not in added_labels),
                        legendgroup=status,
                        hovertemplate=(
                            f"<b>WTG {turbine_id}</b><br>"
                            f"Status: {status}<br>"
                            f"Start: {start.strftime('%Y-%m-%d %H:%M')}<br>"
                            f"End: {end.strftime('%Y-%m-%d %H:%M')}<br>"
                            f"Duration: {period.get('gross_duration_hours', 0):.2f}h<br>"
                            f"Alarms: {alarm_text}<br>"
                            f"Unauth. Stop: {unauthorized_hours:.2f}h"
                            "<extra></extra>"
                        ),
                    )
                )
                added_labels.add(status)

        # Mise en page
        fig.update_layout(
            title="Timeline de Fonctionnement et Arrêts par Turbine",
            xaxis=dict(
                title="Temps",
                type="date",
                tickformat="%d/%m %H:%M",
                showgrid=True,
                gridcolor="rgba(0,0,0,0.1)",
            ),
            yaxis=dict(
                title="Turbines",
                categoryorder="array",
                categoryarray=list(result.detailed_results.keys())[
                    ::-1
                ],  # Inverse pour E1 en haut
            ),
            barmode="stack",
            height=max(400, len(result.detailed_results) * 100),
            width=1200,
            template="plotly_white",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=80, r=40, t=100, b=60),
        )

        return fig

    def _create_empty_figure(self) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text="No timeline data available",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=18),
        )
        return fig
