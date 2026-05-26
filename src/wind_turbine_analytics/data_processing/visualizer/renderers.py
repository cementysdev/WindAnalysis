"""
Renderers universels pour convertir ChartSpec vers Plotly ou Matplotlib.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.figure
import numpy as np
from typing import Union
from src.wind_turbine_analytics.data_processing.visualizer.chart_spec import (
    ChartSpec,
    ChartType,
    SeriesData,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class PlotlyRenderer:
    """Convertit ChartSpec vers Plotly Figure."""

    @staticmethod
    def render(spec: ChartSpec) -> go.Figure:
        """
        Génère une figure Plotly depuis une ChartSpec.

        Args:
            spec: Spécification du graphique

        Returns:
            Figure Plotly
        """
        spec.validate()

        layout = spec.layout

        # Créer figure avec subplots si nécessaire
        if layout.grid_rows > 1 or layout.grid_cols > 1:
            fig = make_subplots(
                rows=layout.grid_rows,
                cols=layout.grid_cols,
                subplot_titles=layout.subplot_titles,
            )
        else:
            fig = go.Figure()

        # Ajouter les séries
        for series in spec.series:
            trace = PlotlyRenderer._create_trace(spec.chart_type, series)
            fig.add_trace(trace)

        # Configuration du layout
        fig.update_layout(
            title=layout.title,
            xaxis_title=layout.xaxis_title,
            yaxis_title=layout.yaxis_title,
            width=layout.width,
            height=layout.height,
            showlegend=layout.showlegend,
            hovermode=layout.hovermode,
            template=layout.template,
        )

        # Configurations spécifiques au type
        if layout.barmode:
            fig.update_layout(barmode=layout.barmode)

        return fig

    @staticmethod
    def _create_trace(chart_type: ChartType, series: SeriesData) -> go.Scatter:
        """Crée une trace Plotly selon le type de graphique."""

        if chart_type == ChartType.BAR:
            return go.Bar(
                x=series.x,
                y=series.y,
                name=series.name,
                marker_color=series.colors if series.colors else None,
                text=series.text,
                hovertemplate=series.hovertemplate,
            )

        elif chart_type == ChartType.LINE:
            return go.Scatter(
                x=series.x,
                y=series.y,
                name=series.name,
                mode="lines",
                line=dict(
                    width=series.line_width,
                    color=series.colors[0] if series.colors else None,
                ),
                fill=series.fill,
                hovertemplate=series.hovertemplate,
            )

        elif chart_type == ChartType.SCATTER:
            return go.Scatter(
                x=series.x,
                y=series.y,
                name=series.name,
                mode=series.mode,
                marker=dict(
                    size=series.marker_size,
                    color=series.colors if series.colors else None,
                ),
                line=dict(width=series.line_width) if "lines" in series.mode else None,
                text=series.text,
                hovertemplate=series.hovertemplate,
            )

        else:
            # Défaut: scatter
            return go.Scatter(
                x=series.x,
                y=series.y,
                name=series.name,
                mode=series.mode,
            )


class MatplotlibRenderer:
    """Convertit ChartSpec vers Matplotlib Figure."""

    @staticmethod
    def render(spec: ChartSpec) -> matplotlib.figure.Figure:
        """
        Génère une figure Matplotlib depuis une ChartSpec.

        Args:
            spec: Spécification du graphique

        Returns:
            Figure Matplotlib
        """
        spec.validate()

        layout = spec.layout

        # Créer figure et axes
        figsize = (layout.width / 100, layout.height / 100)  # Pixels → inches
        fig, ax = plt.subplots(figsize=figsize)

        # Ajouter les séries
        if spec.chart_type == ChartType.BAR:
            MatplotlibRenderer._render_bar(ax, spec.series, layout)
        elif spec.chart_type == ChartType.LINE:
            MatplotlibRenderer._render_line(ax, spec.series)
        elif spec.chart_type == ChartType.SCATTER:
            MatplotlibRenderer._render_scatter(ax, spec.series)
        else:
            logger.warning(f"Chart type {spec.chart_type} not fully implemented for Matplotlib")
            MatplotlibRenderer._render_scatter(ax, spec.series)

        # Configuration du layout
        if layout.title:
            ax.set_title(layout.title, fontsize=14, fontweight='bold')
        if layout.xaxis_title:
            ax.set_xlabel(layout.xaxis_title, fontsize=11)
        if layout.yaxis_title:
            ax.set_ylabel(layout.yaxis_title, fontsize=11)

        if layout.showlegend and len(spec.series) > 1:
            ax.legend(loc='best')

        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        return fig

    @staticmethod
    def _render_bar(ax, series_list: list[SeriesData], layout):
        """Rendu de barres groupées."""
        n_series = len(series_list)

        if layout.barmode == "group" and n_series > 1:
            # Barres groupées
            width = 0.8 / n_series
            x_base = np.arange(len(series_list[0].x))

            for i, series in enumerate(series_list):
                x_pos = x_base + i * width - (0.8 / 2) + (width / 2)
                ax.bar(
                    x_pos,
                    series.y,
                    width=width,
                    label=series.name,
                    color=series.colors if series.colors else None,
                )

            # Labels X
            ax.set_xticks(x_base)
            ax.set_xticklabels(series_list[0].x, rotation=45, ha='right')

        else:
            # Une seule série ou stack
            for series in series_list:
                ax.bar(
                    series.x,
                    series.y,
                    label=series.name,
                    color=series.colors if series.colors else None,
                )
            plt.xticks(rotation=45, ha='right')

    @staticmethod
    def _render_line(ax, series_list: list[SeriesData]):
        """Rendu de lignes."""
        for series in series_list:
            color = series.colors[0] if series.colors else None
            ax.plot(
                series.x,
                series.y,
                label=series.name,
                linewidth=series.line_width,
                color=color,
                marker='o' if 'markers' in series.mode else None,
                markersize=series.marker_size if 'markers' in series.mode else None,
            )

    @staticmethod
    def _render_scatter(ax, series_list: list[SeriesData]):
        """Rendu de scatter plot."""
        for series in series_list:
            ax.scatter(
                series.x,
                series.y,
                label=series.name,
                s=series.marker_size * 10,  # Matplotlib uses larger values
                c=series.colors if series.colors else None,
            )
