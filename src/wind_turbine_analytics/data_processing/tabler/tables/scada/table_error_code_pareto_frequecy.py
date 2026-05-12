"""
Tabler pour le tableau Pareto des codes erreurs (par fréquence).

Génère un tableau pivot avec :
- Lignes : Turbines (WTG)
- Colonnes : Codes erreurs (triés par fréquence totale décroissante, logique Pareto)
- Valeurs : Fréquence d'apparition (nombre d'occurrences)
- Colonne finale : Total par turbine
"""
from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class ErrorCodeParetoFrequencyTabler(BaseTabler):
    """
    Tabler pour l'analyse Pareto des codes erreurs par fréquence (structure pivotée).

    Génère un tableau comparatif avec:
    - Lignes: Turbines (WTG)
    - Colonnes: Codes erreurs (triés par fréquence totale décroissante)
    - Valeurs: Fréquence d'apparition (nombre d'occurrences)
    - Colonne finale: Total des erreurs par turbine

    Exemple de structure:
    | WTG | Code 102 (Pitch) | Code 205 (Comm) | Code 310 (Conv) | Total |
    | E1  | 24               | 12              | 2               | 38    |
    | E2  | 18               | 5               | 0               | 23    |
    """

    def __init__(self):
        super().__init__(table_name="error_code_pareto_frequency")
        # Stocker les fréquences de codes de toutes les turbines
        self._turbine_code_frequencies: Dict[str, Dict[str, int]] = {}
        self._turbine_ids: List[str] = []
        self._all_codes_info: Dict[str, Dict[str, Any]] = {}  # Métadonnées codes

    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes du tableau avec colonnes dynamiques par code erreur.

        Returns:
            Liste des headers: ["WTG", "Code XXX", "Code YYY", ..., "Total"]
        """
        headers = ["WTG"]

        # Calculer la fréquence totale de chaque code (somme sur toutes les turbines)
        code_totals: Dict[str, int] = {}
        for turbine_freqs in self._turbine_code_frequencies.values():
            for code, count in turbine_freqs.items():
                code_totals[code] = code_totals.get(code, 0) + count

        # Trier les codes par fréquence décroissante (logique Pareto)
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
            system = code_info.get("system", "")

            # Tronquer la description si trop longue
            if len(description) > 30:
                description = description[:27] + "..."

            # Format: "Code XXX (System)" ou "Code XXX"
            if system:
                header = f"Code {code} ({system.capitalize()})"
            else:
                header = f"Code {code}"

            headers.append(header)

        # Ajouter colonne Total
        headers.append("Total")

        return headers

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Collecte les fréquences de codes d'une turbine.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - code_frequency: Liste de dicts avec {code, count, description, ...}
        """
        # Enregistrer l'ID de la turbine
        if turbine_id not in self._turbine_ids:
            self._turbine_ids.append(turbine_id)

        # Extraire les fréquences de codes
        code_frequency_list = turbine_result.get("code_frequency", [])

        # Stocker les fréquences pour cette turbine
        turbine_freqs = {}
        for code_data in code_frequency_list:
            # Le code peut être int ou str, normaliser en string
            code = code_data.get("code", "UNKNOWN")
            code_str = str(code)
            count = code_data.get("count", 0)

            turbine_freqs[code_str] = count

            # Stocker les métadonnées du code (description, criticité, système)
            # Utiliser la version string comme clé pour cohérence
            if code_str not in self._all_codes_info:
                self._all_codes_info[code_str] = {
                    "description": code_data.get("description", "Unknown"),
                    "criticality": code_data.get("criticality", "unknown"),
                    "system": code_data.get("system", ""),
                }

        self._turbine_code_frequencies[turbine_id] = turbine_freqs

    def generate(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        Génère le tableau pivoté avec les fréquences des codes erreurs.

        Args:
            result: Résultat d'analyse contenant les données

        Returns:
            Dict avec le tableau pivoté et les données brutes
        """
        # Réinitialiser les données de table
        self._table_data = []
        self._turbine_ids = []
        self._turbine_code_frequencies = {}
        self._all_codes_info = {}

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
        self._pivot_code_frequencies()

        # Log final
        logger.info(
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

    def _pivot_code_frequencies(self) -> None:
        """
        Pivote les fréquences de codes pour créer une ligne par turbine.

        Structure finale :
        - Colonne 1 : Turbine ID
        - Colonnes 2-N : Un code par colonne (triés par fréquence totale Pareto)
        - Colonne finale : Total des erreurs pour la turbine
        """
        # Calculer la fréquence totale de chaque code (somme sur toutes les turbines)
        code_totals: Dict[str, int] = {}
        for turbine_freqs in self._turbine_code_frequencies.values():
            for code, count in turbine_freqs.items():
                # Normaliser le code en string pour le tri
                code_str = str(code)
                code_totals[code_str] = code_totals.get(code_str, 0) + count

        # Trier les codes par fréquence décroissante (logique Pareto)
        sorted_codes = sorted(
            code_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Limiter aux 10 codes les plus fréquents pour lisibilité du rapport Word
        TOP_N_CODES = 10
        total_codes_count = len(code_totals)

        # Log des codes exclus si applicable
        if total_codes_count > TOP_N_CODES:
            excluded_codes = [code for code, _ in sorted_codes[TOP_N_CODES:]]
            excluded_total = sum(code_totals[code] for code in excluded_codes)
            logger.info(
                f"Limiting to top {TOP_N_CODES} codes. "
                f"{total_codes_count - TOP_N_CODES} codes excluded ({excluded_total} occurrences total)"
            )

        sorted_codes = sorted_codes[:TOP_N_CODES]

        # Créer une ligne pour chaque turbine (ordre alphabétique)
        for turbine_id in sorted(self._turbine_ids):
            turbine_freqs = self._turbine_code_frequencies.get(turbine_id, {})

            # Construire la ligne
            row_data = {"wtg": turbine_id}

            # Ajouter la fréquence de chaque code (ordre Pareto)
            total_errors = 0
            for code, _ in sorted_codes:
                # Générer la clé de colonne (normaliser pour docxtpl)
                # Convertir en string et normaliser (minuscules, remplacer tirets)
                code_str = str(code).lower().replace('-', '_')
                col_key = code_str  # Supprimer préfixe "code_" pour simplification

                # Chercher le code dans les fréquences (peut être int ou str)
                count = 0
                for orig_code, orig_count in turbine_freqs.items():
                    if str(orig_code) == str(code):
                        count = orig_count
                        break

                row_data[col_key] = str(count)  # Garder en string pour template Word
                total_errors += count

            # Ajouter le total des erreurs pour cette turbine
            row_data["total"] = str(total_errors)

            self._table_data.append(row_data)

        # Log statistiques Pareto pour les codes affichés
        if sorted_codes:
            displayed_total = sum(count for _, count in sorted_codes)
            total_all = sum(code_totals.values())
            pareto_percent = (displayed_total / total_all * 100) if total_all > 0 else 0

            logger.info(
                f"Pareto analysis: Top {len(sorted_codes)} codes (displayed) represent {pareto_percent:.1f}% "
                f"of total errors ({displayed_total}/{total_all})"
            )
