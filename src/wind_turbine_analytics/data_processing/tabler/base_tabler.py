from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class BaseTabler(ABC):
    """
    Classe de base pour la génération de tableaux Word.

    Suit le pattern Template Method pour permettre des implémentations
    spécifiques tout en maintenant une interface cohérente.

    Cette classe fournit:
    - Une interface standard pour générer des tableaux
    - Des méthodes utilitaires pour le formatage (couleurs, nombres)
    - Un système de gestion des données tabulaires
    """

    def __init__(self, table_name: str):
        """
        Initialise un générateur de tableau.

        Args:
            table_name: Nom du tableau (utilisé comme clé dans le template Word)
        """
        self.table_name = table_name
        self._table_data: List[Dict[str, Any]] = []

    def generate(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        Point d'entrée principal pour générer les données de tableau.

        Args:
            result: Résultat d'analyse contenant les données

        Returns:
            Dict avec:
                - table_name: Données de tableau formatées
                - table_name_raw: Données brutes (liste de dicts) pour debug
                - table_name_headers: En-têtes lisibles pour le template Word
        """
        self._table_data = []
        if result.detailed_results:
            logger.info(
                f"Génération du tableau '{self.table_name}' "
                f"pour {len(result.detailed_results)} turbines"
            )
            for turbine_id, turbine_result in result.detailed_results.items():
                self._add_table_row(turbine_id, turbine_result)

        # Générer le tableau Word formaté

        formatted_table = self._format_as_word_table()

        logger.info(
            f"Tableau '{self.table_name}' généré avec {len(formatted_table)} lignes"
        )

        return {
            self.table_name: formatted_table,
            f"{self.table_name}_raw": self._table_data,  # Pour debug
            f"{self.table_name}_headers": self._get_table_headers(),  # Headers lisibles
        }

    @abstractmethod
    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Méthode abstraite pour ajouter une ligne au tableau.

        Chaque implémentation définit comment transformer les données
        de l'analyseur en une ligne de tableau.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats pour cette turbine
        """
        raise NotImplementedError("Subclasses must implement _add_table_row()")

    @abstractmethod
    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes de colonnes du tableau.

        Returns:
            Liste des noms de colonnes
        """
        raise NotImplementedError("Subclasses must implement _get_table_headers()")

    def _format_as_word_table(self) -> List[Dict[str, Any]]:
        """
        Formate les données pour tableaux Word natifs avec docxtpl.

        Returns:
            Liste de dictionnaires (une ligne = un dict)
        """

        if not self._table_data:
            logger.warning(f"Tableau '{self.table_name}' vide (aucune donnée)")
            return []

        # Retourner directement les données pour docxtpl
        # docxtpl utilisera la syntaxe {% tr for item in table %}
        return self._table_data

    def _format_status_cell(
        self, passed: bool, true_label: str = "✓", false_label: str = "✗"
    ) -> str:
        """
        Formate une cellule de statut avec couleur conditionnelle.

        Args:
            passed: True si le critère est passé
            true_label: Texte pour statut réussi (défaut: ✓)
            false_label: Texte pour statut échoué (défaut: ✗)

        Returns:
            Texte simple (pas de RichText pour compatibilité)
        """
        # Pour l'instant, retourner du texte simple
        # TODO: Implémenter RichText quand le template sera adapté
        if passed:
            return f"{true_label} PASS"
        else:
            return f"{false_label} FAIL"

    def _format_number(self, value: float, decimals: int = 2, unit: str = "") -> str:
        """
        Formate un nombre avec décimales et unité.

        Args:
            value: Valeur numérique
            decimals: Nombre de décimales
            unit: Unité optionnelle (ex: "h", "kW", "%")

        Returns:
            Chaîne formatée
        """
        formatted = f"{value:.{decimals}f}"
        if unit:
            formatted += f" {unit}"
        return formatted
