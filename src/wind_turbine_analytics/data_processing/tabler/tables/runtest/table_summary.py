from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.logger_config import get_logger

logger = get_logger(__name__)


class RunTestSummaryTabler(BaseTabler):
    """
    Tableau récapitulatif montrant tous les critères par turbine.

    Format: | WTG | Criterion 1 | Criterion 2 | Criterion 3 | Criterion 4 | Criterion 5 | Overall |

    Ce tableau agrège les résultats de tous les analyseurs pour donner
    une vue d'ensemble du succès/échec de chaque turbine.
    """

    def __init__(self):
        super().__init__(table_name="summary_table")
        self.all_results: Dict[str, Dict[str, Any]] = (
            {}
        )  # Stocke résultats de tous les analyseurs

    def _get_table_headers(self) -> List[str]:
        """Retourne les en-têtes du tableau."""
        return [
            "WTG",
            "Consecutive Hours (>=120h)",
            "Cut-In/Cut-Out (>=72h)",
            "Nominal Power (>=3h)",
            "Autonomous Operation (<=3)",
            "Availability (>=92%)",
            "Overall",
        ]

    def add_analysis_result(self, analysis_name: str, result: AnalysisResult) -> None:
        """
        Accumule les résultats de chaque analyseur.

        Cette méthode doit être appelée pour chaque analyseur avant de générer
        le tableau récapitulatif.

        Args:
            analysis_name: Nom de l'analyse (ex: "consecutive_hours", "availability")
            result: Résultat d'analyse contenant detailed_results par turbine
        """
        if not result.detailed_results:
            logger.warning(
                f"Pas de résultats détaillés pour {analysis_name}, ignoré dans le récapitulatif"
            )
            return

        for turbine_id, data in result.detailed_results.items():
            if turbine_id not in self.all_results:
                self.all_results[turbine_id] = {}
            self.all_results[turbine_id][analysis_name] = data

        logger.debug(
            f"Résultats de '{analysis_name}' ajoutés au récapitulatif "
            f"({len(result.detailed_results)} turbines)"
        )

    def generate(self, result: AnalysisResult = None) -> Dict[str, Any]:
        """
        Génère le tableau récapitulatif à partir des résultats accumulés.

        Note: Le paramètre result n'est pas utilisé car on utilise self.all_results.

        Returns:
            Dict avec table_name et données formatées
        """
        self._table_data = []

        if not self.all_results:
            logger.warning(
                "Aucun résultat accumulé pour le tableau récapitulatif. "
                "Appelez add_analysis_result() avant generate()."
            )
            return {
                self.table_name: [],
                f"{self.table_name}_raw": [],
                f"{self.table_name}_headers": self._get_table_headers(),  # Headers même si vide
            }

        logger.debug(
            f"Génération du tableau récapitulatif pour {len(self.all_results)} turbines"
        )

        # Générer une ligne par turbine
        for turbine_id, turbine_results in self.all_results.items():
            self._add_table_row(turbine_id, turbine_results)

        formatted_table = self._format_as_word_table()

        return {
            self.table_name: formatted_table,
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),  # Headers lisibles
        }

    def _add_table_row(
        self, turbine_id: str, turbine_result: Dict[str, Any]
    ) -> None:
        """
        Ajoute une ligne pour une turbine dans le tableau récapitulatif.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Dict contenant les résultats de tous les analyseurs
                          Format: {analysis_name: {data}}
        """
        # Extraire les statuts de chaque critère
        consecutive_hours = turbine_result.get("consecutive_hours", {}).get(
            "criterion", False
        )
        cut_in_cut_out = turbine_result.get("cut_in_cut_out", {}).get(
            "criterion_met", False
        )
        nominal_power = turbine_result.get("nominal_power", {}).get(
            "criterion_met", False
        )
        autonomous = turbine_result.get("autonomous_operation", {}).get(
            "criterion_met", False
        )
        availability = turbine_result.get("availability", {}).get(
            "criterion_met", False
        )

        # Overall = tous les critères sont True
        overall = all(
            [consecutive_hours, cut_in_cut_out, nominal_power, autonomous, availability]
        )

        self._table_data.append(
            {
                "wtg": turbine_id,
                "consecutive_hours": self._format_status_cell(consecutive_hours),
                "cut_in_cut_out": self._format_status_cell(cut_in_cut_out),
                "nominal_power": self._format_status_cell(nominal_power),
                "autonomous_operation": self._format_status_cell(autonomous),
                "availability": self._format_status_cell(availability),
                "overall": self._format_status_cell(overall),
            }
        )
