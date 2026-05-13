from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class EbaLossTabler(BaseTabler):
    """
    Tabler pour l'analyse des pertes d'énergie mensuelles (structure pivotée).

    Génère un tableau comparatif avec:
    - Lignes: Périodes mensuelles
    - Colonnes: Une colonne par turbine + colonne WindFarm (moyenne)
    - Valeurs: Pertes d'énergie (%) = 100% - Performance%

    Structure de sortie:
    | Period | WTG E1 (%) | WTG E2 (%) | ... | WindFarm (%) |
    """

    def __init__(self):
        super().__init__(table_name="eba_loss_table")
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

        # Ajouter colonne WindFarm (moyenne des pertes)
        headers.append("WindFarm")

        return headers

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Collecte les données mensuelles d'une turbine.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - monthly_performance: DataFrame ou liste de dicts
        """
        # Enregistrer l'ID de la turbine
        if turbine_id not in self._turbine_ids:
            self._turbine_ids.append(turbine_id)

        # Extraire les performances mensuelles
        monthly_performance = turbine_result.get("monthly_performance", [])

        # Si c'est un DataFrame pandas, le convertir en liste de dicts
        if hasattr(monthly_performance, 'to_dict'):
            monthly_performance = monthly_performance.to_dict('records')

        # Stocker les pertes mensuelles pour cette turbine
        for month_data in monthly_performance:
            period_obj = month_data.get("month")
            period_str = str(period_obj) if period_obj else "N/A"

            performance = month_data.get("performance", 0.0)
            loss = 100.0 - performance  # Perte = 100% - Performance

            # Initialiser le dict pour cette période si nécessaire
            if period_str not in self._monthly_data:
                self._monthly_data[period_str] = {}

            # Stocker la perte de cette turbine pour cette période
            self._monthly_data[period_str][turbine_id] = loss

    def generate(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        Génère le tableau pivoté avec les pertes mensuelles.

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
            logger.debug(
                f"Génération du tableau '{self.table_name}' "
                f"pour {len(result.detailed_results)} turbines"
            )
            for turbine_id, turbine_result in result.detailed_results.items():
                self._add_table_row(turbine_id, turbine_result)

        # Maintenant, pivoter les données collectées
        self._pivot_monthly_data()

        # Log final
        logger.debug(
            f"Tableau '{self.table_name}' généré avec "
            f"{len(self._table_data)} lignes"
        )

        # Retourner le résultat avec les données pivotées ET les headers
        return {
            self.table_name: self._format_as_word_table(),
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),  # Headers lisibles
        }

    def _pivot_monthly_data(self) -> None:
        """
        Pivote les données mensuelles de pertes pour créer une ligne par période.
        """
        # Trier les périodes chronologiquement
        sorted_periods = sorted(self._monthly_data.keys())

        # Créer une ligne pour chaque période
        for period in sorted_periods:
            turbine_losses = self._monthly_data[period]

            # Construire la ligne avec les pertes de chaque turbine
            row_data = {"period": period}

            # Ajouter les pertes des turbines (ordre alphabétique)
            for turbine_id in sorted(self._turbine_ids):
                col_key = f"wtg_{turbine_id.lower()}"

                if turbine_id in turbine_losses:
                    loss = turbine_losses[turbine_id]
                    row_data[col_key] = self._format_number(loss, decimals=2, unit="%")
                else:
                    # Turbine sans données pour cette période
                    row_data[col_key] = "N/A"

            # Calculer la moyenne WindFarm des pertes (ignorer les NaN)
            valid_losses = [
                loss for loss in turbine_losses.values()
                if loss is not None and loss >= 0
            ]

            if valid_losses:
                windfarm_avg = sum(valid_losses) / len(valid_losses)
                row_data["windfarm"] = self._format_number(
                    windfarm_avg, decimals=2, unit="%"
                )
            else:
                row_data["windfarm"] = "N/A"

            self._table_data.append(row_data)
