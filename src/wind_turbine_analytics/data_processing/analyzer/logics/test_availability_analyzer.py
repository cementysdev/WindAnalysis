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

# Import local pour éviter import circulaire avec runtest_workflow
from src.wind_turbine_analytics.application.utils.load_data import (
    prepare_log_dataframe_with_mapping,
)

logger = get_logger(__name__)


class TestAvailabilityAnalyzer(BaseAnalyzer):
    """
    Analyseur de disponibilité des éoliennes.

    Calcule la disponibilité pendant la période de test en soustrayant
    les arrêts non autorisés de la durée totale.
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
        Calcule la disponibilité de l'éolienne pendant la période de test.

        Logique:
        STEP 1: Identifier la période de test (test_start et test_end)
        STEP 2: Calculer la durée totale calendaire
        STEP 3: Calculer la durée d'arrêts non autorisés (basée sur les logs)
        STEP 4: Calculer la disponibilité en % et valider le critère

        Formule: availability = (durée_totale - durée_arrêts) / durée_totale × 100
        """
        # STEP 1: Extraire la période de test
        test_start = pd.to_datetime(turbine_config.test_start, dayfirst=True)
        test_end = pd.to_datetime(turbine_config.test_end, dayfirst=True)

        # Récupérer le critère availability
        availability_criterion = criteria.validation_criterion.get(
            "availability", Criterion()
        )
        required_threshold = availability_criterion.value  # Seuil en % (ex: 92)

        logger.debug(
            f"Analyse disponibilité pour {turbine_config.turbine_id}: "
            f"seuil={required_threshold}%"
        )

        # STEP 2: Calculer la durée totale calendaire (en heures)
        total_hours = (test_end - test_start).total_seconds() / 3600.0

        logger.debug(
            f"Période de test: {test_start} à {test_end} "
            f"(durée totale: {total_hours:.2f}h)"
        )

        if total_hours <= 0:
            logger.error(
                f"Durée de test invalide pour {turbine_config.turbine_id}: "
                f"{total_hours}h"
            )
            return {
                "total_hours": 0.0,
                "unauthorized_downtime_hours": 0.0,
                "available_hours": 0.0,
                "availability_percent": 0.0,
                "required_threshold": required_threshold,
                "criterion_met": False,
                "unauthorized_events": [],
            }

        # STEP 3: Calculer la durée d'arrêts non autorisés
        manager = NordexN311LogCodeManager()

        if log_data.empty:
            logger.warning(
                f"Aucune donnée de log pour {turbine_config.turbine_id}. "
                f"Disponibilité = 100% (aucun arrêt détecté)"
            )
            return {
                "total_hours": round(total_hours, 2),
                "unauthorized_downtime_hours": 0.0,
                "available_hours": round(total_hours, 2),
                "availability_percent": 100.0,
                "required_threshold": required_threshold,
                "criterion_met": True,
                "unauthorized_events": [],
            }

        # Préparer le DataFrame de log avec mapping
        log_prepared, log_start_col, _ = prepare_log_dataframe_with_mapping(
            log_data, turbine_config.mapping_log_data
        )

        # Identifier les codes d'arrêt non autorisés
        unauthorized_codes = manager.get_unauthorized_stop_codes()
        unauthorized_code_list = [code.code for code in unauthorized_codes]

        logger.debug(
            f"Codes d'arrêt non autorisés identifiés: " f"{len(unauthorized_code_list)}"
        )

        if len(unauthorized_code_list) == 0:
            logger.warning(
                "Aucun code d'arrêt non autorisé défini. " "Disponibilité = 100%"
            )
            return {
                "total_hours": round(total_hours, 2),
                "unauthorized_downtime_hours": 0.0,
                "available_hours": round(total_hours, 2),
                "availability_percent": 100.0,
                "required_threshold": required_threshold,
                "criterion_met": True,
                "unauthorized_events": [],
            }

        # Filtrer les logs sur les codes non autorisés
        code_col = turbine_config.mapping_log_data.oper
        if code_col not in log_prepared.columns:
            code_col = turbine_config.mapping_log_data.name

        status_col = turbine_config.mapping_log_data.status

        # Filtrer les événements avec codes non autorisés
        alarms = log_prepared[
            log_prepared[code_col].isin(unauthorized_code_list)
        ].copy()

        if alarms.empty:
            logger.debug(
                "Aucun événement d'arrêt non autorisé dans les logs. "
                "Disponibilité = 100%"
            )
            return {
                "total_hours": round(total_hours, 2),
                "unauthorized_downtime_hours": 0.0,
                "available_hours": round(total_hours, 2),
                "availability_percent": 100.0,
                "required_threshold": required_threshold,
                "criterion_met": True,
                "unauthorized_events": [],
            }

        # Convertir les timestamps et trier
        alarms[log_start_col] = pd.to_datetime(alarms[log_start_col], errors="coerce")
        alarms = alarms.dropna(subset=[log_start_col])
        alarms = alarms.sort_values(log_start_col)

        # Calculer la durée d'arrêts non autorisés en gérant ON/OFF
        unauthorized_downtime_hours = 0.0
        unauthorized_events = []

        active_by_code = {}  # Dict[code, count] pour gérer chevauchements
        active_start = None

        for _, row in alarms.iterrows():
            event_ts = row[log_start_col]
            code = row[code_col]
            status = str(row[status_col]).strip().upper()

            # État avant l'événement
            before_active = any(count > 0 for count in active_by_code.values())

            # Mettre à jour l'état selon ON/OFF
            if status == "ON":
                active_by_code[code] = active_by_code.get(code, 0) + 1
            elif status == "OFF":
                previous = active_by_code.get(code, 0)
                if previous > 0:
                    active_by_code[code] = previous - 1

            # État après l'événement
            after_active = any(count > 0 for count in active_by_code.values())

            # Transition inactive → active : démarrer la mesure
            if not before_active and after_active:
                active_start = event_ts

            # Transition active → inactive : ajouter la durée
            elif before_active and not after_active and active_start is not None:
                # Clipper dans la fenêtre de test
                start = max(active_start, test_start)
                end = min(event_ts, test_end)

                if end > start:
                    duration_hours = (end - start).total_seconds() / 3600.0
                    unauthorized_downtime_hours += duration_hours

                    unauthorized_events.append(
                        {
                            "start": start,
                            "end": end,
                            "duration_hours": round(duration_hours, 2),
                            "codes": [
                                c for c, cnt in active_by_code.items() if cnt > 0
                            ],
                        }
                    )

                active_start = None

        # Gérer les arrêts encore actifs à la fin du test
        if (
            any(count > 0 for count in active_by_code.values())
            and active_start is not None
        ):
            start = max(active_start, test_start)
            end = test_end

            if end > start:
                duration_hours = (end - start).total_seconds() / 3600.0
                unauthorized_downtime_hours += duration_hours

                unauthorized_events.append(
                    {
                        "start": start,
                        "end": end,
                        "duration_hours": round(duration_hours, 2),
                        "codes": [c for c, cnt in active_by_code.items() if cnt > 0],
                        "still_active": True,
                    }
                )

        # Limiter les valeurs dans [0, total_hours]
        unauthorized_downtime_hours = min(
            max(unauthorized_downtime_hours, 0.0), total_hours
        )

        # STEP 4: Calculer la disponibilité
        available_hours = max(total_hours - unauthorized_downtime_hours, 0.0)
        availability_percent = (
            100.0 * (available_hours / total_hours) if total_hours > 0 else 0.0
        )

        criterion_met = availability_percent >= required_threshold

        logger.debug(
            f"Disponibilité calculée: {availability_percent:.2f}% "
            f"(arrêts: {unauthorized_downtime_hours:.2f}h / {total_hours:.2f}h), "
            f"Seuil: {required_threshold}%, Réussi: {criterion_met}"
        )

        return {
            "total_hours": round(total_hours, 2),
            "unauthorized_downtime_hours": round(unauthorized_downtime_hours, 2),
            "available_hours": round(available_hours, 2),
            "availability_percent": round(availability_percent, 2),
            "required_threshold": required_threshold,
            "criterion_met": criterion_met,
            "unauthorized_events": unauthorized_events,
        }
