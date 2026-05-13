from src.wind_turbine_analytics.application.utils.load_data import (
    prepare_log_dataframe_with_mapping,
)
from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
from src.logger_config import get_logger
import pandas as pd
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineConfig,
    ValidationCriteria,
    Criterion,
)
from typing import Dict, Any
from src.wind_turbine_analytics.data_processing.log_code.generator_type.nordex_n311_log_code_manager import (
    NordexN311LogCodeManager,
)
from src.wind_turbine_analytics.data_processing.log_code.base_log_code import (
    ResetMode,
)

logger = get_logger(__name__)


class AutonomousOperationAnalyzer(BaseAnalyzer):
    """
    Analyseur d'autonomie d'exploitation des éoliennes.

    Vérifie que l'éolienne peut fonctionner en mode automatique sans intervention
    manuelle sur site (local restart) pendant la période de test.

    Critère de succès : Nombre de codes nécessitant un redémarrage manuel <= seuil
    (typiquement 3 dans config.yml: local_restarts.value)
    """

    def __init__(self) -> None:
        super().__init__()

    def _compute(
        self,
        operation_data: pd.DataFrame,
        log_data: pd.DataFrame,
        turbine_config: TurbineConfig,
        criteria: ValidationCriteria,
    ) -> Dict[str, Any]:
        """
        Analyse l'autonomie d'exploitation d'une éolienne.

        Logique:
        STEP 1: Charger les données de log et préparer avec mapping
        STEP 2: Filtrer les logs sur la période de test (runtest_start - runtest_end)
        STEP 3: Identifier les codes nécessitant un redémarrage manuel (MANUAL ou SAFETY_LOCAL)
        STEP 4: Compter les occurrences et évaluer le critère
        STEP 5: Retourner les détails des arrêts et le statut de validation

        Args:
            operation_data: DataFrame des données d'opération (non utilisé directement ici)
            turbine_config: Configuration de la turbine
            criteria: Critères de validation

        Returns:
            Dictionnaire avec:
                - manual_restart_codes: Liste des codes nécessitant intervention manuelle
                - manual_restart_count: Nombre total d'arrêts manuels
                - required_threshold: Seuil maximal autorisé
                - criterion_met: True si count <= threshold
                - manual_restart_events: Liste détaillée des événements
        """
        # STEP 1: Extraire les informations de configuration

        test_start = turbine_config.test_start
        test_end = turbine_config.test_end

        # Récupérer le critère local_restarts
        local_restart_criterion = criteria.validation_criterion.get(
            "local_restarts", Criterion()
        )
        required_threshold = local_restart_criterion.value

        logger.debug(
            f"Analyse autonomie d'exploitation pour {turbine_config.turbine_id}: "
            f"seuil={required_threshold} redémarrages manuels max"
        )

        # Charger les données de log
        manager = NordexN311LogCodeManager()

        if log_data.empty:
            logger.warning(
                f"Aucune donnée de log pour {turbine_config.turbine_id} "
                f"à {turbine_config.general_information.path_log_data}"
            )
            return {
                "manual_restart_codes": [],
                "manual_restart_count": 0,
                "required_threshold": required_threshold,
                "criterion_met": True,  # Pas d'arrêts = succès
                "manual_restart_events": [],
            }

        # Préparer le DataFrame de log avec mapping
        log_prepared, log_start_col, _ = prepare_log_dataframe_with_mapping(
            log_data, turbine_config.mapping_log_data
        )

        # STEP 2: Filtrer les logs sur la période de test
        # On garde les événements qui se sont produits pendant la période de test
        mask_test_period = (log_prepared[log_start_col] >= test_start) & (
            log_prepared[log_start_col] <= test_end
        )
        log_test_period = log_prepared[mask_test_period].copy()

        logger.debug(
            f"Nombre d'événements de log dans la période de test: {len(log_test_period)}"
        )

        if len(log_test_period) == 0:
            logger.debug("Aucun événement dans la période de test -> Autonomie validée")
            return {
                "manual_restart_codes": [],
                "manual_restart_count": 0,
                "required_threshold": required_threshold,
                "criterion_met": True,
                "manual_restart_events": [],
            }

        # STEP 3: Identifier les codes nécessitant un redémarrage manuel
        # Méthode 1: Utiliser get_codes_by_reset_mode() pour récupérer les codes MANUAL et SAFETY_LOCAL
        manual_codes = manager.get_codes_by_reset_mode(ResetMode.MANUAL)
        safety_local_codes = manager.get_codes_by_reset_mode(ResetMode.SAFETY_LOCAL)

        # Combiner les deux listes
        manual_restart_required_codes = manual_codes + safety_local_codes
        manual_restart_code_list = [code.code for code in manual_restart_required_codes]

        logger.debug(
            f"Codes nécessitant redémarrage manuel identifiés: "
            f"{len(manual_restart_code_list)}"
        )

        # Filtrer les événements de log qui correspondent à ces codes
        # Utiliser le mapping pour identifier la colonne code
        code_col = turbine_config.mapping_log_data.oper  # ou .name selon le mapping

        # Gérer les deux cas possibles de mapping (oper ou name)
        if code_col in log_test_period.columns:
            code_column = code_col
        else:
            # Fallback: essayer l'autre colonne
            alt_code_col = turbine_config.mapping_log_data.name
            if alt_code_col in log_test_period.columns:
                code_column = alt_code_col
            else:
                logger.error(
                    f"Impossible de trouver la colonne de code dans les logs. "
                    f"Colonnes disponibles: {log_test_period.columns.tolist()}"
                )
                raise ValueError(
                    f"Colonne de code non trouvée pour {turbine_config.turbine_id}"
                )

        # Filtrer les événements avec codes manuels
        manual_restart_events = log_test_period[
            log_test_period[code_column].isin(manual_restart_code_list)
        ].copy()

        # STEP 4: Compter les occurrences (seulement les événements ON)
        # Un arrêt = une transition ON (pas besoin de compter le OFF)
        status_col = turbine_config.mapping_log_data.status
        if status_col in manual_restart_events.columns:
            manual_restart_on_events = manual_restart_events[
                manual_restart_events[status_col].str.upper() == "ON"
            ]
        else:
            # Si pas de colonne status, compter tous les événements
            logger.warning(
                f"Pas de colonne status dans les logs, tous les événements sont comptés"
            )
            manual_restart_on_events = manual_restart_events

        manual_restart_count = len(manual_restart_on_events)

        # STEP 5: Évaluer le critère
        criterion_met = manual_restart_count <= required_threshold

        logger.debug(
            f"Redémarrages manuels trouvés: {manual_restart_count}, "
            f"Seuil: {required_threshold}, Réussi: {criterion_met}"
        )

        # Préparer les détails des événements pour le rapport
        event_details = []
        for _, event in manual_restart_on_events.iterrows():
            event_details.append(
                {
                    "timestamp": event[log_start_col],
                    "code": event[code_column],
                    "name": event.get(turbine_config.mapping_log_data.name, "Unknown"),
                    "status": event.get(status_col, "ON"),
                }
            )

        # Si il y a des événements, afficher les détails
        if event_details:
            logger.warning(f"Détails des {manual_restart_count} redémarrages manuels:")
            for evt in event_details:
                logger.warning(
                    f"  - {evt['timestamp']}: Code {evt['code']} ({evt['name']})"
                )

        return {
            "manual_restart_codes": manual_restart_code_list,
            "manual_restart_count": manual_restart_count,
            "required_threshold": required_threshold,
            "criterion_met": criterion_met,
            "manual_restart_events": event_details,
        }
