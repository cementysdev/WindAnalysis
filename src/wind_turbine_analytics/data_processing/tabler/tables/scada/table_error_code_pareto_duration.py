"""
Tabler pour le tableau Pareto des codes erreurs (par durée).

Génère un tableau pivot avec :
- Lignes : Turbines (WTG)
- Colonnes : Codes erreurs (triés par durée totale décroissante, logique Pareto)
- Valeurs : Durée totale d'indisponibilité (heures)
- Colonne finale : Total par turbine
"""
from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class ErrorCodeParetoDurationTabler(BaseTabler):
    """
    Tabler pour l'analyse Pareto des codes erreurs par durée (structure pivotée).

    Génère un tableau comparatif avec:
    - Lignes: Turbines (WTG)
    - Colonnes: Codes erreurs (triés par durée totale décroissante)
    - Valeurs: Durée totale d'indisponibilité (heures)
    - Colonne finale: Total des heures d'indisponibilité par turbine

    Exemple de structure:
    | WTG | Code 102 (Pitch) | Code 205 (Comm) | Code 310 (Conv) | Total |
    | E1  | 15.67            | 8.23            | 2.45            | 26.35 |
    | E2  | 12.34            | 3.56            | 0.00            | 15.90 |
    """

    def __init__(self):
        super().__init__(table_name="error_code_pareto_duration")
        # Stocker les durées de codes de toutes les turbines
        self._turbine_code_durations: Dict[str, Dict[str, float]] = {}
        self._turbine_ids: List[str] = []
        self._all_codes_info: Dict[str, Dict[str, Any]] = {}  # Métadonnées codes
        self._turbine_test_durations: Dict[str, float] = {}  # Durée de test par turbine

    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes du tableau avec colonnes dynamiques par code erreur.

        Returns:
            Liste des headers: ["WTG", "Code XXX", "Code YYY", ..., "Total"]
        """
        headers = ["WTG"]

        # Calculer la durée totale de chaque code (somme sur toutes les turbines)
        code_totals: Dict[str, float] = {}
        for turbine_durations in self._turbine_code_durations.values():
            for code, duration in turbine_durations.items():
                code_totals[code] = code_totals.get(code, 0.0) + duration

        # Trier les codes par durée décroissante (logique Pareto)
        sorted_codes = sorted(
            code_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Ajouter une colonne par code (ordre Pareto)
        for code, _ in sorted_codes:
            # Récupérer la description du code (si disponible)
            code_info = self._all_codes_info.get(code, {})
            description = code_info.get("description", "Unknown")
            criticality = code_info.get("criticality", "")

            # Tronquer la description si trop longue
            if len(description) > 30:
                description = description[:27] + "..."

            # Format: "Code XXX (Criticality)" ou "Code XXX"
            if criticality and criticality != "unknown":
                header = f"Code {code} ({criticality.capitalize()})"
            else:
                header = f"Code {code}"

            headers.append(header)

        # Ajouter colonne Total
        headers.append("Total (h)")
        headers.append("STATUS")

        return headers

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Collecte les durées de codes d'une turbine.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - most_impactful_codes: Liste de dicts avec {code, total_duration_hours, description, ...}
                - test_duration_hours: Durée totale de test
        """
        # Enregistrer l'ID de la turbine
        if turbine_id not in self._turbine_ids:
            self._turbine_ids.append(turbine_id)

        # Stocker la durée de test pour calcul du status
        test_duration = turbine_result.get("test_duration_hours", 0.0)
        self._turbine_test_durations[turbine_id] = test_duration

        # Extraire les codes impactants (durées)
        impactful_codes_list = turbine_result.get("most_impactful_codes", [])

        # Stocker les durées pour cette turbine
        turbine_durations = {}
        for code_data in impactful_codes_list:
            # Le code peut être int ou str, normaliser en string
            code = code_data.get("code", "UNKNOWN")
            code_str = str(code)
            duration_hours = code_data.get("total_duration_hours", 0.0)

            turbine_durations[code_str] = duration_hours

            # Stocker les métadonnées du code (description, criticité, occurrences)
            # Utiliser la version string comme clé pour cohérence
            if code_str not in self._all_codes_info:
                self._all_codes_info[code_str] = {
                    "description": code_data.get("description", "Unknown"),
                    "criticality": code_data.get("criticality", "unknown"),
                    "occurrences": code_data.get("occurrences", 0),
                }

        self._turbine_code_durations[turbine_id] = turbine_durations

    def generate(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        Génère le tableau pivoté avec les durées des codes erreurs.

        Args:
            result: Résultat d'analyse contenant les données

        Returns:
            Dict avec le tableau pivoté et les données brutes
        """
        # Réinitialiser les données de table
        self._table_data = []
        self._turbine_ids = []
        self._turbine_code_durations = {}
        self._all_codes_info = {}

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
        self._pivot_code_durations()

        # Log final
        logger.debug(
            f"Tableau '{self.table_name}' généré avec "
            f"{len(self._table_data)} lignes (turbines) et "
            f"{len(self._all_codes_info)} codes distincts"
        )

        # Retourner le résultat avec les données pivotées ET les headers
        return {
            self.table_name: self._format_as_word_table(),
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),  # Headers lisibles
        }

    def _pivot_code_durations(self) -> None:
        """
        Pivote les durées de codes pour créer une ligne par turbine.

        Structure finale :
        - Colonne 1 : Turbine ID
        - Colonnes 2-N : Un code par colonne (triés par durée totale Pareto)
        - Colonne finale : Total des heures d'indisponibilité pour la turbine
        """
        # Calculer la durée totale de chaque code (somme sur toutes les turbines)
        code_totals: Dict[str, float] = {}
        for turbine_durations in self._turbine_code_durations.values():
            for code, duration in turbine_durations.items():
                # Normaliser le code en string pour le tri
                code_str = str(code)
                code_totals[code_str] = code_totals.get(code_str, 0.0) + duration

        # Trier les codes par durée décroissante (logique Pareto)
        sorted_codes = sorted(
            code_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Limiter aux 10 codes les plus impactants pour lisibilité du rapport Word
        TOP_N_CODES = 10
        total_codes_count = len(code_totals)

        # Log des codes exclus si applicable
        if total_codes_count > TOP_N_CODES:
            excluded_codes = [code for code, _ in sorted_codes[TOP_N_CODES:]]
            excluded_duration = sum(code_totals[code] for code in excluded_codes)
            logger.debug(
                f"Limiting to top {TOP_N_CODES} codes by duration. "
                f"{total_codes_count - TOP_N_CODES} codes excluded ({excluded_duration:.2f}h total)"
            )

        sorted_codes = sorted_codes[:TOP_N_CODES]

        # Créer une ligne pour chaque turbine (ordre alphabétique)
        for turbine_id in sorted(self._turbine_ids):
            turbine_durations = self._turbine_code_durations.get(turbine_id, {})

            # Construire la ligne
            row_data = {"wtg": turbine_id}

            # Ajouter la durée de chaque code (ordre Pareto)
            total_duration = 0.0
            for code, _ in sorted_codes:
                # Générer la clé de colonne (normaliser pour docxtpl)
                # Convertir en string et normaliser (minuscules, remplacer tirets)
                code_str = str(code).lower().replace('-', '_')
                col_key = code_str  # Pas de préfixe "code_"

                # Chercher le code dans les durées (peut être int ou str)
                duration = 0.0
                for orig_code, orig_duration in turbine_durations.items():
                    if str(orig_code) == str(code):
                        duration = orig_duration
                        break

                # Formater avec 2 décimales
                row_data[col_key] = f"{duration:.2f}"
                total_duration += duration

            # Ajouter le total des heures d'indisponibilité pour cette turbine
            row_data["total"] = f"{total_duration:.2f}"

            # Calculate uptime and status
            from src.wind_turbine_analytics.data_processing.status_levels import StatusLevel

            test_duration = self._turbine_test_durations.get(turbine_id, 0.0)
            uptime_pct = (
                ((test_duration - total_duration) / test_duration * 100)
                if test_duration > 0
                else 0.0
            )

            status = StatusLevel.from_percentage(uptime_pct)
            row_data["status"] = str(status)

            self._table_data.append(row_data)

        # Log statistiques Pareto pour les codes affichés
        if sorted_codes:
            displayed_duration = sum(duration for _, duration in sorted_codes)
            total_all_duration = sum(code_totals.values())
            pareto_percent = (displayed_duration / total_all_duration * 100) if total_all_duration > 0 else 0

            logger.debug(
                f"Pareto analysis: Top {len(sorted_codes)} codes (displayed) represent {pareto_percent:.1f}% "
                f"of total downtime ({displayed_duration:.2f}h/{total_all_duration:.2f}h)"
            )
