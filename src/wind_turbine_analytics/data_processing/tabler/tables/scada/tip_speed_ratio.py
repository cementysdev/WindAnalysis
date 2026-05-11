from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.logger_config import get_logger

logger = get_logger(__name__)


class TipSpeedRatioTabler(BaseTabler):
    """
    Tabler pour l'analyse du Tip Speed Ratio (TSR).

    Génère un tableau avec une ligne par turbine contenant :
    - TSR moyen et écart-type
    - Plage optimale de TSR
    - Pourcentage de mesures dans la plage optimale
    - Statut de validation du critère

    Structure de sortie:
    | WTG | Mean TSR | Std TSR | Optimal Range | In Range (%) | Status |
    """

    def __init__(self):
        super().__init__(table_name="tip_speed_ratio_table")

    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes du tableau pour l'analyse TSR.

        Returns:
            Liste des headers avec 6 colonnes
        """
        return [
            "WTG",
            "Mean TSR",
            "Std TSR",
            "Optimal Range",
            "In Range (%)",
        ]

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Ajoute une ligne au tableau pour une turbine avec ses statistiques TSR.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - mean_tsr: TSR moyen
                - std_tsr: Écart-type du TSR
                - optimal_range: Plage optimale [min, max]
                - percentage_in_range: % de mesures dans la plage optimale
                - criterion_met: True si le TSR moyen est dans la plage optimale
        """
        # Extraire les valeurs avec gestion des erreurs
        mean_tsr = turbine_result.get("mean_tsr", 0.0)
        std_tsr = turbine_result.get("std_tsr", 0.0)
        optimal_range = turbine_result.get("optimal_range", [7.0, 9.0])
        percentage_in_range = turbine_result.get("percentage_in_range", 0.0)
        criterion_met = turbine_result.get("criterion_met", False)

        # Vérifier si c'est une erreur
        if "error" in turbine_result:
            error_msg = turbine_result["error"]
            logger.warning(f"Turbine {turbine_id}: TSR analysis error - {error_msg}")
            row_data = {
                "wtg": turbine_id,
                "mean_tsr": "N/A",
                "std_tsr": "N/A",
                "optimal_range": "N/A",
                "in_range": "N/A",
                "status": f"ERROR: {error_msg}",
            }
        else:
            # Formater la plage optimale
            optimal_range_str = f"[{optimal_range[0]:.1f}, {optimal_range[1]:.1f}]"

            # Construire la ligne du tableau
            row_data = {
                "wtg": turbine_id,
                "mean_tsr": self._format_number(mean_tsr, decimals=2),
                "std_tsr": self._format_number(std_tsr, decimals=2),
                "optimal_range": optimal_range_str,
                "in_range": self._format_number(
                    percentage_in_range, decimals=1, unit="%"
                ),
            }

        self._table_data.append(row_data)
