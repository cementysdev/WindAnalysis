from typing import Dict, Any, List
from pathlib import Path
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineFarm,
)


class CsvFilesTabler(BaseTabler):
    """
    Tableau listant les fichiers CSV utilisés pour le test.

    Format: | WTG | Operation Data | Log Data |

    Ce tabler est spécial car il ne traite pas un AnalysisResult mais
    directement les informations de TurbineFarm.

    Note: Les clés du dictionnaire correspondent aux headers en snake_case:
    - "WTG" -> clé "wtg"
    - "Operation Data" -> clé "operation_data"
    - "Log Data" -> clé "log_data"
    """

    def __init__(self):
        super().__init__(table_name="csv_files_table")

    def _get_table_headers(self) -> List[str]:
        """Retourne les en-têtes du tableau."""
        return ["WTG", "Operation Data", "Log Data"]

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Méthode non utilisée pour ce tabler.
        Voir generate_from_turbine_farm() à la place.
        """
        pass

    def generate_from_turbine_farm(self, turbine_farm: TurbineFarm) -> Dict[str, Any]:
        """
        Génère le tableau directement depuis TurbineFarm.

        Args:
            turbine_farm: Configuration des turbines

        Returns:
            Dict avec les données du tableau
        """
        self._table_data = []

        for turbine_id, turbine_config in turbine_farm.farm.items():
            # Récupérer les chemins
            path_operation = "N/A"
            path_log = "N/A"

            if (
                turbine_config.general_information
                and turbine_config.general_information.path_operation_data
            ):
                operation_path = Path(
                    turbine_config.general_information.path_operation_data
                )
                path_operation = operation_path.name

            if (
                turbine_config.general_information
                and turbine_config.general_information.path_log_data
            ):
                log_path = Path(turbine_config.general_information.path_log_data)
                path_log = log_path.name

            self._table_data.append(
                {
                    "wtg": turbine_id,
                    "operation_data": path_operation,
                    "log_data": path_log,
                }
            )

        return {
            self.table_name: self._table_data,
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),
        }
