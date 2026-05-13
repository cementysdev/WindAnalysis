from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from typing import Dict, Any, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod
from src.logger_config import get_logger
import plotly.graph_objects as go

logger = get_logger(__name__)


class BaseVisualizer(ABC):
    """
    Classe de base pour la génération de visualisations.

    Support:
    - Plotly (PNG + JSON pour dashboard web futur)
    - Seaborn/Matplotlib (PNG seulement)
    - Grid layout pour multi-turbines
    """

    def __init__(self, chart_name: str, use_plotly: bool = True):
        """
        Args:
            chart_name: Nom du graphique (ex: "power_curve_chart")
            use_plotly: True pour Plotly, False pour Seaborn/Matplotlib
        """
        self.chart_name = chart_name
        self.use_plotly = use_plotly
        self.output_dir = Path("output/charts")

    def generate(self, result: AnalysisResult) -> Dict[str, str]:
        """
        Génère la visualisation et sauvegarde les fichiers.

        Args:
            result: Résultat d'analyse contenant les données

        Returns:
            Dict avec les chemins des fichiers générés:
            {"png_path": "output/charts/power_curve.png",
             "json_path": "output/charts/power_curve.json"}  # Si Plotly
        """
        # Créer le répertoire de sortie si nécessaire
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Génération du graphique '{self.chart_name}'...")

        # Appeler la méthode abstraite pour créer la figure
        fig = self._create_figure(result)

        # Chemins de sortie
        png_path = self.output_dir / f"{self.chart_name}.png"
        json_path = self.output_dir / f"{self.chart_name}.json"

        # Sauvegarder selon le type
        if self.use_plotly:
            # Plotly: sauvegarder PNG et JSON
            fig.write_image(str(png_path), width=1200, height=800)
            fig.write_json(str(json_path))
            logger.debug(f"✅ Graphique Plotly sauvegardé: {png_path} + {json_path}")

            # Stocker les chemins dans metadata
            self._store_in_metadata(result, str(png_path), str(json_path))

            return {"png_path": str(png_path), "json_path": str(json_path)}
        else:
            # Matplotlib/Seaborn: sauvegarder PNG uniquement
            fig.savefig(str(png_path), dpi=150, bbox_inches="tight")
            logger.debug(f"✅ Graphique Matplotlib sauvegardé: {png_path}")

            # Stocker les chemins dans metadata
            self._store_in_metadata(result, str(png_path), None)

            return {"png_path": str(png_path)}

    def _store_in_metadata(
        self, result: AnalysisResult, png_path: str, json_path: Optional[str]
    ) -> None:
        """
        Stocke les chemins des fichiers dans result.metadata.

        Args:
            result: Résultat d'analyse
            png_path: Chemin du fichier PNG
            json_path: Chemin du fichier JSON (optionnel)
        """
        if result.metadata is None:
            result.metadata = {}
        if "charts" not in result.metadata:
            result.metadata["charts"] = {}

        chart_info = {"png_path": png_path}
        if json_path:
            chart_info["json_path"] = json_path

        result.metadata["charts"][self.chart_name] = chart_info

    @abstractmethod
    def _create_figure(
        self, result: AnalysisResult
    ) -> Union[go.Figure, "matplotlib.figure.Figure"]:
        """
        Méthode abstraite pour créer la figure.

        À implémenter dans chaque sous-classe.

        Args:
            result: Résultat d'analyse contenant les données

        Returns:
            Figure Plotly (go.Figure) ou Matplotlib (plt.Figure)
        """
        raise NotImplementedError(
            f"Visualization for '{self.chart_name}' is not implemented."
        )
