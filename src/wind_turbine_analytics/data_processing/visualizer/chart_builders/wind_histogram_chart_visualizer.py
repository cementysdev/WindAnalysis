from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from src.logger_config import get_logger

logger = get_logger(__name__)


class WindHistogramChartVisualizer(BaseVisualizer):
    """
    Visualiseur d'histogramme de vitesse de vent avec bins de 0.5 m/s.
    Converti vers Plotly pour affichage interactif dans l'interface web.
    """

    def __init__(self, output_dir=None):
        super().__init__(chart_name="wind_histogram_chart", use_plotly=True, output_dir=output_dir)

    def _create_empty_figure(self) -> go.Figure:
        """Créer une figure vide informative."""
        fig = go.Figure()
        fig.update_layout(
            title={
                "text": "<b>Distribution de la vitesse du vent</b>",
                "x": 0.5,
            },
            template="plotly_white",
            height=400,
        )
        fig.add_annotation(
            text="Aucune donnée disponible pour l'histogramme de vitesse du vent",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        return fig

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            logger.warning("Aucune donnée détaillée pour générer l'histogramme")
            return self._create_empty_figure()

        turbine_ids = sorted(result.detailed_results.keys())
        n_turbines = len(turbine_ids)

        # Calculer le layout de la grille
        n_cols = min(n_turbines, 3)
        n_rows = (n_turbines + n_cols - 1) // n_cols

        # Créer les subplot titles
        subplot_titles = [f"<b>WTG {tid}</b>" for tid in turbine_ids]

        # Créer la figure avec subplots
        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.12,
            horizontal_spacing=0.1,
            shared_xaxes=True,
        )

        # 1. Déterminer la vitesse max globale pour uniformiser les bins
        all_speeds = []
        for tid in turbine_ids:
            df = result.detailed_results[tid].get("chart_data")
            if df is not None and not df.empty and "wind_speed" in df.columns:
                all_speeds.extend(df["wind_speed"].dropna().tolist())

        if not all_speeds:
            logger.warning("Aucune donnée de vitesse de vent disponible")
            return self._create_empty_figure()

        max_wind = max(all_speeds)
        # Bins de 0.5 m/s
        bin_size = 0.5

        # 2. Tracer pour chaque turbine
        for idx, turbine_id in enumerate(turbine_ids):
            row = idx // n_cols + 1
            col = idx % n_cols + 1

            chart_data = result.detailed_results[turbine_id].get("chart_data")

            if chart_data is None or chart_data.empty or "wind_speed" not in chart_data.columns:
                # Ajouter une annotation "No data" pour cette turbine
                fig.add_annotation(
                    text="No data",
                    x=0.5,
                    y=0.5,
                    xref=f"x{idx+1} domain",
                    yref=f"y{idx+1} domain",
                    showarrow=False,
                    font=dict(size=12, color="gray"),
                    row=row,
                    col=col,
                )
                continue

            wind_speeds = chart_data["wind_speed"].dropna()

            if len(wind_speeds) == 0:
                continue

            # Créer l'histogramme avec Plotly
            fig.add_trace(
                go.Histogram(
                    x=wind_speeds,
                    xbins=dict(start=0, end=max_wind + bin_size, size=bin_size),
                    marker=dict(
                        color="#4393c3",
                        line=dict(color="white", width=1),
                    ),
                    opacity=0.8,
                    showlegend=False,
                    hovertemplate="Vitesse: %{x:.1f} m/s<br>Count: %{y}<extra></extra>",
                ),
                row=row,
                col=col,
            )

            # Configuration des axes pour ce subplot
            fig.update_xaxes(
                title_text="Wind Speed [m/s]" if row == n_rows else None,
                showgrid=False,
                dtick=5,  # Un tick tous les 5 m/s
                row=row,
                col=col,
            )

            fig.update_yaxes(
                title_text="Count",
                showgrid=True,
                gridcolor="rgba(0,0,0,0.1)",
                row=row,
                col=col,
            )

        # Layout global
        height = 400 + (n_rows - 1) * 350
        fig.update_layout(
            title={
                "text": "<b>Wind Speed Distribution (0.5 m/s bins)</b>",
                "x": 0.5,
                "xanchor": "center",
            },
            height=height,
            template="plotly_white",
            showlegend=False,
            margin=dict(l=60, r=40, t=100, b=60),
        )

        return fig
