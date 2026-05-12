import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class PerformanceLevelVisualizer(BaseVisualizer):
    """
    Visualiseur des niveaux de performance basé sur la classification des régimes.

    Génère un graphique avec 3 subplots par turbine (vertical):
    - Subplot 1: Rotation (RPM normalisé) vs Wind Speed normalisé
    - Subplot 2: Power (puissance normalisée) vs Wind Speed normalisé
    - Subplot 3: Pitch (angle normalisé) vs Wind Speed normalisé

    Chaque point est coloré selon sa zone opérationnelle:
    - Zone 1 (bleu): Arrêt (vent faible)
    - Zone 2 (orange): Démarrage
    - Zone 3 (vert): Rotation max
    - Zone 4 (rouge): Puissance max
    - Zone 5 (violet): Arrêt (vent élevé)
    - Zone 6 (noir): Outliers

    Les seuils de vitesse de vent (X_threshold) sont affichés avec des lignes verticales.
    """

    def __init__(self):
        super().__init__(chart_name="performance_level_chart", use_plotly=True)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            return self._create_empty_figure()

        turbine_ids = sorted(result.detailed_results.keys())
        n_turbines = len(turbine_ids)

        # Grille de subplots: maximum 2 colonnes par ligne
        n_cols = min(2, n_turbines)
        n_rows = (n_turbines + n_cols - 1) // n_cols

        # Chaque turbine a 3 subplots verticaux (Rotation, Power, Pitch)
        # Donc on a n_rows x n_cols turbines, chaque cellule contient 3 subplots
        # On va créer une figure avec (n_rows * 3) rows et n_cols columns

        total_rows = n_rows * 3  # 3 subplots par turbine (verticalement)

        fig = make_subplots(
            rows=total_rows,
            cols=n_cols,
            subplot_titles=None,  # On ajoutera des annotations manuellement
            vertical_spacing=0.04,
            horizontal_spacing=0.12,
        )

        # Palette de couleurs pour les zones (correspond aux clusters)
        zone_colors = {
            1: "#1f77b4",  # Bleu - Stop (low wind)
            2: "#ff7f0e",  # Orange - Start
            3: "#2ca02c",  # Vert - Max rotation
            4: "#d62728",  # Rouge - Max power
            5: "#9467bd",  # Violet - Stop (high wind)
            6: "#000000",  # Noir - Outliers
        }

        zone_names = {
            1: "Zone 1: Stop (low wind)",
            2: "Zone 2: Start",
            3: "Zone 3: Max rotation",
            4: "Zone 4: Max power",
            5: "Zone 5: Stop (high wind)",
            6: "Zone 6: Outliers",
        }

        for t_idx, turbine_id in enumerate(turbine_ids):
            turbine_data = result.detailed_results[turbine_id]
            chart_data = turbine_data.get("chart_data")
            X_threshold = turbine_data.get("X_threshold", [])

            if chart_data is None or chart_data.empty:
                continue

            # Position de la turbine dans la grille
            col = (t_idx % n_cols) + 1
            base_row = (t_idx // n_cols) * 3 + 1  # Première ligne des 3 subplots

            # Échantillonner si trop de données
            if len(chart_data) > 2000:
                chart_data = chart_data.sample(n=2000, random_state=42)

            # Pour chaque zone, créer une trace
            unique_zones = sorted(chart_data["cluster"].unique())

            for zone in unique_zones:
                zone_data = chart_data[chart_data["cluster"] == zone]
                color = zone_colors.get(zone, "#808080")
                name = zone_names.get(zone, f"Zone {zone}")

                # Subplot 1: Rotation
                fig.add_trace(
                    go.Scatter(
                        x=zone_data["wind_speed"],
                        y=zone_data["rpm_norm"],
                        mode="markers",
                        name=name,
                        marker=dict(size=3, color=color, opacity=0.6),
                        showlegend=(t_idx == 0),  # Légende seulement pour la première turbine
                        legendgroup=f"zone_{zone}",
                        hovertemplate=(
                            f"{name}<br>"
                            "Wind speed: %{x:.1f} m/s<br>"
                            "RPM (norm): %{y:.3f}<extra></extra>"
                        ),
                    ),
                    row=base_row,
                    col=col,
                )

                # Subplot 2: Power
                fig.add_trace(
                    go.Scatter(
                        x=zone_data["wind_speed"],
                        y=zone_data["power_norm"],
                        mode="markers",
                        marker=dict(size=3, color=color, opacity=0.6),
                        showlegend=False,
                        legendgroup=f"zone_{zone}",
                        hovertemplate=(
                            f"{name}<br>"
                            "Wind speed: %{x:.1f} m/s<br>"
                            "Power (norm): %{y:.3f}<extra></extra>"
                        ),
                    ),
                    row=base_row + 1,
                    col=col,
                )

                # Subplot 3: Pitch
                fig.add_trace(
                    go.Scatter(
                        x=zone_data["wind_speed"],
                        y=zone_data["pitch_norm"],
                        mode="markers",
                        marker=dict(size=3, color=color, opacity=0.6),
                        showlegend=False,
                        legendgroup=f"zone_{zone}",
                        hovertemplate=(
                            f"{name}<br>"
                            "Wind speed: %{x:.1f} m/s<br>"
                            "Pitch (norm): %{y:.3f}<extra></extra>"
                        ),
                    ),
                    row=base_row + 2,
                    col=col,
                )

            # Ajouter les seuils verticaux (X_threshold)
            if X_threshold:
                for x_thresh in X_threshold:
                    for subplot_offset in range(3):
                        fig.add_vline(
                            x=x_thresh,
                            line_dash="dot",
                            line_color="black",
                            opacity=0.7,
                            row=base_row + subplot_offset,
                            col=col,
                        )

            # Annotations pour les titres de turbine (au-dessus du premier subplot)
            fig.add_annotation(
                text=f"<b>Turbine {turbine_id}</b>",
                xref="paper",
                yref="paper",
                x=(col - 0.5) / n_cols,
                y=1 - ((base_row - 1) / total_rows),
                showarrow=False,
                font=dict(size=14),
                xanchor="center",
                yanchor="bottom",
            )

        # Configuration globale
        height = 400 + (total_rows * 120)  # Hauteur dynamique
        fig.update_layout(
            title={
                "text": "<b>Performance Level Analysis - Operating Zones Classification</b>",
                "x": 0.5,
            },
            height=height,
            template="plotly_white",
            legend_title_text="Operating Zones",
            margin=dict(t=100, b=50, l=80, r=50),
        )

        # Mise à jour des axes
        # Axes X (seulement pour la dernière ligne de chaque colonne)
        for col_idx in range(1, n_cols + 1):
            for turbine_row in range(n_rows):
                last_row_for_turbine = (turbine_row * 3) + 3
                fig.update_xaxes(
                    title_text="Wind Speed (m/s)",
                    gridcolor="#f0f0f0",
                    row=last_row_for_turbine,
                    col=col_idx,
                )

        # Axes Y
        for row_idx in range(1, total_rows + 1):
            subplot_in_group = (row_idx - 1) % 3
            if subplot_in_group == 0:
                ylabel = "Rotation (-)"
            elif subplot_in_group == 1:
                ylabel = "Power (-)"
            else:
                ylabel = "Pitch (-)"

            for col_idx in range(1, n_cols + 1):
                fig.update_yaxes(
                    title_text=ylabel,
                    gridcolor="#f0f0f0",
                    range=[0, 1.05],
                    row=row_idx,
                    col=col_idx,
                )

        return fig

    def _create_empty_figure(self) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", showarrow=False)
        return fig
