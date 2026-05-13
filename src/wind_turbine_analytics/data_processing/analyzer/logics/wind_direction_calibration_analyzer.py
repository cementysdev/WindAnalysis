from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
from src.logger_config import get_logger
import pandas as pd
import numpy as np
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineConfig,
    ValidationCriteria,
    Criterion,
)
from typing import Dict, Any
import dateparser

logger = get_logger(__name__)


class WindDirectionCalibrationAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _calculate_angular_difference(
        angle1: pd.Series, angle2: pd.Series
    ) -> pd.Series:
        """
        Calcule la différence angulaire minimale entre deux angles (0-360°).
        Gère le wraparound (ex: 359° et 1° → écart de 2° et non 358°).

        Args:
            angle1: Première série d'angles en degrés (0-360)
            angle2: Deuxième série d'angles en degrés (0-360)

        Returns:
            Série des écarts absolus en degrés [0-180°]
        """
        diff = np.abs(angle1 - angle2)
        # Si la différence > 180°, prendre le chemin le plus court (360° - diff)
        diff = np.where(diff > 180, 360 - diff, diff)
        return diff

    def _compute(
        self,
        operation_data: pd.DataFrame,
        log_data: pd.DataFrame,
        turbine_config: TurbineConfig,
        criteria: ValidationCriteria,
    ) -> Dict[str, Any]:

        test_start = turbine_config.test_start
        test_end = turbine_config.test_end
        mapping = turbine_config.mapping_operation_data
        timestamp_col = mapping.timestamp

        # Colonnes des variables d'intérêt
        wind_speed_col = mapping.wind_speed
        wind_direction_col = mapping.wind_direction
        nacelle_position_col = mapping.nacelle_position

        # Vérifier que les colonnes nécessaires existent
        if not wind_direction_col:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: wind_direction column not configured"
            )
            return {"error": "wind_direction column not configured"}

        if not nacelle_position_col:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: nacelle_position column not configured"
            )
            return {"error": "nacelle_position column not configured"}

        # Filtrer par période de test
        test_data = operation_data[
            (operation_data[timestamp_col] >= test_start)
            & (operation_data[timestamp_col] <= test_end)
        ].copy()

        if len(test_data) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No data in test period"
            )
            return {"error": "No data in test period"}

        # Convertir en numérique
        test_data[wind_direction_col] = pd.to_numeric(
            test_data[wind_direction_col], errors="coerce"
        )
        test_data[nacelle_position_col] = pd.to_numeric(
            test_data[nacelle_position_col], errors="coerce"
        )
        test_data[wind_speed_col] = pd.to_numeric(
            test_data[wind_speed_col], errors="coerce"
        )

        # Obtenir le cut-in depuis criteria
        v_min = criteria.validation_criterion.get(
            "cut_in_to_cut_out", Criterion()
        ).specification
        if isinstance(v_min, (list, tuple)):
            v_min = v_min[0]
        else:
            v_min = 3.0  # Valeur par défaut

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Filtering data with wind_speed > {v_min} m/s"
        )

        # Filtrer par vitesse de vent (uniquement périodes actives)
        test_data = test_data[test_data[wind_speed_col] > v_min].copy()

        if len(test_data) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No data after wind speed filtering"
            )
            return {"error": "No data after wind speed filtering"}

        # Supprimer les lignes avec NaN dans wind_direction ou nacelle_position
        test_data = test_data.dropna(
            subset=[wind_direction_col, nacelle_position_col]
        )

        if len(test_data) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No valid data after removing NaN"
            )
            return {"error": "No valid data after removing NaN"}

        # Calculer l'écart angulaire pour chaque point
        test_data["angular_difference"] = self._calculate_angular_difference(
            test_data[wind_direction_col], test_data[nacelle_position_col]
        )

        # Créer plage journalière
        daily_range = pd.date_range(start=test_start, end=test_end, freq="1D")

        # Listes pour stocker les résultats journaliers
        daily_results = []

        for i in range(len(daily_range) - 1):
            day_start = daily_range[i]
            day_end = daily_range[i + 1]

            # Filtrer les données du jour
            day_data = test_data[
                (test_data[timestamp_col] >= day_start)
                & (test_data[timestamp_col] < day_end)
            ]

            if len(day_data) == 0:
                # Pas de données ce jour-là, skip
                continue

            # Calculer les 4 métriques
            mean_error = day_data["angular_difference"].mean()
            std_error = day_data["angular_difference"].std()
            max_error = day_data["angular_difference"].max()

            # Corrélation (gérer les cas où variance = 0)
            if (
                day_data[wind_direction_col].std() > 0
                and day_data[nacelle_position_col].std() > 0
            ):
                correlation = (
                    day_data[[wind_direction_col, nacelle_position_col]]
                    .corr()
                    .iloc[0, 1]
                )
            else:
                correlation = np.nan

            daily_results.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "mean_angular_error": round(mean_error, 2),
                    "std_angular_error": round(std_error, 2),
                    "max_angular_error": round(max_error, 2),
                    "correlation": (
                        round(correlation, 3) if not np.isnan(correlation) else None
                    ),
                    "num_measurements": len(day_data),
                }
            )

        # Statistiques globales sur toute la période
        overall_mean_error = test_data["angular_difference"].mean()
        overall_std_error = test_data["angular_difference"].std()
        overall_max_error = test_data["angular_difference"].max()

        # Corrélation globale
        if (
            test_data[wind_direction_col].std() > 0
            and test_data[nacelle_position_col].std() > 0
        ):
            overall_correlation = (
                test_data[[wind_direction_col, nacelle_position_col]]
                .corr()
                .iloc[0, 1]
            )
        else:
            overall_correlation = np.nan

        # Critère de validation : écart moyen < 5°
        threshold = 5.0  # degrés
        criterion_met = overall_mean_error < threshold

        # Determine status level based on mean angular error
        from src.wind_turbine_analytics.data_processing.status_levels import StatusLevel
        status_level = StatusLevel.from_angle_error(
            overall_mean_error,
            thresholds={"success": 3.0, "minor": 5.0, "warning": 7.0, "major": 10.0}
        )

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Wind direction calibration analysis completed. "
            f"Mean angular error: {overall_mean_error:.2f}°, Threshold: {threshold}°, "
            f"Criterion met: {criterion_met}, Status: {str(status_level)}"
        )

        # Créer chart_data avec colonnes standardisées pour les visualiseurs
        # Vérifier que toutes les colonnes nécessaires existent
        columns_to_include = []
        standard_names = []

        if wind_direction_col in test_data.columns:
            columns_to_include.append(wind_direction_col)
            standard_names.append("wind_direction")

        if mapping.activation_power and mapping.activation_power in test_data.columns:
            columns_to_include.append(mapping.activation_power)
            standard_names.append("activation_power")

        if wind_speed_col in test_data.columns:
            columns_to_include.append(wind_speed_col)
            standard_names.append("wind_speed")

        if timestamp_col in test_data.columns:
            columns_to_include.append(timestamp_col)
            standard_names.append("timestamp")

        if nacelle_position_col in test_data.columns:
            columns_to_include.append(nacelle_position_col)
            standard_names.append("nacelle_position")

        chart_data_df = test_data[columns_to_include].copy()
        chart_data_df.columns = standard_names

        return {
            "overall_mean_angular_error": round(overall_mean_error, 2),
            "overall_std_angular_error": round(overall_std_error, 2),
            "overall_max_angular_error": round(overall_max_error, 2),
            "overall_correlation": (
                round(overall_correlation, 3)
                if not np.isnan(overall_correlation)
                else None
            ),
            "threshold_degrees": threshold,
            "criterion_met": criterion_met,
            "status_level": status_level,
            "total_measurements": len(test_data),
            "daily_calibration": daily_results,
            "chart_data": chart_data_df,
        }