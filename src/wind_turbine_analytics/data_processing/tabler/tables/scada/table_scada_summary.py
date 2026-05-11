"""
Tabler récapitulatif SCADA - agrège tous les résultats d'analyse.

Similaire à RunTestSummaryTabler mais pour les analyses SCADA.
"""

from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult


class ScadaSummaryTabler(BaseTabler):
    """
    Tableau récapitulatif pour toutes les analyses SCADA.

    Agrège les résultats de:
    - EBA Cut-In/Cut-Out
    - EBA Manufacturer
    - Code Error Analysis
    - Data Availability
    - Wind Direction Calibration
    - Tip Speed Ratio
    """

    def __init__(self):
        super().__init__(table_name="scada_summary_table")
        # Stocker les résultats de toutes les analyses
        self._analysis_results: Dict[str, AnalysisResult] = {}

    def add_analysis_result(
        self, analysis_name: str, result: AnalysisResult
    ) -> None:
        """
        Ajoute un résultat d'analyse à l'agrégateur.

        Args:
            analysis_name: Nom de l'analyse (ex: "eba_cut_in_cut_out")
            result: Résultat de l'analyse
        """
        self._analysis_results[analysis_name] = result

    def generate(self) -> Dict[str, Any]:
        """
        Génère le tableau récapitulatif en agrégeant tous les résultats.

        Returns:
            Dict avec le tableau summary et les données brutes
        """
        # Réinitialiser les données
        self._table_data = []

        # Collecter tous les IDs de turbines
        all_turbine_ids = set()
        for result in self._analysis_results.values():
            if result.detailed_results:
                all_turbine_ids.update(result.detailed_results.keys())

        # Créer une ligne par turbine
        for turbine_id in sorted(all_turbine_ids):
            self._add_summary_row(turbine_id)

        # Retourner le format standard avec headers
        return {
            self.table_name: self._format_as_word_table(),
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),  # Headers lisibles
        }

    def _get_table_headers(self) -> List[str]:
        """Retourne les en-têtes du tableau."""
        return [
            "WTG",
            "EBA C/I-C/O",
            "EBA Mfr",
            "Availability",
            "Calibration",
            "TSR",
            "Overall"
        ]

    def _add_summary_row(self, turbine_id: str) -> None:
        """
        Ajoute une ligne récapitulative pour une turbine.

        Args:
            turbine_id: ID de la turbine
        """
        # EBA Cut-In/Cut-Out
        eba_cutin_status = self._get_criterion_status(
            "eba_cut_in_cut_out", turbine_id, performance_threshold=90.0
        )

        # EBA Manufacturer
        eba_mfr_status = self._get_criterion_status(
            "eba_manufacturer", turbine_id, performance_threshold=85.0
        )

        # Data Availability
        availability_status = self._get_criterion_status(
            "data_availability", turbine_id, key="availability_overall", threshold=80.0
        )

        # Wind Direction Calibration
        calibration_status = self._get_criterion_status(
            "wind_calibration", turbine_id, key="criterion_met"
        )

        # Tip Speed Ratio
        tsr_status = self._get_criterion_status(
            "tip_speed_ratio", turbine_id, key="criterion_met"
        )

        # Overall: Tous OK = OK, sinon FAIL
        all_statuses = [
            eba_cutin_status,
            eba_mfr_status,
            availability_status,
            calibration_status,
            tsr_status,
        ]
        overall_met = all(all_statuses)

        self._table_data.append({
            "wtg": turbine_id,
            "eba_cutin": self._format_status_cell(eba_cutin_status),
            "eba_mfr": self._format_status_cell(eba_mfr_status),
            "availability": self._format_status_cell(availability_status),
            "calibration": self._format_status_cell(calibration_status),
            "tsr": self._format_status_cell(tsr_status),
            "overall": self._format_status_cell(overall_met),
        })

    def _get_criterion_status(
        self,
        analysis_name: str,
        turbine_id: str,
        key: str = "performance_percent",
        threshold: float = None,
        performance_threshold: float = None,
    ) -> bool:
        """
        Extrait le statut d'un critère pour une turbine.

        Args:
            analysis_name: Nom de l'analyse
            turbine_id: ID de la turbine
            key: Clé du résultat à vérifier
            threshold: Seuil pour critères d'availability
            performance_threshold: Seuil pour critères de performance

        Returns:
            True si critère satisfait, False sinon
        """
        if analysis_name not in self._analysis_results:
            return False

        result = self._analysis_results[analysis_name]
        if not result.detailed_results or turbine_id not in result.detailed_results:
            return False

        turbine_result = result.detailed_results[turbine_id]

        # Si la clé est "criterion_met", utiliser directement
        if key == "criterion_met":
            return turbine_result.get("criterion_met", False)

        # Sinon, comparer avec un seuil
        value = turbine_result.get(key, 0.0)

        if performance_threshold is not None:
            return value >= performance_threshold
        elif threshold is not None:
            return value >= threshold
        else:
            # Par défaut, vérifier si > 0
            return value > 0.0

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Non utilisé pour le summary (utilise _add_summary_row à la place).
        """
        pass
