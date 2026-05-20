from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from src.logger_config import get_logger

logger = get_logger(__name__)


class WindDirectionCalibrationVisualizer(BaseVisualizer):
    def __init__(self):
        super().__init__(chart_name="wind_direction_calibration", use_plotly=True)

    def _create_empty_figure(self) -> go.Figure:
        """Create an empty figure with an informative message."""
        fig = go.Figure()
        fig.update_layout(
            title={
                "text": "<b>Analyse de Calibration - Direction du Vent</b>",
                "x": 0.5,
            },
            template="plotly_white",
            height=400,
        )
        fig.add_annotation(
            text="Aucune donnée disponible pour la calibration de direction du vent.<br>"
            "Vérifiez que les colonnes wind_direction et nacelle_position sont configurées.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        return fig

    def _calculate_optimal_tickformat(self, timestamps: pd.Series) -> dict:
        """Détermine un formatage lisible sans secondes/minutes inutiles."""
        if len(timestamps) == 0:
            return {}

        time_span_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0

        # On simplifie les formats pour éviter les chevauchements
        if time_span_days > 180:
            return {"tickformat": "%b %Y", "dtick": "M3", "tickangle": 0}
        elif time_span_days > 31:
            return {"tickformat": "%d %b", "dtick": "M1", "tickangle": 0}
        else:
            # Pour moins d'un mois, on met le jour et le mois
            return {"tickformat": "%d %b", "dtick": 86400000 * 2, "tickangle": 0}

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            return self._create_empty_figure()

        turbine_ids = sorted(result.detailed_results.keys())
        n_turbines = len(turbine_ids)
        n_rows = n_turbines * 2

        # Correction 1: shared_xaxes=True pour lier les zooms et aligner les axes
        fig = make_subplots(
            rows=n_rows,
            cols=1,
            shared_xaxes=True,
            subplot_titles=[
                item
                for tid in turbine_ids
                for item in [
                    f"<b>{tid}</b> - Écart Angulaire Moyen",
                    f"<b>{tid}</b> - Corrélation",
                ]
            ],
            vertical_spacing=0.02,  # Espacement réduit car l'axe X est partagé
            row_heights=[1] * n_rows,
        )

        all_timestamps = []
        valid_turbines = []  # Track turbines with valid data

        for idx, turbine_id in enumerate(turbine_ids):
            turbine_data = result.detailed_results[turbine_id]
            if "error" in turbine_data:
                logger.warning(
                    f"Turbine {turbine_id} has error: {turbine_data['error']}"
                )
                continue

            daily_calibration = turbine_data.get("daily_calibration", [])
            if not daily_calibration:
                logger.warning(
                    f"Turbine {turbine_id} has no daily_calibration data"
                )
                continue

            df_daily = pd.DataFrame(daily_calibration)
            if df_daily.empty:
                logger.warning(
                    f"Turbine {turbine_id} daily_calibration DataFrame is empty"
                )
                continue

            # Convert to datetime and then to string format for Plotly compatibility
            df_daily["date"] = pd.to_datetime(df_daily["date"]).dt.strftime("%Y-%m-%d")
            all_timestamps.extend(pd.to_datetime(df_daily["date"]).tolist())
            valid_turbines.append(turbine_id)  # Mark this turbine as having valid data

            threshold = turbine_data.get("threshold_degrees", 5.0)
            overall_mean = turbine_data.get("overall_mean_angular_error", 0)
            criterion_met = turbine_data.get("criterion_met", False)

            row_error = idx * 2 + 1
            row_corr = idx * 2 + 2

            # --- SUBPLOT 1: Écart ---
            fig.add_trace(
                go.Scatter(
                    x=df_daily["date"],
                    y=df_daily["mean_angular_error"],
                    mode="lines+markers",
                    line=dict(color="royalblue", width=2),
                    marker=dict(size=4),
                    showlegend=False,
                    name="Écart",
                ),
                row=row_error,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=df_daily["date"],
                    y=[threshold] * len(df_daily),
                    mode="lines",
                    line=dict(color="red", width=1.5, dash="dash"),
                    showlegend=False,
                    name="Seuil",
                ),
                row=row_error,
                col=1,
            )

            # --- SUBPLOT 2: Corrélation ---
            fig.add_trace(
                go.Scatter(
                    x=df_daily["date"],
                    y=df_daily["correlation"],
                    mode="lines+markers",
                    line=dict(color="green", width=2),
                    marker=dict(size=4),
                    showlegend=False,
                    name="Corrélation",
                ),
                row=row_corr,
                col=1,
            )

            # Annotations (Positionnement corrigé pour être plus propre)
            status_text = (
                f"<b>[OK]</b> {overall_mean:.2f}° < {threshold}°"
                if criterion_met
                else f"<b>[!]</b> {overall_mean:.2f}° > {threshold}°"
            )
            status_color = "green" if criterion_met else "red"

            fig.add_annotation(
                text=status_text,
                xref="x domain",
                yref=f"y{row_error}",
                x=0.98,
                y=0.9,
                showarrow=False,
                font=dict(size=10, color=status_color),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor=status_color,
                borderwidth=1,
                borderpad=3,
                row=row_error,
                col=1,
            )

            # Configuration des axes Y
            fig.update_yaxes(
                title_text="Écart (°)", row=row_error, col=1, gridcolor="#eee"
            )
            fig.update_yaxes(title_text="Corr.", row=row_corr, col=1, gridcolor="#eee")

        # Check if we have any valid data
        if not valid_turbines:
            logger.error("No turbines with valid calibration data found")
            return self._create_empty_figure()

        # Correction 2: Appliquer le format de date optimal
        tick_config = self._calculate_optimal_tickformat(pd.Series(all_timestamps))

        # Correction 3: Boucle pour nettoyer les axes X
        for r in range(1, n_rows + 1):
            is_last_row = r == n_rows
            fig.update_xaxes(
                showticklabels=is_last_row,  # Seule la dernière ligne affiche les dates
                type="date",
                gridcolor="#eee",
                showgrid=True,
                **tick_config,
                row=r,
                col=1,
            )

        fig.update_layout(
            title={
                "text": "<b>Analyse de Calibration - Direction du Vent</b>",
                "x": 0.5,
            },
            height=300 * n_turbines + 100,
            margin=dict(t=80, b=50, l=60, r=40),
            hovermode="x unified",
            plot_bgcolor="white",
        )

        return fig
