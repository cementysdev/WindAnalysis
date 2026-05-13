"""
Présentateur Word spécifique au workflow RunTest.

Utilise une stratégie de remplissage des tableaux par index numérique.
Le template contient des tableaux pré-formatés avec headers, on remplace leur contenu.
"""

from typing import Dict, Any, List
from docx import Document
from .word_presenter import WordPresenter
from src.logger_config import get_logger

logger = get_logger(__name__)


class RunTestWordPresenter(WordPresenter):
    """
    Présentateur Word pour les rapports RunTest.

    Stratégie de remplissage des tableaux:
    - Template contient déjà des tableaux avec headers et structure
    - On parcourt les tableaux dans l'ordre d'apparition (index numérique)
    - On remplace le contenu en fonction d'un mapping fixe
    - Compatible avec les templates RunTest existants

    Ordre des tableaux dans le template:
    1. Historique révisions (ignoré)
    2. Liste fichiers CSV
    3. Résumé global (summary_table)
    4. Heures consécutives (critère 1)
    5. Cut-in/cut-out (critère 2)
    6. Puissance nominale - valeurs (critère 3a)
    7. Puissance nominale - durée (critère 3b)
    8. Autonomie (critère 4)
    9. Disponibilité (critère 5)
    """

    def _process_tables(self, doc: Document, context: Dict[str, Any]) -> None:
        """
        Remplit les tableaux en parcourant par index numérique.

        Args:
            doc: Document Word chargé
            context: Contexte avec les données de tableaux
        """
        logger.debug("Filling tables using RunTest index-based strategy...")

        # Mapping index → nom de table dans le contexte
        table_mapping = {
            1: "csv_files_table",                   # Liste des fichiers CSV
            2: "summary_table",                     # Résumé global
            3: "consecutive_hours_table",           # Critère 1
            4: "cut_in_cut_out_table",              # Critère 2
            5: "nominal_power_values_table",        # Critère 3a
            6: "nominal_power_duration_table",      # Critère 3b
            7: "autonomous_operation_table",        # Critère 4
            8: "availability_table",                # Critère 5
        }

        # Parcourir les tableaux du document
        for table_idx, table in enumerate(doc.tables):
            if table_idx in table_mapping:
                table_name = table_mapping[table_idx]

                if table_name in context:
                    data = context[table_name]
                    if isinstance(data, list) and len(data) > 0:
                        self._fill_table_by_index(table, data)
                        logger.debug(f"✅ Table {table_idx} ('{table_name}') filled with {len(data)} rows")
                    else:
                        logger.warning(f"⚠️ Empty data for table {table_idx} ('{table_name}')")
                else:
                    logger.warning(f"⚠️ Table '{table_name}' not found in context")
            else:
                # Table non mappée (ex: historique révisions, graphiques)
                logger.debug(f"Skipping table {table_idx} (not in mapping)")

    def _fill_table_by_index(self, table, data: List[Dict[str, Any]]) -> None:
        """
        Remplit une table existante avec les données.

        Stratégie:
        - La table existe déjà avec un header (première ligne)
        - On ajoute de nouvelles lignes pour chaque élément de data
        - L'ordre des colonnes est défini par l'ordre des clés du dict (Python 3.7+)

        Args:
            table: Tableau Word existant
            data: Liste de dictionnaires avec les données (ordre des clés = ordre des colonnes)
        """
        # Supprimer les lignes existantes après le header (si présentes)
        # Note: On garde la première ligne (header) et on supprime le reste
        while len(table.rows) > 1:
            table._element.remove(table.rows[-1]._element)

        # Ajouter les nouvelles lignes avec données
        for row_data in data:
            new_row = table.add_row()

            # Remplir les cellules selon l'ordre des valeurs du dict
            # Python 3.7+ garantit que dict.values() suit l'ordre d'insertion
            for col_idx, value in enumerate(row_data.values()):
                if col_idx < len(new_row.cells):
                    new_row.cells[col_idx].text = str(value)
                else:
                    # Plus de valeurs que de colonnes - warning
                    logger.warning(
                        f"⚠️ More values than columns: "
                        f"{len(list(row_data.values()))} values, {len(new_row.cells)} columns"
                    )
                    break
