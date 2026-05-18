"""Time-Based Availability (TBA) Manufacturer Analyzer."""

from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
import pandas as pd
from typing import Dict, Any
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineConfig,
    ValidationCriteria,
    Criterion,
)
from src.logger_config import get_logger
from src.wind_turbine_analytics.data_processing.log_code.generator_type.nordex_n311_log_code_manager import (
    NordexN311LogCodeManager,
)
from src.wind_turbine_analytics.data_processing.status_levels import (
    StatusLevel,
)

logger = get_logger(__name__)


class TbaManufacturerAnalyzer(BaseAnalyzer):
    """
    Analyseur de disponibilité temporelle (Time-Based Availability) Manufacturer.

    Calcule le pourcentage de TEMPS où l'éolienne est disponible, en EXCLUANT les arrêts
    considérés comme "disponibilité propriétaire" :
    - Intervention manuelle du propriétaire (FM7 - Customer Stop)
    - Demande de l'agrégateur / curtailment
    - Givrage / Icing conditions

    Une éolienne est considérée comme disponible lorsque :
    - La vitesse du vent est entre cut-in et cut-out
    - La production est > 0 kW
    - OU l'arrêt est dû à une intervention propriétaire/curtailment/givrage

    Formule:
    TBA Manufacturer = (Temps disponible + Temps arrêts exclus) / Temps total dans plage vent × 100%

    Différence avec TbACutInCutOut:
    - TbACutInCutOut : AUCUN filtrage (tous les arrêts comptent comme indisponibles)
    - TbaManufacturer : EXCLUT certains arrêts (propriétaire, curtailment, givrage)
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
        Calcule la disponibilité temporelle mensuelle avec exclusion de certains codes.

        Args:
            operation_data: Données SCADA avec wind_speed, activation_power
            log_data: Données de logs pour identifier les arrêts à exclure
            turbine_config: Configuration de la turbine
            criteria: Critères de validation (cut_in_to_cut_out specification)

        Returns:
            Dict avec:
                - total_points_in_range: Nombre total de points dans plage vent
                - available_points: Nombre de points avec production > 0
                - excluded_points: Nombre de points avec arrêts exclus
                - unavailable_points: Nombre de points réellement indisponibles
                - availability_pct: Disponibilité Manufacturer en %
                - monthly_availability: Liste des disponibilités mensuelles
                - mean_availability_pct: Moyenne des disponibilités mensuelles
                - status_level: Niveau de statut (SUCCESS, WARNING, etc.)
        """
        # Extract mapping and configuration
        mapping = turbine_config.mapping_operation_data
        wind_speed_col = mapping.wind_speed
        timestamp_col = mapping.timestamp
        power_col = mapping.activation_power

        test_start = turbine_config.test_start
        test_end = turbine_config.test_end

        # Get cut-in and cut-out values from criteria
        criterion = criteria.validation_criterion.get("cut_in_to_cut_out", Criterion())
        specification = getattr(criterion, "specification", None)

        if (
            specification is None
            or not isinstance(specification, (list, tuple))
            or len(specification) != 2
        ):
            logger.error(
                f"Turbine {turbine_config.turbine_id}: Invalid specification for cut_in_to_cut_out"
            )
            return {"error": "Invalid specification for cut_in_to_cut_out criterion"}

        v_min, v_max = specification

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: TBA Manufacturer analysis with cut-in={v_min} m/s, cut-out={v_max} m/s"
        )

        # Initialize log code manager
        manager = NordexN311LogCodeManager()
        start_date_col = turbine_config.mapping_log_data.start_date
        end_date_col = turbine_config.mapping_log_data.end_date
        oper_col = turbine_config.mapping_log_data.oper

        # Get owner availability codes from manager (extensible to other manufacturers)
        owner_codes_dict = manager.get_owner_availability_codes()

        # Flatten all categories into a single list of code strings
        excluded_codes = [
            code.code
            for category_codes in owner_codes_dict.values()
            for code in category_codes
        ]

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Excluding {len(excluded_codes)} codes from unavailability:\n"
            f"  - Owner intervention: {len(owner_codes_dict['owner_intervention'])} codes\n"
            f"  - Curtailment: {len(owner_codes_dict['curtailment'])} codes\n"
            f"  - Icing: {len(owner_codes_dict['icing'])} codes"
        )

        # Convert timestamp column to datetime
        operation_data[timestamp_col] = pd.to_datetime(
            operation_data[timestamp_col], errors="coerce"
        )

        # Filter by test period
        df = operation_data[
            (operation_data[timestamp_col] >= test_start)
            & (operation_data[timestamp_col] <= test_end)
        ].copy()

        if len(df) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No data in test period"
            )
            return {"error": "No data in test period"}

        # Convert columns to numeric
        df[wind_speed_col] = pd.to_numeric(df[wind_speed_col], errors="coerce")
        df[power_col] = pd.to_numeric(df[power_col], errors="coerce")

        # Drop rows with missing wind_speed or power
        df = df.dropna(subset=[wind_speed_col, power_col])

        if len(df) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No valid data after removing NaN"
            )
            return {"error": "No valid data after removing NaN"}

        # Filter points within cut-in to cut-out range
        df_in_range = df[
            df[wind_speed_col].between(v_min, v_max, inclusive="both")
        ].copy()

        if len(df_in_range) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No data points in wind speed range [{v_min}, {v_max}] m/s"
            )
            return {
                "error": f"No data points in wind speed range [{v_min}, {v_max}] m/s"
            }

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: {len(df_in_range)} points in wind speed range"
        )

        # Create mask for periods with excluded codes (owner availability)
        # These periods will be considered as "available" even if power = 0
        mask_excluded = manager.create_time_mask(
            log_df=log_data,
            target_df=df_in_range,
            code_column=oper_col,
            log_start_col=start_date_col,
            log_end_col=end_date_col,
            target_timestamp_col=timestamp_col,
            codes_to_filter=excluded_codes,
        )

        # Invert mask: True where excluded codes are present
        mask_excluded_periods = ~mask_excluded

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: {mask_excluded_periods.sum()} points "
            f"with excluded codes (owner availability)"
        )

        # Classify points:
        # - available: power > 0
        # - excluded: power = 0 BUT during excluded code periods
        # - unavailable: power = 0 AND NOT during excluded code periods
        df_in_range["power_available"] = df_in_range[power_col] > 0
        df_in_range["excluded_period"] = mask_excluded_periods
        df_in_range["available"] = (
            df_in_range["power_available"] | df_in_range["excluded_period"]
        )

        # Add month column for monthly aggregation
        df_in_range["month"] = df_in_range[timestamp_col].dt.to_period("M")

        # Calculate monthly availability
        monthly_stats = (
            df_in_range.groupby("month")
            .agg(
                total_points=("available", "count"),
                available_points=("available", "sum"),
                excluded_points=("excluded_period", "sum"),
                power_available_points=("power_available", "sum"),
            )
            .reset_index()
        )

        monthly_stats["unavailable_points"] = (
            monthly_stats["total_points"] - monthly_stats["available_points"]
        )
        monthly_stats["availability_pct"] = (
            100.0 * monthly_stats["available_points"] / monthly_stats["total_points"]
        ).fillna(0.0)

        # Convert month to string for serialization
        monthly_stats["month"] = monthly_stats["month"].astype(str)

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Monthly TBA Manufacturer:\n"
            f"{monthly_stats[['month', 'availability_pct']].to_string(index=False)}"
        )

        # Global statistics
        total_points_in_range = len(df_in_range)
        available_points = df_in_range["available"].sum()
        excluded_points = df_in_range["excluded_period"].sum()
        power_available_points = df_in_range["power_available"].sum()
        unavailable_points = total_points_in_range - available_points
        availability_pct = (
            100.0 * available_points / total_points_in_range
            if total_points_in_range > 0
            else 0.0
        )

        # Calculate mean availability for status
        monthly_availabilities = monthly_stats["availability_pct"].tolist()
        mean_availability = (
            sum(monthly_availabilities) / len(monthly_availabilities)
            if monthly_availabilities
            else 0.0
        )

        status_level = StatusLevel.from_percentage(mean_availability)

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: TBA Manufacturer analysis completed. "
            f"Global availability: {availability_pct:.2f}%, "
            f"Points breakdown: "
            f"power>0={power_available_points}, excluded={excluded_points}, unavailable={unavailable_points}, "
            f"Mean monthly availability: {mean_availability:.2f}%, "
            f"Status: {str(status_level)}"
        )

        return {
            "total_points_in_range": int(total_points_in_range),
            "available_points": int(available_points),
            "power_available_points": int(power_available_points),
            "excluded_points": int(excluded_points),
            "unavailable_points": int(unavailable_points),
            "availability_pct": round(availability_pct, 2),
            "monthly_availability": monthly_stats[
                [
                    "month",
                    "total_points",
                    "available_points",
                    "power_available_points",
                    "excluded_points",
                    "unavailable_points",
                    "availability_pct",
                ]
            ].to_dict(orient="records"),
            "mean_availability_pct": round(mean_availability, 2),
            "status_level": status_level,
        }
