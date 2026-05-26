"""
Spécifications standardisées pour les graphiques.
Permet de séparer la logique métier (préparation données) du rendu (Plotly/Matplotlib).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class ChartType(str, Enum):
    """Types de graphiques supportés."""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    POLAR = "polar"
    HEATMAP = "heatmap"
    TIMELINE = "timeline"


@dataclass
class SeriesData:
    """
    Données d'une série à tracer.

    Attributes:
        name: Nom de la série (ex: "E01", "Température")
        x: Valeurs de l'axe X
        y: Valeurs de l'axe Y
        colors: Couleurs des points/barres (optionnel)
        mode: Mode de tracé ("lines", "markers", "lines+markers")
        marker_size: Taille des marqueurs
        line_width: Largeur de ligne
        fill: Type de remplissage (ex: "tozeroy")
        text: Texte à afficher sur les points
        hovertemplate: Template pour le hover
        meta: Métadonnées additionnelles spécifiques au type de graphique
    """
    name: str
    x: List[Any]
    y: List[Any]
    colors: Optional[List[str]] = None
    mode: str = "lines+markers"
    marker_size: int = 6
    line_width: int = 2
    fill: Optional[str] = None
    text: Optional[List[str]] = None
    hovertemplate: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutConfig:
    """
    Configuration du layout du graphique.

    Attributes:
        title: Titre du graphique
        xaxis_title: Titre de l'axe X
        yaxis_title: Titre de l'axe Y
        width: Largeur en pixels
        height: Hauteur en pixels
        showlegend: Afficher la légende
        barmode: Mode pour les barres ("group", "stack")
        hovermode: Mode du hover ("x", "y", "closest")
        template: Template de style ("plotly", "plotly_white", etc.)
        grid_rows: Nombre de lignes pour subplots
        grid_cols: Nombre de colonnes pour subplots
        subplot_titles: Titres des subplots
        meta: Configurations additionnelles spécifiques
    """
    title: str = ""
    xaxis_title: str = ""
    yaxis_title: str = ""
    width: int = 1200
    height: int = 800
    showlegend: bool = True
    barmode: Optional[str] = None
    hovermode: str = "closest"
    template: str = "plotly_white"
    grid_rows: int = 1
    grid_cols: int = 1
    subplot_titles: Optional[List[str]] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartSpec:
    """
    Spécification complète d'un graphique.
    Format intermédiaire entre données métier et rendu.

    Attributes:
        chart_type: Type de graphique (bar, line, scatter, etc.)
        series: Liste des séries de données à tracer
        layout: Configuration du layout
    """
    chart_type: ChartType
    series: List[SeriesData]
    layout: LayoutConfig = field(default_factory=LayoutConfig)

    def validate(self) -> None:
        """Valide la cohérence de la spécification."""
        if not self.series:
            raise ValueError("ChartSpec must contain at least one series")

        # Vérifier que toutes les séries ont la même longueur de x et y
        for i, series in enumerate(self.series):
            if len(series.x) != len(series.y):
                raise ValueError(
                    f"Series '{series.name}' has mismatched x ({len(series.x)}) "
                    f"and y ({len(series.y)}) lengths"
                )
