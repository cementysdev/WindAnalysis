from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.logger_config import get_logger

logger = get_logger(__name__)


class WindDirectionCalibrationTabler(BaseTabler):
    """
    Tabler pour l'analyse de calibration de direction du vent.

    Génère un tableau avec une ligne par turbine contenant :
    - Écart angulaire moyen (nacelle vs vent)
    - Écart-type et écart maximum
    - Corrélation globale
    - Statut de validation du critère (écart < 5°)

    Structure de sortie:
    | WTG | Mean Error (°) | Std Error (°) | Max Error (°) | Correlation | Status |
    """

    def __init__(self):
        super().__init__(table_name="wind_direction_calibration_table")

    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes du tableau pour l'analyse de calibration.

        Returns:
            Liste des headers avec 6 colonnes
        """
        return [
            "WTG",
            "Mean Error (°)",
            "Std Error (°)",
            "Max Error (°)",
            "Correlation",
            "Status",
        ]

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Ajoute une ligne au tableau pour une turbine avec ses statistiques de calibration.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - overall_mean_angular_error: Écart moyen global
                - overall_std_angular_error: Écart-type global
                - overall_max_angular_error: Écart maximum global
                - overall_correlation: Corrélation entre wind_direction et nacelle_position
                - criterion_met: True si écart moyen < 5°
        """
        # Vérifier si c'est une erreur
        if "error" in turbine_result:
            error_msg = turbine_result["error"]
            logger.warning(
                f"Turbine {turbine_id}: Wind direction calibration error - {error_msg}"
            )
            row_data = {
                "wtg": turbine_id,
                "mean_error": "N/A",
                "std_error": "N/A",
                "max_error": "N/A",
                "correlation": "N/A",
                "status": f"ERROR: {error_msg}",
            }
        else:
            # Extraire les valeurs
            mean_error = turbine_result.get("overall_mean_angular_error", 0.0)
            std_error = turbine_result.get("overall_std_angular_error", 0.0)
            max_error = turbine_result.get("overall_max_angular_error", 0.0)
            correlation = turbine_result.get("overall_correlation", None)
            status_level = turbine_result.get("status_level", None)

            # Formater la corrélation (peut être None)
            if correlation is not None:
                correlation_str = f"{correlation:.3f}"
            else:
                correlation_str = "N/A"

            # Formater le status
            if status_level is not None:
                status_str = str(status_level)
            else:
                # Fallback to old criterion_met if status_level not available
                criterion_met = turbine_result.get("criterion_met", False)
                status_str = self._format_status_cell(criterion_met)

            # Construire la ligne du tableau
            row_data = {
                "wtg": turbine_id,
                "mean_error": self._format_number(mean_error, decimals=2, unit="°"),
                "std_error": self._format_number(std_error, decimals=2, unit="°"),
                "max_error": self._format_number(max_error, decimals=2, unit="°"),
                "correlation": correlation_str,
                "status": status_str,
            }

        self._table_data.append(row_data)
