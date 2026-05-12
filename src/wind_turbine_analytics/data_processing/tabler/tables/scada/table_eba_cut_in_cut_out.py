from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class EbaCutInCutOutTabler(BaseTabler):
    """
    Tabler pour l'analyse EBA Cut-In/Cut-Out (structure pivotée).

    Génère un tableau comparatif avec:
    - Lignes: Périodes mensuelles
    - Colonnes: Une colonne par turbine + colonne WindFarm (moyenne)
    - Valeurs: Indices de performance (%)

    Structure de sortie:
    | Period | WTG E1 (%) | WTG E2 (%) | ... | WindFarm (%) |
    """

    def __init__(self):
        super().__init__(table_name="eba_cut_in_cut_out_table")
        # Stocker les données mensuelles de toutes les turbines
        self._monthly_data: Dict[str, Dict[str, float]] = {}
        self._turbine_ids: List[str] = []

    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes du tableau avec colonnes dynamiques par turbine.

        Returns:
            Liste des headers: ["Period", "WTG E1", "WTG E2", ..., "WindFarm"]
        """
        headers = ["Period"]

        # Ajouter une colonne par turbine (ordre alphabétique)
        for turbine_id in sorted(self._turbine_ids):
            headers.append(f"WTG {turbine_id}")

        # Ajouter colonne WindFarm (moyenne)
        headers.append("WindFarm")

        return headers

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Collecte les données mensuelles d'une turbine.

        Cette méthode est appelée pour chaque turbine. Les données sont stockées
        en interne et seront pivotées dans generate().

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - monthly_performance: DataFrame ou liste de dicts avec performance mensuelle
        """
        # Enregistrer l'ID de la turbine

        if turbine_id not in self._turbine_ids:
            self._turbine_ids.append(turbine_id)

        # Extraire les performances mensuelles
        monthly_performance = turbine_result.get("monthly_performance", [])

        # Si c'est un DataFrame pandas, le convertir en liste de dicts
        if hasattr(monthly_performance, "to_dict"):
            monthly_performance = monthly_performance.to_dict("records")

        # Stocker les données mensuelles pour cette turbine

        for month_data in monthly_performance:
            # 1. Récupérer l'objet Period et le convertir en string (ex: "2024-04")
            period_obj = month_data.get("month")
            period_str = str(period_obj) if period_obj else "N/A"

            # 2. Correction de la clé : on utilise "performance" comme dans vos données
            performance = month_data.get("performance", 0.0)

            # 3. Initialiser le dictionnaire imbriqué pour la période si inexistant
            if period_str not in self._monthly_data:
                self._monthly_data[period_str] = {}

            # 4. Stocker la performance pour cette turbine
            self._monthly_data[period_str][turbine_id] = performance

    def generate(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        Génère le tableau pivoté avec les performances mensuelles.

        Surcharge de la méthode de base pour implémenter la logique de pivot
        et calcul de la moyenne WindFarm.

        Args:
            result: Résultat d'analyse contenant les données

        Returns:
            Dict avec le tableau pivoté et les données brutes
        """
        # Réinitialiser les données de table
        self._table_data = []
        self._turbine_ids = []
        self._monthly_data = {}

        # Collecte manuelle (ne PAS appeler super().generate())
        # car le pivot est incompatible avec le template method de BaseTabler
        if result.detailed_results:
            logger.info(
                f"Génération du tableau '{self.table_name}' "
                f"pour {len(result.detailed_results)} turbines"
            )
            for turbine_id, turbine_result in result.detailed_results.items():
                self._add_table_row(turbine_id, turbine_result)

        # Maintenant, pivoter les données collectées
        self._pivot_monthly_data()

        # Log final
        logger.info(
            f"Tableau '{self.table_name}' généré avec {len(self._table_data)} lignes"
        )

        # Retourner le résultat avec les données pivotées ET les headers
        return {
            self.table_name: self._format_as_word_table(),
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),  # Headers lisibles
        }

    def _pivot_monthly_data(self) -> None:
        """
        Pivote les données mensuelles pour créer une ligne par période.

        Transforme:
        _monthly_data = {
            "2024-01": {"E1": 98.2, "E2": 94.5},
            "2024-02": {"E1": 99.1, "E2": 98.8}
        }

        En table_data:
        [
            {"period": "2024-01", "wtg_e1": "98.2 %", "wtg_e2": "94.5 %", "windfarm": "96.4 %"},
            {"period": "2024-02", "wtg_e1": "99.1 %", "wtg_e2": "98.8 %", "windfarm": "99.0 %"}
        ]
        """
        # Trier les périodes chronologiquement
        sorted_periods = sorted(self._monthly_data.keys())

        # Créer une ligne pour chaque période
        for period in sorted_periods:
            turbine_performances = self._monthly_data[period]

            # Construire la ligne avec les performances de chaque turbine
            row_data = {"period": period}

            # Ajouter les performances des turbines (ordre alphabétique)
            for turbine_id in sorted(self._turbine_ids):
                col_key = f"wtg_{turbine_id.lower()}"

                if turbine_id in turbine_performances:
                    performance = turbine_performances[turbine_id]
                    row_data[col_key] = self._format_number(
                        performance, decimals=2, unit="%"
                    )
                else:
                    # Turbine sans données pour cette période
                    row_data[col_key] = "N/A"

            # Calculer la moyenne WindFarm (ignorer les NaN)
            valid_performances = [
                perf
                for perf in turbine_performances.values()
                if perf is not None and perf > 0
            ]

            if valid_performances:
                windfarm_avg = sum(valid_performances) / len(valid_performances)
                row_data["windfarm"] = self._format_number(
                    windfarm_avg, decimals=2, unit="%"
                )
            else:
                row_data["windfarm"] = "N/A"

            self._table_data.append(row_data)
