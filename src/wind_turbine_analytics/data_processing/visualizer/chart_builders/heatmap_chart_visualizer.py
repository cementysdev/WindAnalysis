from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.logger_config import get_logger

logger = get_logger(__name__)


class HeatmapChartVisualizer(BaseVisualizer):
    """
    Visualiseur de heatmap pour la disponibilité des données utilisant Plotly.
    Compatible avec .write_image()
    """

    def __init__(self, output_dir=None):
        # ✅ Changement crucial : use_plotly=True
        super().__init__(chart_name="heatmap_chart", use_plotly=True, output_dir=output_dir)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        # Gestion des données manquantes
        if not result or not result.detailed_results:
            return self._create_empty_plotly_figure()

        all_dfs = []

        # 1. Collecte et préparation des données
        for turbine_id, turbine_data in result.detailed_results.items():
            df = turbine_data.get("chart_data")
            if df is None or df.empty:
                continue

            df = df.copy()

            # Détection du temps
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            elif isinstance(df.index, pd.DatetimeIndex):
                df["timestamp"] = df.index
            else:
                # Fallback temporel si aucune date n'existe
                df["timestamp"] = pd.date_range(
                    start="2024-01-01", periods=len(df), freq="10min"
                )

            all_dfs.append(
                pd.DataFrame(
                    {
                        "timestamp": df["timestamp"],
                        "turbine_id": turbine_id,
                        "available": 1,
                    }
                )
            )

        if not all_dfs:
            return self._create_empty_plotly_figure()

        # 2. Construction de la matrice (Binnage horaire)
        full_df = pd.concat(all_dfs)
        matrix = (
            full_df.set_index("timestamp")
            .groupby("turbine_id")
            .resample("H")["available"]
            .max()
            .unstack(level=0)
            .fillna(0)
            .T
        )

        if matrix.empty:
            return self._create_empty_plotly_figure()

        # 3. Création de la Heatmap Plotly
        # On définit une échelle de couleurs discrète (Rouge pour 0, Vert pour 1)
        colorscale = [
            [0.0, "#f44336"],
            [0.5, "#f44336"],  # 0 à 0.5 = Rouge
            [0.5, "#4caf50"],
            [1.0, "#4caf50"],  # 0.5 à 1 = Vert
        ]

        fig = go.Figure(
            data=go.Heatmap(
                z=matrix.values,
                x=matrix.columns,
                y=matrix.index,
                colorscale=colorscale,
                showscale=False,
                xgap=1,  # Espace entre les cellules pour voir la grille
                ygap=1,
                hovertemplate="Turbine: %{y}<br>Heure: %{x}<br>Status: %{z}<extra></extra>",
            )
        )

        # 4. Mise en page (Layout)
        fig.update_layout(
            title={
                "text": "Data Availability Matrix (Hourly)",
                "y": 0.9,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=18),
            },
            xaxis_title="Time",
            yaxis_title="Turbine ID",
            template="plotly_white",
            height=200
            + (len(matrix) * 40),  # Hauteur dynamique selon le nombre de turbines
            margin=dict(l=50, r=50, t=80, b=50),
        )

        return fig

    def _create_empty_plotly_figure(self) -> go.Figure:
        """Crée une figure Plotly vide valide."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for heatmap",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="red"),
        )
        # On définit une taille minimale pour que write_image ne plante pas
        fig.update_layout(width=800, height=400)
        return fig
