from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
import pandas as pd
from src.logger_config import get_logger
from typing import Dict, List, Tuple

logger = get_logger(__name__)


class DataAvailabilityVisualizer(BaseVisualizer):
    """
    Visualiseur pour la disponibilité des données SCADA.

    Génère un graphique à barres horizontales empilées avec:
    - Axe X: Temps (périodes horaires)
    - Axe Y: Variables par turbine (wind_speed, active_power, pitch, etc.)
    - Couleurs: Vert (≥95%), Jaune (30-95%), Rouge (<30%)
    - Format type Gantt chart pour voir la disponibilité temporelle
    """

    def __init__(self):
        super().__init__(chart_name="data_availability_chart", use_plotly=True)

    def _calculate_optimal_tickformat(self, timestamps: pd.Series) -> dict:
        """
        Determine optimal X-axis formatting based on data time span.

        Args:
            timestamps: All timestamps in the availability data

        Returns:
            Dict with xaxis configuration parameters
        """
        if len(timestamps) == 0:
            return {}

        time_span_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0

        # Configuration pour les longues périodes (> 6 mois)
        if time_span_days > 180:
            return {
                "tickformat": "%b %Y",
                "dtick": "M3",  # On affiche un tick tous les 3 mois pour aérer
                "tickangle": 0,
            }
        # Configuration pour les périodes moyennes (1 à 6 mois)
        elif time_span_days > 31:
            return {
                "tickformat": "%d %b",
                "dtick": "M1",  # Un tick par mois
                "tickangle": 0,
            }
        # Configuration pour les courtes périodes (< 1 mois)
        else:
            return {
                "tickformat": "%d/%m %H:%M",
                "dtick": 3600000 * 12,  # Toutes les 12 heures
                "tickangle": -45,
            }

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        turbine_results = result.detailed_results
        turbine_ids = sorted(turbine_results.keys())
        y_labels = []
        traces = []

        variables = ["wind_speed", "active_power", "wind_direction", "temperature"]
        variable_display_names = {
            "wind_speed": "ws",
            "active_power": "power",
            "wind_direction": "dir",
            "temperature": "temp",
        }

        for turbine_id in reversed(turbine_ids):
            turbine_result = turbine_results[turbine_id]
            if "error" in turbine_result:
                continue
            availability_df = turbine_result["availability_table"]

            for var in variables:
                if var not in availability_df.columns:
                    continue
                short_name = variable_display_names.get(var, var)
                y_label = f"{short_name}_{turbine_id}"
                y_labels.append(y_label)
                self._add_availability_bars(
                    traces, availability_df, var, y_label, turbine_id
                )

        fig = go.Figure(data=traces)

        fig.update_layout(
            title={
                "text": (
                    "<b>SCADA Data Availability - Operational Parameters</b><br>"
                    "<span style='font-size:12px; color:gray;'>Availability computed as proportion of valid 1-hour data points</span>"
                ),
                "x": 0.5,
                "y": 0.95,
                "xanchor": "center",
                "yanchor": "top",
            },
            xaxis_title="Time",
            yaxis_title=None,  # On peut enlever le titre Y car les labels sont explicites
            barmode="overlay",
            # On réduit bargap pour rendre les barres plus épaisses
            bargap=0.05,
            height=max(600, len(y_labels) * 30),
            showlegend=True,
            # Légende centrée en haut
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
            ),
            # Marges ajustées
            margin=dict(l=120, r=40, t=140, b=80),
            plot_bgcolor="rgba(240,240,240,0.5)",  # Un fond gris très léger pour mieux voir les trous
            yaxis=dict(
                categoryorder="array",
                categoryarray=y_labels,
                gridcolor="white",
                showgrid=True,
            ),
            xaxis=dict(
                type="date",
                showgrid=True,
                gridcolor="white",
                **self._calculate_optimal_tickformat(
                    pd.concat(
                        [
                            turbine_results[tid]["availability_table"]["timestamp"]
                            for tid in turbine_ids
                            if "availability_table" in turbine_results[tid]
                        ]
                    ) if any("availability_table" in turbine_results[tid] for tid in turbine_ids)
                    else pd.Series(dtype='datetime64[ns]')  # Series vide si pas de données
                ),
            ),
        )

        return fig

    def _add_availability_bars(
        self,
        traces: list,
        availability_df: pd.DataFrame,
        variable: str,
        y_label: str,
        turbine_id: str,
    ):
        timestamps = pd.to_datetime(availability_df["timestamp"])
        values = availability_df[variable].values

        segments = self._group_consecutive_segments(timestamps, values)

        for segment_start, segment_end, segment_value in segments:
            if segment_value == 1:
                color = "#2ca02c"  # Vert
                legend_group = "good"
                legend_name = "Good (>95%)"
            elif segment_value == 0:
                color = "#FFA500"  # Orange
                legend_group = "unavailable"
                legend_name = "Unavailable (0%)"
            else:
                color = "#ff7f0e"
                legend_group = "partial"
                legend_name = "Partial (30-95%)"

            show_legend = not any(
                getattr(trace, "legendgroup", None) == legend_group for trace in traces
            )

            # --- CORRECTION 1: Calculer la durée en millisecondes pour Plotly ---
            duration_ms = (segment_end - segment_start).total_seconds() * 1000.0
            # Garder la durée en heures pour le texte de survol (hover)
            duration_hours = (segment_end - segment_start).total_seconds() / 3600.0

            status_text = {
                1: "Available (100%)",
                0: "Unavailable (0%)",
            }.get(segment_value, f"Partial ({segment_value*100:.0f}%)")

            traces.append(
                go.Bar(
                    x=[duration_ms],  # Largeur en ms
                    y=[y_label],
                    orientation="h",
                    marker=dict(
                        color=color, line_width=0
                    ),  # line_width=0 pour éviter les contours blancs
                    base=segment_start.isoformat() if hasattr(segment_start, 'isoformat') else segment_start,  # Date de début
                    legendgroup=legend_group,
                    name=legend_name,
                    showlegend=show_legend,
                    hovertemplate=(
                        f"<b>{turbine_id} - {variable}</b><br>"
                        f"Start: {segment_start.strftime('%Y-%m-%d %H:%M')}<br>"
                        f"End: {segment_end.strftime('%Y-%m-%d %H:%M')}<br>"
                        f"Duration: {duration_hours:.1f}h<br>"
                        f"Status: {status_text}"
                        "<extra></extra>"
                    ),
                )
            )

    def _group_consecutive_segments(
        self, timestamps: pd.Series, values: pd.Series
    ) -> List[Tuple[pd.Timestamp, pd.Timestamp, int]]:
        segments = []
        if len(timestamps) == 0:
            return segments

        if isinstance(timestamps, pd.DatetimeIndex):
            timestamps = timestamps.to_series().reset_index(drop=True)

        # Déterminer le pas de temps moyen (ex: 1 jour ou 1 heure)
        # pour étendre le dernier segment jusqu'à la fin de sa période
        if len(timestamps) > 1:
            delta = timestamps.iloc[1] - timestamps.iloc[0]
        else:
            delta = pd.Timedelta(hours=1)

        current_start = timestamps.iloc[0]
        current_value = values[0]

        for i in range(1, len(timestamps)):
            if values[i] != current_value:
                # --- CORRECTION 2: Le segment finit au début du timestamp suivant ---
                segments.append((current_start, timestamps.iloc[i], current_value))
                current_start = timestamps.iloc[i]
                current_value = values[i]

        # Ajouter le dernier segment en ajoutant le delta pour couvrir sa durée
        segments.append((current_start, timestamps.iloc[-1] + delta, current_value))

        return segments
