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
    CodeCriticality,
    FunctionalSystem,
)

logger = get_logger(__name__)


class CodeErrorAnalyzer(BaseAnalyzer):
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
        Analyse les codes erreurs présents dans les log_data:
        - Fréquence des codes erreurs
        - Corrélation avec baisses de production et vitesses de vent
        - Identification des codes les plus fréquents et leur impact
        - Répartition par niveau de criticité
        """
        # Configuration et validation
        mapping_op = turbine_config.mapping_operation_data
        mapping_log = turbine_config.mapping_log_data

        timestamp_col = mapping_op.timestamp
        power_col = mapping_op.activation_power
        wind_speed_col = mapping_op.wind_speed
        code_col = mapping_log.oper
        start_date_col = mapping_log.start_date
        end_date_col = mapping_log.end_date

        test_start = turbine_config.test_start
        test_end = turbine_config.test_end

        # Initialiser le gestionnaire de codes
        manager = NordexN311LogCodeManager()

        # Filtrer les données dans la période de test
        operation_data[timestamp_col] = pd.to_datetime(
            operation_data[timestamp_col], errors="coerce"
        )
        op_filtered = operation_data[
            (operation_data[timestamp_col] >= test_start)
            & (operation_data[timestamp_col] <= test_end)
        ].copy()

        # Filtrer les logs dans la période de test
        log_data[start_date_col] = pd.to_datetime(
            log_data[start_date_col], errors="coerce"
        )
        log_data[end_date_col] = pd.to_datetime(log_data[end_date_col], errors="coerce")

        log_filtered = log_data[
            (log_data[start_date_col] <= test_end)
            & (log_data[end_date_col] >= test_start)
        ].copy()

        if log_filtered.empty:
            logger.warning(
                f"Aucun code d'erreur trouvé pour la turbine {turbine_config.turbine_id}"
            )
            return {"error": "No error codes in period", "total_codes": 0}

        # 1. ANALYSE DE FRÉQUENCE DES CODES
        code_frequency = log_filtered[code_col].value_counts().to_dict()
        total_events = len(log_filtered)

        # Enrichir avec les informations du manager
        code_details = []
        for code, count in code_frequency.items():
            error_code = manager.get_code(str(code))
            if error_code:
                code_details.append(
                    {
                        "code": code,
                        "count": int(count),
                        "frequency_percent": round(count / total_events * 100, 2),
                        "description": error_code.description,
                        "criticality": (
                            error_code.criticality.value
                            if error_code.criticality
                            else "unknown"
                        ),
                        "system": (
                            error_code.functional_system.value
                            if error_code.functional_system
                            else "unknown"
                        ),
                        "reset_mode": error_code.reset_mode,
                        "affects_availability": error_code.affects_availability(),
                    }
                )
            else:
                code_details.append(
                    {
                        "code": code,
                        "count": int(count),
                        "frequency_percent": round(count / total_events * 100, 2),
                        "description": "Unknown code",
                        "criticality": "unknown",
                        "system": "unknown",
                        "reset_mode": "unknown",
                        "affects_availability": False,
                    }
                )

        # Trier par fréquence décroissante
        code_details = sorted(code_details, key=lambda x: x["count"], reverse=True)

        # 2. RÉPARTITION PAR CRITICITÉ
        criticality_stats = {}
        for crit in CodeCriticality:
            codes = [c for c in code_details if c["criticality"] == crit.value]
            total_count = sum(c["count"] for c in codes)
            criticality_stats[crit.value] = {
                "unique_codes": len(codes),
                "total_occurrences": total_count,
                "percent_of_total": (
                    round(total_count / total_events * 100, 2)
                    if total_events > 0
                    else 0
                ),
                "codes": [c["code"] for c in codes],
            }

        # Ajouter les codes inconnus
        unknown_codes = [c for c in code_details if c["criticality"] == "unknown"]
        if unknown_codes:
            total_unknown = sum(c["count"] for c in unknown_codes)
            criticality_stats["unknown"] = {
                "unique_codes": len(unknown_codes),
                "total_occurrences": total_unknown,
                "percent_of_total": round(total_unknown / total_events * 100, 2),
                "codes": [c["code"] for c in unknown_codes],
            }

        # 3. RÉPARTITION PAR SYSTÈME FONCTIONNEL
        system_stats = {}
        for system in FunctionalSystem:
            codes = [c for c in code_details if c["system"] == system.value]
            total_count = sum(c["count"] for c in codes)
            if total_count > 0:
                system_stats[system.value] = {
                    "unique_codes": len(codes),
                    "total_occurrences": total_count,
                    "percent_of_total": round(total_count / total_events * 100, 2),
                    "codes": [c["code"] for c in codes[:5]],  # Top 5 par système
                }

        # 4. ANALYSE D'IMPACT SUR LA PRODUCTION
        # Calculer la production moyenne pendant et hors périodes d'erreur
        P_nom = turbine_config.general_information.nominal_power
        if P_nom is None:
            P_nom = 3.78  # Valeur par défaut
        if P_nom <= 20:
            P_nom = P_nom * 1000  # Convertir MW en kW

        # Créer un masque pour les périodes avec codes critiques
        mask_critical = manager.create_time_mask(
            log_df=log_filtered,
            target_df=op_filtered,
            code_column=code_col,
            log_start_col=start_date_col,
            log_end_col=end_date_col,
            target_timestamp_col=timestamp_col,
            criticality_filter=[CodeCriticality.CRITICAL, CodeCriticality.HIGH],
        )

        # Inverser le masque pour avoir les périodes AVEC erreurs
        periods_with_errors = ~mask_critical
        periods_without_errors = mask_critical

        # Statistiques de production
        power_with_errors = op_filtered[periods_with_errors][power_col]
        power_without_errors = op_filtered[periods_without_errors][power_col]

        production_impact = {
            "mean_power_with_errors_kW": (
                round(float(power_with_errors.mean()), 2)
                if len(power_with_errors) > 0
                else 0
            ),
            "mean_power_without_errors_kW": (
                round(float(power_without_errors.mean()), 2)
                if len(power_without_errors) > 0
                else 0
            ),
            "periods_with_critical_errors_count": int(periods_with_errors.sum()),
            "periods_without_errors_count": int(periods_without_errors.sum()),
            "production_loss_percent": 0,
        }

        if production_impact["mean_power_without_errors_kW"] > 0:
            loss = (
                (
                    production_impact["mean_power_without_errors_kW"]
                    - production_impact["mean_power_with_errors_kW"]
                )
                / production_impact["mean_power_without_errors_kW"]
                * 100
            )
            production_impact["production_loss_percent"] = round(loss, 2)

        # 5. CORRÉLATION AVEC VITESSE DE VENT
        # Analyser la distribution des vitesses de vent lors des erreurs
        wind_with_errors = op_filtered[periods_with_errors][wind_speed_col]
        wind_without_errors = op_filtered[periods_without_errors][wind_speed_col]

        wind_correlation = {
            "mean_wind_with_errors_ms": (
                round(float(wind_with_errors.mean()), 2)
                if len(wind_with_errors) > 0
                else 0
            ),
            "mean_wind_without_errors_ms": (
                round(float(wind_without_errors.mean()), 2)
                if len(wind_without_errors) > 0
                else 0
            ),
            "wind_ranges": {},
        }

        # Répartition par plages de vent
        wind_bins = [(0, 3), (3, 8), (8, 13), (13, 20), (20, 30)]
        for v_min, v_max in wind_bins:
            mask_wind = (op_filtered[wind_speed_col] >= v_min) & (
                op_filtered[wind_speed_col] < v_max
            )
            errors_in_range = (periods_with_errors & mask_wind).sum()
            total_in_range = mask_wind.sum()

            if total_in_range > 0:
                wind_correlation["wind_ranges"][f"{v_min}-{v_max}m/s"] = {
                    "error_periods": int(errors_in_range),
                    "total_periods": int(total_in_range),
                    "error_rate_percent": round(
                        errors_in_range / total_in_range * 100, 2
                    ),
                }

        # 6. CODES LES PLUS IMPACTANTS
        # Calculer pour chaque code la durée totale d'indisponibilité
        impactful_codes = []
        for code_info in code_details[:10]:  # Top 10
            code = code_info["code"]
            code_logs = log_filtered[log_filtered[code_col] == code]

            # Calculer la durée totale
            total_duration_hours = 0
            for _, row in code_logs.iterrows():
                duration = (
                    row[end_date_col] - row[start_date_col]
                ).total_seconds() / 3600
                total_duration_hours += duration

            impactful_codes.append(
                {
                    "code": code,
                    "occurrences": code_info["count"],
                    "total_duration_hours": round(total_duration_hours, 2),
                    "criticality": code_info["criticality"],
                    "description": code_info["description"],
                }
            )

        # Trier par durée totale
        impactful_codes = sorted(
            impactful_codes, key=lambda x: x["total_duration_hours"], reverse=True
        )

        # Calculate uptime percentage for status
        test_duration_hours = (test_end - test_start).total_seconds() / 3600
        total_error_duration = sum(code["total_duration_hours"] for code in impactful_codes)

        # Uptime percentage (temps sans erreur)
        uptime_pct = (
            ((test_duration_hours - total_error_duration) / test_duration_hours * 100)
            if test_duration_hours > 0
            else 0.0
        )

        # Determine status level based on uptime
        from src.wind_turbine_analytics.data_processing.status_levels import StatusLevel
        status_level = StatusLevel.from_percentage(uptime_pct)

        logger.debug(
            "Turbine %s: Error duration = %.2fh / %.2fh, Uptime = %.2f%%, Status = %s",
            turbine_config.turbine_id,
            total_error_duration,
            test_duration_hours,
            uptime_pct,
            str(status_level),
        )

        # Résultat final
        return {
            "summary": {
                "total_error_events": total_events,
                "unique_error_codes": len(code_frequency),
                "test_period_hours": round(
                    (test_end - test_start).total_seconds() / 3600, 2
                ),
                "turbine_id": turbine_config.turbine_id,
            },
            "code_frequency": code_details[:20],  # Top 20
            "criticality_distribution": criticality_stats,
            "system_distribution": system_stats,
            "production_impact": production_impact,
            "wind_correlation": wind_correlation,
            "most_impactful_codes": impactful_codes[:10],  # Top 10
            "total_error_duration_hours": round(total_error_duration, 2),
            "test_duration_hours": round(test_duration_hours, 2),
            "uptime_pct": round(uptime_pct, 2),
            "status_level": status_level,
        }
