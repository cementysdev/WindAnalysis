from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from src.logger_config import get_logger

logger = get_logger(__name__)


class PowerRoseChartVisualizer(BaseVisualizer):
    """
    Visualiseur de rose des puissances par direction du vent.

    Identique à WindRoseChartVisualizer mais affiche la fréquence selon
    direction du vent et TRANCHES DE PUISSANCE (au lieu de vitesse).

    Utile pour détecter:
    - Problèmes de calibration de nacelle (certains secteurs sous-performent)
    - Effets de sillage entre turbines
    - Obstacles environnementaux

    Complémentaire à WindDirectionCalibrationVisualizer.
    """

    def __init__(self):
        super().__init__(chart_name="power_rose_chart", use_plotly=True)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            fig = go.Figure()
            fig.update_layout(
                title="Rose des Puissances - Fréquence par Direction",
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

        # --- Configuration des Tranches de Puissance ---
        # Adapter selon la puissance nominale typique (ex: 3780 kW pour N131)
        power_bins = [0, 500, 1000, 1500, 2000, 2500, 3000, 10000]
        power_labels = [
            "0-500",
            "500-1000",
            "1000-1500",
            "1500-2000",
            "2000-2500",
            "2500-3000",
            ">3000",
        ]
        # Couleurs : du bleu clair (faible puissance) au bleu foncé (haute puissance)
        colors = [
            "#d1e5f0",  # Bleu très clair
            "#92c5de",
            "#4393c3",
            "#2166ac",
            "#053061",  # Bleu foncé
            "#67001f",  # Rouge foncé (puissance maximale)
            "#a50026",  # Rouge très foncé
        ]

        # Directions : Nord (0°) en haut, sens horaire
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
            df["wind_direction"] = pd.to_numeric(
                df["wind_direction"], errors="coerce"
            )
            df["activation_power"] = pd.to_numeric(
                df["activation_power"], errors="coerce"
            )
            df = df.dropna(subset=["wind_direction", "activation_power"])
            if df.empty:
                continue

            # --- Binning Direction (Gestion du Nord 360/0) ---
            # On décale de 11.25 pour que le "N" soit centré sur 0
            df["dir_idx"] = ((df["wind_direction"] + 11.25) % 360 // 22.5).astype(
                int
            )
            df["dir_bin"] = df["dir_idx"].apply(lambda x: dir_labels[x])

            # --- Binning Puissance ---
            df["power_bin"] = pd.cut(
                df["activation_power"],
                bins=power_bins,
                labels=power_labels,
                include_lowest=True,
            )

            # Table de fréquence (comptage)
            freq_table = (
                df.groupby(["dir_bin", "power_bin"], observed=False)
                .size()
                .unstack(fill_value=0)
            )

            # Normalisation Globale (longueur = fréquence totale en %)
            total_records = len(df)
            freq_table_pct = (freq_table / total_records) * 100

            cumulative = np.zeros(len(dir_labels))

            for power_label, color in zip(power_labels, colors):
                # Réaligner les données pour suivre l'ordre de dir_labels
                values = (
                    freq_table_pct[power_label]
                    .reindex(dir_labels, fill_value=0)
                    .values
                )

                fig.add_trace(
                    go.Barpolar(
                        r=values,
                        theta=directions_deg,  # 0, 22.5, 45, ...
                        name=f"{power_label} kW",
                        marker_color=color,
                        base=cumulative,
                        customdata=np.full(len(values), power_label),
                        hovertemplate=(
                            "Direction: %{theta}°<br>"
                            "Puissance: %{customdata} kW<br>"
                            "Fréquence: %{r:.1f}%"
                        ),
                        showlegend=(idx == 0),
                    ),
                    row=row,
                    col=col,
                )
                cumulative += values

        # --- Layout Global ---
        fig.update_layout(
            title=(
                "<b>Rose des Puissances - Fréquence par Direction</b><br>"
                "<span style='font-size:12px; color:gray;'>"
                "Puissance active selon direction du vent - "
                "Détecte les problèmes de calibration nacelle"
                "</span>"
            ),
            template="plotly_white",
            legend=dict(title="Puissance active (kW)", x=1.1),
            margin=dict(t=100, b=20, l=20, r=20),
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
            radialaxis=dict(
                showticklabels=True,
                ticks="outside",
                ticksuffix="%",
            ),
        )

        logger.info(
            f"Rose des puissances créée pour {n_turbines} turbine(s) "
            f"avec {len(dir_labels)} secteurs directionnels"
        )

        return fig
