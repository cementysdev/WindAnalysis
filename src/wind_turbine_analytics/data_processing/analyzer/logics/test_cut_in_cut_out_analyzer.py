from src.wind_turbine_analytics.application.utils.load_data import load_csv
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
from src.wind_turbine_analytics.application.utils.load_data import (
    prepare_log_dataframe_with_mapping,
)

logger = get_logger(__name__)


class TestCutInCutOutAnalyzer(BaseAnalyzer):
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
        Analyse des périodes de fonctionnement entre cut-in et cut-out.

        Logique :
        STEP 1 : Filtrer les données (wind_speed entre cut-in/cut-out, power > 0)
        STEP 2 : Détecter les périodes continues disponibles/indisponibles
        STEP 3 : Soustraire les arrêts non autorisés de chaque période
        STEP 4 : Vérifier le critère de succès (au moins une période >= seuil)
        """

        # Extraire les informations de configuration
        test_start = pd.to_datetime(turbine_config.test_start, dayfirst=True)
        test_end = pd.to_datetime(turbine_config.test_end, dayfirst=True)
        mapping = turbine_config.mapping_operation_data
        timestamp_col = mapping.timestamp
        wind_speed_col = mapping.wind_speed
        power_col = mapping.activation_power

        # Récupérer les critères
        cut_in_cut_out_criterion = criteria.validation_criterion.get(
            "cut_in_to_cut_out", Criterion()
        )
        required_hours = cut_in_cut_out_criterion.value
        cut_in_speed, cut_out_speed = cut_in_cut_out_criterion.specification

        logger.debug(
            f"Analyse cut-in/cut-out pour {turbine_config.turbine_id}: "
            f"cut-in={cut_in_speed} m/s, cut-out={cut_out_speed} m/s, "
            f"critère={required_hours}h"
        )

        # Charger les données de log
        manager = NordexN311LogCodeManager()
        if log_data.empty:
            logger.error(f"Log data is empty for turbine {turbine_config.turbine_id}")
            raise ValueError(
                f"Log data is empty for turbine {turbine_config.turbine_id}"
            )

        # Préparer le DataFrame de log avec mapping
        log_prepared, log_start_col, log_end_col = prepare_log_dataframe_with_mapping(
            log_data, turbine_config.mapping_log_data
        )

        # Copier et filtrer les données opérationnelles
        df = operation_data.copy()
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], dayfirst=True)
        df = df.sort_values(timestamp_col)

        # Filtrer sur la période de test
        mask_test_period = (df[timestamp_col] >= test_start) & (
            df[timestamp_col] <= test_end
        )
        df_filtered = df[mask_test_period].copy()

        if len(df_filtered) == 0:
            logger.warning("Aucune donnée dans la période de test")
            return {
                "available_periods": [],
                "unavailable_periods": [],
                "max_available_duration_hours": 0.0,
                "criterion_met": False,
            }

        # STEP 1: Créer le filtre (wind_speed entre cut-in/cut-out ET power > 0)
        # Ensure wind speed column is float to avoid comparison issues
        if not pd.api.types.is_float_dtype(df_filtered[wind_speed_col]):
            logger.warning(
                "Column '%s' is not float (dtype=%s). Converting to float.",
                wind_speed_col,
                df_filtered[wind_speed_col].dtype,
            )
            df_filtered[wind_speed_col] = pd.to_numeric(
                df_filtered[wind_speed_col], errors="coerce"
            ).astype(float)
        if not pd.api.types.is_float_dtype(df_filtered[power_col]):
            logger.warning(
                "Column '%s' is not float (dtype=%s). Converting to float.",
                power_col,
                df_filtered[power_col].dtype,
            )
            df_filtered[power_col] = pd.to_numeric(
                df_filtered[power_col], errors="coerce"
            ).astype(float)

        df_filtered["is_available"] = (
            (df_filtered[wind_speed_col] >= cut_in_speed)
            & (df_filtered[wind_speed_col] <= cut_out_speed)
            & (df_filtered[power_col] > 0)
        )

        # STEP 2: Détecter les périodes continues (groupes)
        df_filtered["period_change"] = (
            df_filtered["is_available"] != df_filtered["is_available"].shift()
        )
        df_filtered["group"] = df_filtered["period_change"].cumsum()

        # Agréger par groupe
        periods = df_filtered.groupby("group").agg(
            {
                timestamp_col: ["min", "max"],
                "is_available": "first",
            }
        )

        periods.columns = ["start", "end", "is_available"]
        periods["gross_duration_hours"] = (
            periods["end"] - periods["start"]
        ).dt.total_seconds() / 3600

        # STEP 3: Soustraire les arrêts non autorisés de chaque période
        unauthorized_codes = manager.get_unauthorized_stop_codes()
        unauthorized_code_list = [code.code for code in unauthorized_codes]

        logger.debug(
            f"Codes d'arrêt non autorisés identifiés: {len(unauthorized_code_list)}"
        )

        # Préparer les colonnes de log
        # Format: "03.02.2026 12:46:01:880" (avec millisecondes après :)
        # Remplacer le dernier : par . pour pandas

        # Filtrer les logs sur les codes non autorisés
        # Utiliser get_code() pour gérer les alias FE/FM

        code_col = turbine_config.mapping_log_data.oper
        unauthorized_logs = log_prepared[
            log_prepared[code_col].apply(
                lambda x: (
                    manager.get_code(str(x)) is not None
                    and manager.get_code(str(x)).affects_availability()
                    and manager.get_code(str(x)).is_critical_stop()
                )
            )
        ].copy()

        logger.debug(
            f"Arrêts non autorisés trouvés dans les logs: {len(unauthorized_logs)}"
        )

        # Pour chaque période, calculer le temps d'arrêt non autorisé et collecter les codes
        available_periods = []
        unavailable_periods = []

        for _, period in periods.iterrows():
            period_start = period["start"]
            period_end = period["end"]
            gross_duration = period["gross_duration_hours"]
            is_available = period["is_available"]

            # Trouver les arrêts non autorisés qui chevauchent cette période
            overlapping_stops = unauthorized_logs[
                (unauthorized_logs[log_start_col] < period_end)
                & (unauthorized_logs[log_end_col] > period_start)
            ]

            # Calculer le temps total d'arrêt non autorisé et collecter détails
            total_stop_duration_hours = 0.0
            stop_details = []
            alarm_codes_for_period = []

            for _, stop in overlapping_stops.iterrows():
                # Calculer le chevauchement
                overlap_start = max(stop[log_start_col], period_start)
                overlap_end = min(stop[log_end_col], period_end)
                overlap_duration = (overlap_end - overlap_start).total_seconds() / 3600

                if overlap_duration > 0:
                    total_stop_duration_hours += overlap_duration

                    # Récupérer le code et sa description
                    code_value = str(stop[code_col])
                    error_code = manager.get_code(code_value)

                    # Ajouter le code à la liste (éviter les doublons)
                    if code_value not in alarm_codes_for_period:
                        alarm_codes_for_period.append(code_value)

                    stop_details.append(
                        {
                            "code": code_value,
                            "description": (
                                error_code.description
                                if error_code
                                else "Description non disponible"
                            ),
                            "start": overlap_start,
                            "end": overlap_end,
                            "duration_hours": round(overlap_duration, 2),
                        }
                    )

            # Durée nette = durée brute - arrêts non autorisés
            net_duration_hours = max(0, gross_duration - total_stop_duration_hours)

            period_data = {
                "start": period_start,
                "end": period_end,
                "gross_duration_hours": round(gross_duration, 2),
                "unauthorized_stop_hours": round(total_stop_duration_hours, 2),
                "net_duration_hours": round(net_duration_hours, 2),
                "unauthorized_stops": stop_details,  # Liste des arrêts détaillés
                "alarm_codes": alarm_codes_for_period,  # Codes d'alarme pour cette période
                "is_available": is_available,  # Indicateur disponible/indisponible
            }

            if is_available:
                available_periods.append(period_data)
            else:
                unavailable_periods.append(period_data)

        # STEP 4: Vérifier le critère (au moins une période >= required_hours)
        max_net_duration = (
            max(p["net_duration_hours"] for p in available_periods)
            if available_periods
            else 0.0
        )

        criterion_met = max_net_duration >= required_hours

        logger.debug(
            f"Durée maximale continue (nette): {max_net_duration}h, "
            f"Critère: {required_hours}h, Réussi: {criterion_met}"
        )

        # Combiner toutes les périodes et trier par chronologie
        all_periods = available_periods + unavailable_periods
        all_periods_sorted = sorted(all_periods, key=lambda p: p["start"])

        return {
            "all_periods": all_periods_sorted,  # Toutes les périodes triées
            "available_periods": available_periods,
            "unavailable_periods": unavailable_periods,
            "max_net_duration_hours": round(max_net_duration, 2),
            "required_hours": required_hours,
            "criterion_met": criterion_met,
            "cut_in_speed": cut_in_speed,
            "cut_out_speed": cut_out_speed,
        }
