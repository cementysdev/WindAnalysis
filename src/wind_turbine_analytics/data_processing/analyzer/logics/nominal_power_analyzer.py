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

logger = get_logger(__name__)


class NominalPowerAnalyzer(BaseAnalyzer):
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
        Analyse de la puissance nominale d'une turbine.

        Logique:
        STEP 1: Filtrer les données sur la période de test
        STEP 2: Créer un masque où power >= specification% * P_nom
        STEP 3: Calculer la durée cumulée totale (nombre de points × 10min)
        STEP 4: Valider si durée >= value (heures requises)
        """
        # Extraire les informations de configuration
        test_start = pd.to_datetime(turbine_config.test_start, dayfirst=True)
        test_end = pd.to_datetime(turbine_config.test_end, dayfirst=True)
        mapping = turbine_config.mapping_operation_data
        timestamp_col = mapping.timestamp
        power_col = mapping.activation_power
        P_nom = turbine_config.general_information.nominal_power

        # Vérification de la puissance nominale
        if P_nom is None:
            logger.error(
                f"Nominal power not defined for turbine " f"{turbine_config.turbine_id}"
            )
            raise ValueError(f"Nominal power missing for {turbine_config.turbine_id}")

        # Convertir en kW si nécessaire (si < 100, c'est probablement en MW)
        if P_nom <= 100:
            logger.debug(
                f"Nominal power for turbine {turbine_config.turbine_id} "
                f"is {P_nom} MW, converting to kW"
            )
            P_nom = P_nom * 1000  # Convertir MW en kW

        # Récupérer les critères
        nominal_criterion = criteria.validation_criterion.get(
            "nominal_power_hours", Criterion()
        )
        required_hours = nominal_criterion.value
        power_threshold_percent = nominal_criterion.specification

        # Calculer le seuil de puissance
        power_threshold = (power_threshold_percent / 100.0) * P_nom

        logger.debug(
            f"Analyse puissance nominale pour {turbine_config.turbine_id}: "
            f"P_nom={P_nom}kW, seuil={power_threshold_percent}% "
            f"({power_threshold:.2f}kW), durée requise={required_hours}h"
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
                "total_duration_hours": 0.0,
                "required_hours": required_hours,
                "criterion_met": False,
                "power_threshold_kW": power_threshold,
                "power_threshold_percent": power_threshold_percent,
                "nominal_power_kW": P_nom,
                "selected_window_start": None,
                "selected_window_end": None,
            }

        # STEP 2: Créer un masque pour power >= seuil (utilise fillna pour gérer les NaN)
        mask = df_filtered[power_col].fillna(0) >= power_threshold

        # STEP 3: Calculer la durée cumulée (nombre de points × 10 minutes)
        total_duration = float(mask.sum()) * (10.0 / 60.0)

        # STEP 4: Valider le critère
        criterion_met = total_duration >= required_hours

        # Identifier les valeurs maximales dans la période de test
        max_power = df_filtered[power_col].max()
        max_power_idx = df_filtered[power_col].idxmax()
        max_power_timestamp = df_filtered.loc[max_power_idx, timestamp_col]

        # Déterminer la fenêtre de temps (premier et dernier point au-dessus du seuil)
        first_idx = mask[mask].index.min() if mask.any() else None
        last_idx = mask[mask].index.max() if mask.any() else None
        selected_window_start = (
            df_filtered.loc[first_idx, timestamp_col] if first_idx is not None else None
        )
        selected_window_end = (
            df_filtered.loc[last_idx, timestamp_col] if last_idx is not None else None
        )

        # Si wind_speed existe, récupérer aussi la vitesse max
        wind_speed_col = mapping.wind_speed
        if wind_speed_col and wind_speed_col in df_filtered.columns:
            max_wind_speed = df_filtered[wind_speed_col].max()
            max_wind_idx = df_filtered[wind_speed_col].idxmax()
            max_wind_timestamp = df_filtered.loc[max_wind_idx, timestamp_col]
        else:
            max_wind_speed = None
            max_wind_timestamp = None

        logger.debug(
            f"Durée totale >= {power_threshold_percent}% P_nom: "
            f"{total_duration:.2f}h, Critère: {required_hours}h, "
            f"Réussi: {criterion_met}"
        )
        logger.debug(
            f"Puissance max observée: {max_power:.2f}kW " f"le {max_power_timestamp}"
        )
        if max_wind_speed is not None:
            logger.debug(
                f"Vitesse vent max observée: {max_wind_speed:.2f}m/s "
                f"le {max_wind_timestamp}"
            )

        # Préparer les données pour visualisation (courbe de puissance + rose des vents)
        # Extraire wind_speed, power et wind_direction pour les visualizers
        chart_data = None
        if wind_speed_col and wind_speed_col in df_filtered.columns:
            # Colonnes à extraire
            cols_to_extract = [wind_speed_col, power_col]

            # Vérifier si wind_direction existe
            wind_dir_col = mapping.wind_direction if hasattr(mapping, 'wind_direction') else None
            if wind_dir_col and wind_dir_col in df_filtered.columns:
                cols_to_extract.append(wind_dir_col)

            chart_data = df_filtered[cols_to_extract].copy()

            # Renommer les colonnes
            new_names = ["wind_speed", "power"]
            if len(cols_to_extract) == 3:
                new_names.append("wind_direction")
            chart_data.columns = new_names

            # Supprimer les NaN
            chart_data = chart_data.dropna()

        # Construire le résultat
        result = {
            "total_duration_hours": round(total_duration, 2),
            "required_hours": required_hours,
            "criterion_met": criterion_met,
            "power_threshold_kW": round(power_threshold, 2),
            "power_threshold_percent": power_threshold_percent,
            "nominal_power_kW": P_nom,
            "max_power_observed_kW": round(max_power, 2),
            "max_power_timestamp": max_power_timestamp,
            "selected_window_start": selected_window_start,
            "selected_window_end": selected_window_end,
            "chart_data": chart_data,  # Données pour visualisation
        }

        if max_wind_speed is not None:
            result["max_wind_speed_observed_ms"] = round(max_wind_speed, 2)
            result["max_wind_speed_timestamp"] = max_wind_timestamp

        return result
