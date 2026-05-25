from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from src.logger_config import get_logger

logger = get_logger(__name__)


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class WindRoseChartVisualizer(BaseVisualizer):
    def __init__(self, output_dir=None):
        super().__init__(chart_name="wind_rose_chart", use_plotly=True, output_dir=output_dir)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            fig = go.Figure()
            fig.update_layout(
                title="Rose des Vents - Fréquence par Direction",
                template="plotly_white",
            )
            fig.add_annotation(
                text="Aucune donnée disponible",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
            )
            return fig

        turbine_ids = list(result.detailed_results.keys())
        n_turbines = len(turbine_ids)
        n_cols = min(n_turbines, 2)  # Maximum 2 colonnes
        n_rows = (n_turbines + n_cols - 1) // n_cols

        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            specs=[[{"type": "polar"}] * n_cols for _ in range(n_rows)],
            subplot_titles=[f"WTG {tid}" for tid in turbine_ids],
        )

        # --- Configuration Standard Météo ---
        wind_bins = [0, 3, 5, 10, 15, 20, 25, 100]
        wind_labels = ["0-3", "3-5", "5-10", "10-15", "15-20", "20-25", ">25"]
        colors = [
            "#d1e5f0",
            "#92c5de",
            "#4393c3",
            "#2166ac",
            "#053061",
            "#67001f",
            "#a50026",
        ]

        # Directions : On commence par le Nord (0°) et on suit le sens horaire
        dir_labels = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        directions_deg = np.arange(0, 360, 22.5)

        for idx, turbine_id in enumerate(turbine_ids):
            row, col = (idx // n_cols) + 1, (idx % n_cols) + 1
            chart_data = result.detailed_results[turbine_id].get("chart_data")

            if chart_data is None or chart_data.empty:
                continue

            df = chart_data.copy()
            df["wind_direction"] = pd.to_numeric(df["wind_direction"], errors="coerce")
            df["wind_speed"] = pd.to_numeric(df["wind_speed"], errors="coerce")
            df = df.dropna(subset=["wind_direction", "wind_speed"])
            if df.empty:
                continue

            # --- Correction Binning Direction (Gestion du Nord 360/0) ---
            # On décale de 11.25 pour que le "N" soit centré sur 0
            df["dir_idx"] = ((df["wind_direction"] + 11.25) % 360 // 22.5).astype(int)
            df["dir_bin"] = df["dir_idx"].apply(lambda x: dir_labels[x])

            df["wind_bin"] = pd.cut(
                df["wind_speed"],
                bins=wind_bins,
                labels=wind_labels,
                include_lowest=True,
            )

            # Table de fréquence (comptage)
            freq_table = (
                df.groupby(["dir_bin", "wind_bin"], observed=False)
                .size()
                .unstack(fill_value=0)
            )

            # --- Choix de normalisation ---
            # Option A: Normalisation Globale (Rose classique : la longueur = fréquence totale)
            total_records = len(df)
            freq_table_pct = (freq_table / total_records) * 100

            # Option B: Ton choix (Normalisation par direction : chaque barre fait 100%)
            # freq_table_pct = freq_table.div(freq_table.sum(axis=1), axis=0).fillna(0) * 100

            cumulative = np.zeros(len(dir_labels))

            for wind_label, color in zip(wind_labels, colors):
                # On réaligne les données pour qu'elles suivent l'ordre de dir_labels
                values = (
                    freq_table_pct[wind_label].reindex(dir_labels, fill_value=0).values
                )

                fig.add_trace(
                    go.Barpolar(
                        r=values,
                        theta=directions_deg,  # 0, 22.5, ...
                        name=f"{wind_label} m/s",
                        marker_color=color,
                        base=cumulative,
                        customdata=np.full(len(values), wind_label),
                        hovertemplate="Direction: %{theta}°<br>Vitesse: %{customdata} m/s<br>Fréquence: %{r:.1f}%",
                        showlegend=(idx == 0),
                    ),
                    row=row,
                    col=col,
                )
                cumulative += values

        # --- Layout Global ---
        fig.update_layout(
            title="Rose des Vents - Fréquence par Direction",
            template="plotly_white",
            legend=dict(title="Vitesse du vent", x=1.1),
            margin=dict(t=80, b=20, l=20, r=20),
        )

        # --- Configuration des axes polaires ---
        fig.update_polars(
            angularaxis=dict(
                direction="clockwise",  # Sens horaire (Météo)
                period=360,
                rotation=90,  # Le 0° (Nord) est en haut
                tickmode="array",
                tickvals=directions_deg,
                ticktext=dir_labels,
            ),
            radialaxis=dict(ticksuffix="%", angle=45, gridcolor="rgba(0,0,0,0.1)"),
        )

        return fig
