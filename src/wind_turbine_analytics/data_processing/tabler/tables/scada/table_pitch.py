from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.logger_config import get_logger

logger = get_logger(__name__)


class PitchTabler(BaseTabler):
    """
    Tabler pour l'analyse de l'angle de pitch des 3 pales.

    Génère un tableau avec une ligne par turbine contenant :
    - Pitch moyen par pale (blade 1, 2, 3)
    - Écart-type par pale
    - Désynchronisation maximale entre pales

    Structure de sortie:
    | WTG | Blade 1 Mean (°) | Blade 2 Mean (°) | Blade 3 Mean (°) | Mean All (°) | Max Desync (°) |
    """

    def __init__(self):
        super().__init__(table_name="pitch_table")

    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes du tableau pour l'analyse pitch des 3 pales.

        Returns:
            Liste des headers avec 6 colonnes
        """
        return [
            "WTG",
            "Blade 1 Mean (°)",
            "Blade 2 Mean (°)",
            "Blade 3 Mean (°)",
            "Mean All (°)",
            "Max Desync (°)",
        ]

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Ajoute une ligne au tableau pour une turbine avec ses statistiques pitch des 3 pales.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - blade1: Dict avec mean_pitch, std_pitch, etc.
                - blade2: Dict avec mean_pitch, std_pitch, etc.
                - blade3: Dict avec mean_pitch, std_pitch, etc.
                - mean_pitch_all: Pitch moyen global (moyenne des 3 pales)
                - max_desync: Désynchronisation maximale entre pales
        """
        # Vérifier si c'est une erreur
        if "error" in turbine_result:
            error_msg = turbine_result["error"]
            logger.warning(f"Turbine {turbine_id}: Pitch analysis error - {error_msg}")
            row_data = {
                "wtg": turbine_id,
                "blade1_mean": "N/A",
                "blade2_mean": "N/A",
                "blade3_mean": "N/A",
                "mean_all": "N/A",
                "max_desync": f"ERROR: {error_msg}",
            }
        else:
            # Extraire les statistiques par pale
            blade1_stats = turbine_result.get("blade1", {})
            blade2_stats = turbine_result.get("blade2", {})
            blade3_stats = turbine_result.get("blade3", {})

            blade1_mean = blade1_stats.get("mean_pitch", 0.0)
            blade2_mean = blade2_stats.get("mean_pitch", 0.0)
            blade3_mean = blade3_stats.get("mean_pitch", 0.0)

            mean_pitch_all = turbine_result.get("mean_pitch_all", 0.0)
            max_desync = turbine_result.get("max_desync", 0.0)

            # Construire la ligne du tableau
            row_data = {
                "wtg": turbine_id,
                "blade1_mean": self._format_number(blade1_mean, decimals=2, unit="°"),
                "blade2_mean": self._format_number(blade2_mean, decimals=2, unit="°"),
                "blade3_mean": self._format_number(blade3_mean, decimals=2, unit="°"),
                "mean_all": self._format_number(mean_pitch_all, decimals=2, unit="°"),
                "max_desync": self._format_number(max_desync, decimals=2, unit="°"),
            }

        self._table_data.append(row_data)
