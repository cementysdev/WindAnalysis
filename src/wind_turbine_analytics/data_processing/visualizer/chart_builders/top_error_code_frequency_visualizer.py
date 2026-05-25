from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.logger_config import get_logger

logger = get_logger(__name__)


class TopErrorCodeFrequencyVisualizer(BaseVisualizer):
    def __init__(self, output_dir=None):
        super().__init__(chart_name="top_error_code_frequency", use_plotly=True, output_dir=output_dir)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            logger.warning("Aucune donnée détaillée")
            return self._create_empty_figure()

        valid_turbines = sorted(
            [
                tid
                for tid, data in result.detailed_results.items()
                if "error" not in data
            ]
        )
        if not valid_turbines:
            return self._create_empty_figure()

        n_turbines = len(valid_turbines)
        subplot_titles = []
        for turbine_id in valid_turbines:
            subplot_titles.append(f"<b>{turbine_id} - Frequency</b>")
            subplot_titles.append(f"<b>{turbine_id} - Duration</b>")

        # --- AMÉLIORATION DE L'ESPACEMENT ---
        # vertical_spacing augmenté pour éviter les chevauchements
        fig = make_subplots(
            rows=n_turbines,
            cols=2,
            subplot_titles=subplot_titles,
            horizontal_spacing=0.15,
            vertical_spacing=0.08,
        )

        for row_idx, turbine_id in enumerate(valid_turbines, start=1):
            turbine_data = result.detailed_results[turbine_id]

            # --- SUBPLOT GAUCHE (Fréquence) ---
            code_frequency = turbine_data.get("code_frequency", [])
            if code_frequency:
                top_10_freq = list(reversed(code_frequency[:10]))
                codes = [f"{c['code']}" for c in top_10_freq]
                counts = [c["count"] for c in top_10_freq]
                descriptions = [
                    c.get("description", "Unknown")[:50] for c in top_10_freq
                ]

                fig.add_trace(
                    go.Bar(
                        y=codes,
                        x=counts,
                        orientation="h",
                        marker=dict(
                            color=counts,  # Valeur pour le dégradé
                            colorscale="YlOrRd",  # Jaune -> Orange -> Rouge
                            showscale=False,
                            line=dict(color="white", width=1),
                        ),
                        text=[f" {c}" for c in counts],
                        textposition="outside",
                        customdata=descriptions,
                        hovertemplate="Code: %{y}<br>Count: %{x}<br>%{customdata}<extra></extra>",
                        showlegend=False,
                    ),
                    row=row_idx,
                    col=1,
                )

            # --- SUBPLOT DROIT (Durée) ---
            impactful_codes = turbine_data.get("most_impactful_codes", [])
            if impactful_codes:
                top_10_impact = list(reversed(impactful_codes[:10]))
                codes_impact = [f"{c['code']}" for c in top_10_impact]
                durations = [c["total_duration_hours"] for c in top_10_impact]
                descriptions_impact = [
                    c.get("description", "Unknown")[:50] for c in top_10_impact
                ]

                fig.add_trace(
                    go.Bar(
                        y=codes_impact,
                        x=durations,
                        orientation="h",
                        marker=dict(
                            color=durations,  # Valeur pour le dégradé
                            colorscale="Reds",  # Dégradé de Rouges
                            showscale=False,
                            line=dict(color="white", width=1),
                        ),
                        text=[f" {d:.1f}h" for d in durations],
                        textposition="outside",
                        customdata=descriptions_impact,
                        hovertemplate="Code: %{y}<br>Duration: %{x:.2f}h<br>%{customdata}<extra></extra>",
                        showlegend=False,
                    ),
                    row=row_idx,
                    col=2,
                )

        # --- MISE EN PAGE ET TAILLE DYNAMIQUE ---
        # Augmentation de la hauteur par turbine (500 au lieu de 350)
        dynamic_height = 300 + (n_turbines * 500)

        fig.update_layout(
            title={
                "text": "Error Code Analysis - Top 10 per Turbine<br><sub>Bars colored by intensity (higher value = darker red)</sub>",
                "font": {"size": 20},
                "x": 0.5,
                "xanchor": "center",
            },
            height=dynamic_height,
            width=1400,
            template="plotly_white",
            margin=dict(t=150, b=100, l=100, r=100),  # Plus d'espace autour
        )

        # Update subplot title font size
        fig.update_annotations(font_size=14)

        for row_idx in range(1, n_turbines + 1):
            fig.update_xaxes(
                title_text="Occurrences" if row_idx == n_turbines else "",
                row=row_idx,
                col=1,
                gridcolor="whitesmoke",
            )
            fig.update_xaxes(
                title_text="Duration (h)" if row_idx == n_turbines else "",
                row=row_idx,
                col=2,
                gridcolor="whitesmoke",
            )
            fig.update_yaxes(tickfont=dict(size=11), row=row_idx, col=1)
            fig.update_yaxes(tickfont=dict(size=11), row=row_idx, col=2)

        return fig

    def _create_empty_figure(self) -> go.Figure:
        # (Gardé identique à votre version)
        fig = go.Figure()
        fig.add_annotation(
            text="No error data", x=0.5, y=0.5, showarrow=False, font_size=20
        )
        return fig
