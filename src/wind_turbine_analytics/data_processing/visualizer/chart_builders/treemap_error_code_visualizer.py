import plotly.graph_objects as go
import plotly.express as px
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)


class TreemapErrorCodeVisualizer(BaseVisualizer):
    def __init__(self, output_dir=None):
        super().__init__(chart_name="treemap_error_code", use_plotly=True, output_dir=output_dir)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        if not result.detailed_results:
            return self._create_empty_figure()

        ids, labels, parents, values, hovertext, colors = [], [], [], [], [], []

        # Palette contrastée
        palette = px.colors.qualitative.Bold
        system_color_map = {}
        color_index = 0

        # Racine
        ids.append("Wind Farm")
        labels.append("<b>WIND FARM</b>")
        parents.append("")
        values.append(0)
        colors.append("#f8f9fa")

        for turbine_id, turbine_data in result.detailed_results.items():
            if "error" in turbine_data:
                continue

            summary = turbine_data.get("summary", {})
            total_turbine_errors = summary.get("total_error_events", 0)

            # Niveau Turbine
            ids.append(turbine_id)
            labels.append(f"<b>Turbine {turbine_id}</b>")
            parents.append("Wind Farm")
            values.append(total_turbine_errors)
            colors.append("white")

            codes = turbine_data.get("code_frequency", [])
            systems_in_turbine = {}
            for c in codes:
                sys_name = c.get("system", "unknown").capitalize()
                systems_in_turbine[sys_name] = (
                    systems_in_turbine.get(sys_name, 0) + c["count"]
                )

            # Niveau Système
            for sys_name, sys_count in systems_in_turbine.items():
                sys_id = f"{turbine_id}_{sys_name}"
                if sys_name not in system_color_map:
                    system_color_map[sys_name] = palette[color_index % len(palette)]
                    color_index += 1

                current_sys_color = system_color_map[sys_name]
                ids.append(sys_id)
                labels.append(
                    f"<b>{sys_name}</b>"
                )  # Texte simplifié pour gagner de la place
                parents.append(turbine_id)
                values.append(sys_count)
                colors.append(current_sys_color)

                # Niveau Code
                for c in codes:
                    if c.get("system", "unknown").capitalize() == sys_name:
                        code_id = f"{sys_id}_{c['code']}"
                        ids.append(code_id)
                        labels.append(
                            f"C-{c['code']}"
                        )  # "C-" au lieu de "Code " pour gagner de la place
                        parents.append(sys_id)
                        values.append(c["count"])
                        colors.append(current_sys_color)
                        hovertext.append(f"Code: {c['code']}<br>Count: {c['count']}")

        fig = go.Figure(
            go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="remainder",
                # Amélioration du texte
                texttemplate="<span style='color:white'><b>%{label}</b></span><br><span style='color:white'>%{value}</span>",
                textposition="middle center",
                # PATHBAR : La solution pour la lisibilité des blocs parents
                pathbar=dict(visible=True, thickness=30, edgeshape=">"),
                marker=dict(
                    colors=colors,
                    line=dict(width=1.5, color="white"),
                    pad=dict(t=20),  # Espace pour le titre interne
                ),
            )
        )

        fig.update_layout(
            title={
                "text": "<b>Error Distribution Analysis</b>",
                "x": 0.5,
                "font": {"size": 24},
            },
            # On augmente la taille pour donner plus de place au texte
            width=1400,
            height=1000,
            margin=dict(t=80, l=10, r=10, b=10),
            # Paramètre CRITIQUE : on autorise le texte plus petit mais on le garde blanc
            uniformtext=dict(minsize=11, mode="show"),
            paper_bgcolor="white",
        )

        return fig

    def _create_empty_figure(self) -> go.Figure:
        return go.Figure().add_annotation(text="No data", x=0.5, y=0.5, showarrow=False)
