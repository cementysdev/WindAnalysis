from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from typing import Dict, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod
from src.logger_config import get_logger
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.figure

# Imports du nouveau système ChartSpec
from src.wind_turbine_analytics.data_processing.visualizer.chart_spec import ChartSpec
from src.wind_turbine_analytics.data_processing.visualizer.renderers import (
    PlotlyRenderer,
    MatplotlibRenderer,
)

logger = get_logger(__name__)


class BaseVisualizer(ABC):
    """
    Classe de base pour la génération de visualisations.

    Support:
    - Plotly (PNG + JSON pour dashboard web futur)
    - Seaborn/Matplotlib (PNG seulement)
    - Grid layout pour multi-turbines
    """

    def __init__(
        self,
        chart_name: str,
        use_plotly: bool = True,
        output_dir: Optional[Path] = None
    ):
        """
        Args:
            chart_name: Nom du graphique (ex: "power_curve_chart")
            use_plotly: True pour Plotly, False pour Seaborn/Matplotlib
            output_dir: Dossier de sortie personnalisé (défaut: output/charts)
                       Pour sessions: tmp/sessions/{session_id}/charts/
        """
        self.chart_name = chart_name
        self.use_plotly = use_plotly

        # Utiliser output_dir fourni, sinon fallback output/charts
        if output_dir is not None:
            self.output_dir = Path(output_dir)
        else:
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
            # JSON toujours sauvegardé (pas besoin de Chrome)
            fig.write_json(str(json_path))
            logger.debug(f"✅ Graphique Plotly JSON sauvegardé: {json_path}")

            # PNG: essayer Kaleido d'abord, sinon convertir en Matplotlib
            png_saved = False
            kaleido_error = None

            logger.info(f"🔄 [{self.chart_name}] Tentative export PNG (Kaleido → Matplotlib fallback)...")

            try:
                # Méthode 1: Kaleido (si disponible en local)
                logger.debug(f"  → Essai Kaleido pour {self.chart_name}...")
                fig.write_image(str(png_path), width=1200, height=800)

                # Vérifier que le fichier a réellement été créé
                if png_path.exists() and png_path.stat().st_size > 0:
                    png_saved = True
                    logger.info(f"✅ [{self.chart_name}] PNG exporté via Kaleido: {png_path}")
                else:
                    # Kaleido n'a pas levé d'exception mais n'a pas créé le fichier
                    kaleido_error = Exception("Kaleido: PNG file not created or empty")
                    logger.warning(f"  ⚠️ Kaleido failed silently for {self.chart_name}, trying Matplotlib...")
                    raise kaleido_error
            except Exception as e_kaleido:
                # Méthode 2: Conversion Plotly → Matplotlib (Databricks)
                logger.info(f"  → Fallback Matplotlib pour {self.chart_name} (Kaleido error: {type(e_kaleido).__name__})")

                try:
                    from src.wind_turbine_analytics.data_processing.visualizer.plotly_to_matplotlib_converter import (
                        PlotlyToMatplotlibConverter,
                    )

                    logger.info(
                        f"  → Conversion Plotly→Matplotlib en cours pour {self.chart_name}..."
                    )
                    mpl_fig = PlotlyToMatplotlibConverter.convert(fig)
                    logger.debug(f"  → Sauvegarde PNG Matplotlib: {png_path}")
                    mpl_fig.savefig(str(png_path), dpi=150, bbox_inches="tight")
                    plt.close(mpl_fig)
                    png_saved = True
                    logger.info(
                        f"✅ [{self.chart_name}] PNG exporté via Matplotlib: {png_path}"
                    )
                except Exception as e_matplotlib:
                    import traceback
                    logger.error(
                        f"❌ [{self.chart_name}] Échec export PNG complet"
                    )
                    logger.error(
                        f"  → Kaleido error: {type(e_kaleido).__name__}: {e_kaleido}"
                    )
                    logger.error(
                        f"  → Matplotlib error: {type(e_matplotlib).__name__}: {e_matplotlib}"
                    )
                    logger.error(
                        f"  → Traceback:\n{traceback.format_exc()}"
                    )
                    png_saved = False

            # Stocker les chemins dans metadata
            self._store_in_metadata(
                result,
                str(png_path) if png_saved else None,
                str(json_path)
            )

            return {
                "png_path": str(png_path) if png_saved else None,
                "json_path": str(json_path)
            }
        else:
            # Matplotlib/Seaborn: sauvegarder PNG uniquement
            fig.savefig(str(png_path), dpi=150, bbox_inches="tight")
            logger.debug(f"✅ Graphique Matplotlib sauvegardé: {png_path}")

            # Stocker les chemins dans metadata
            self._store_in_metadata(result, str(png_path), None)

            return {"png_path": str(png_path)}

    def _store_in_metadata(
        self, result: AnalysisResult, png_path: Optional[str], json_path: Optional[str]
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

        chart_info = {}
        if png_path:
            chart_info["png_path"] = png_path
        if json_path:
            chart_info["json_path"] = json_path

        result.metadata["charts"][self.chart_name] = chart_info

    def generate_with_chartspec(
        self, result: AnalysisResult, render_png: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Génère la visualisation en utilisant le système ChartSpec.
        Produit JSON Plotly (pour web) + PNG Matplotlib (pour Word).

        Args:
            result: Résultat d'analyse contenant les données
            render_png: Si True, génère PNG Matplotlib (pour rapports Word)

        Returns:
            Dict avec chemins des fichiers:
            {"json_path": "...", "png_path": "..." or None}
        """
        # Créer le répertoire de sortie
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"Génération du graphique '{self.chart_name}' "
            f"(ChartSpec mode)..."
        )

        # ÉTAPE 1: Préparer les données (logique métier)
        chart_spec = self._prepare_chart_data(result)

        # ÉTAPE 2a: Générer JSON Plotly (toujours, pour web)
        plotly_fig = PlotlyRenderer.render(chart_spec)
        json_path = self.output_dir / f"{self.chart_name}.json"
        plotly_fig.write_json(str(json_path))
        logger.debug(f"✅ Plotly JSON: {json_path}")

        # ÉTAPE 2b: Générer PNG Matplotlib (conditionnel, pour Word)
        png_path_str = None
        if render_png:
            try:
                mpl_fig = MatplotlibRenderer.render(chart_spec)
                png_path = self.output_dir / f"{self.chart_name}.png"
                mpl_fig.savefig(
                    str(png_path), dpi=150, bbox_inches="tight"
                )
                plt.close(mpl_fig)
                png_path_str = str(png_path)
                logger.debug(f"✅ Matplotlib PNG: {png_path}")
            except Exception as e:
                logger.warning(
                    f"Échec génération PNG Matplotlib: {e}"
                )

        # Stocker dans metadata
        self._store_in_metadata(result, png_path_str, str(json_path))

        return {"json_path": str(json_path), "png_path": png_path_str}

    def _prepare_chart_data(self, result: AnalysisResult) -> ChartSpec:
        """
        Prépare les données du graphique (logique métier).
        À implémenter dans les sous-classes utilisant ChartSpec.

        Args:
            result: Résultat d'analyse

        Returns:
            ChartSpec standardisée

        Raises:
            NotImplementedError: Si la sous-classe n'implémente pas
        """
        raise NotImplementedError(
            f"ChartSpec preparation for '{self.chart_name}' "
            f"not implemented. Implement _prepare_chart_data()."
        )

    @abstractmethod
    def _create_figure(
        self, result: AnalysisResult
    ) -> Union[go.Figure, matplotlib.figure.Figure]:
        """
        Méthode abstraite pour créer la figure (ancien système).

        À implémenter dans chaque sous-classe.

        Args:
            result: Résultat d'analyse contenant les données

        Returns:
            Figure Plotly (go.Figure) ou Matplotlib (plt.Figure)
        """
        raise NotImplementedError(
            f"Visualization for '{self.chart_name}' is not implemented."
        )
