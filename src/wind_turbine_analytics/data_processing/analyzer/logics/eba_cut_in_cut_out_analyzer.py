from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
import pandas as pd
import numpy as np

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
from src.wind_turbine_analytics.data_processing.log_code import (
    CodeCriticality,
    FunctionalSystem,
)

logger = get_logger(__name__)


class EbACutInCutOutAnalyzer(BaseAnalyzer):
    def __init__(self) -> None:
        super().__init__()

    def _compute(
        self,
        operation_data: pd.DataFrame,
        log_data: pd.DataFrame,
        turbine_config: TurbineConfig,
        criteria: ValidationCriteria,
    ) -> Dict[str, Any]:
        # Cette méthode doit retourner un dictionnaire avec les résultats
        # Logics :
        # Production > 0, wind speed between cut-in and cut-out,
        # including all downtimes (curtailments, maintenance, grid issues,

        mapping = turbine_config.mapping_operation_data
        wind_speed_col = mapping.wind_speed
        timestamp_col = mapping.timestamp
        power_col = mapping.activation_power
        P_nom = turbine_config.general_information.nominal_power

        test_start = turbine_config.test_start
        test_end = turbine_config.test_end

        manager = NordexN311LogCodeManager()
        start_date_col = turbine_config.mapping_log_data.start_date
        end_date_col = turbine_config.mapping_log_data.end_date
        oper_col = turbine_config.mapping_log_data.oper

        if P_nom <= 100:
            logger.warning(
                "Nominal power for turbine %s is very low (%s kW)."
                " This may indicate an issue with the configuration. "
                "Defaulting to 1.0 kW for synthetic power curve generation.",
                turbine_config.turbine_id,
                P_nom,
            )
            P_nom = P_nom * 1000  # Default nominal power in kW (ex: 3.78 MW)

        criterion = None
        if criteria.validation_criterion is not None:
            criterion = criteria.validation_criterion.get(
                "cut_in_to_cut_out", Criterion()
            )
        else:
            criterion = Criterion()
        specification = getattr(criterion, "specification", None)
        if (
            specification is None
            or not isinstance(specification, (list, tuple))
            or len(specification) != 2
        ):
            raise ValueError("Invalid specification for cut_in_to_cut_out criterion")
        v_min, v_max = specification
        dt_minutes = 5  # Assuming data is at 5-minute intervals; adjust as needed
        dt_hours = dt_minutes / 60.0

        theorical_power_curve = None
        # TODO : Verifier si la courbe de puissance garantie est disponible, et l'utiliser pour déterminer les points de cut-in et cut-out spécifiques à la turbine.
        if (
            turbine_config.general_information is not None
            and getattr(
                turbine_config.general_information, "path_guaranteed_power_curve", None
            )
            is not None
        ):
            # Charger la courbe de puissance garantie et identifier les points de cut-in et cut-out basés sur un seuil de puissance (ex: 5% de P_nom).
            # TODO : Implémenter la logique de chargement de la courbe de puissance garantie et d'identification des points de cut-in et cut-out.
            logger.debug(
                "Guaranteed power curve provided for turbine %s. "
                "Loading and identifying cut-in and cut-out points.",
                turbine_config.turbine_id,
            )
            pass
        else:
            logger.warning(
                "No guaranteed power curve provided for turbine %s. "
                "Generating synthetic power curve from operation data.",
                turbine_config.turbine_id,
            )
            theorical_power_curve = self.generate_synthetic_power_curve(
                operation_data, turbine_config, criteria
            )
        operation_data[timestamp_col] = pd.to_datetime(
            operation_data[timestamp_col], errors="coerce"
        )
        df = (
            operation_data[[timestamp_col, wind_speed_col, power_col]]
            .where(lambda x: x[timestamp_col].between(test_start, test_end))
            .copy()
            .dropna(subset=[wind_speed_col, power_col])
        )

        if not pd.api.types.is_float_dtype(df[wind_speed_col]):
            logger.warning(
                f"Wind speed column '{wind_speed_col}' is not numeric, "
                f"cannot compute cut-in/cut-out analysis for turbine {turbine_config.turbine_id}"
            )
            df[wind_speed_col] = pd.to_numeric(df[wind_speed_col], errors="coerce")
        if not pd.api.types.is_float_dtype(df[power_col]):
            logger.warning(
                f"Power column '{power_col}' is not numeric, "
                f"cannot compute cut-in/cut-out analysis for turbine {turbine_config.turbine_id}"
            )
            df[power_col] = pd.to_numeric(df[power_col], errors="coerce")

        mask_operating = manager.create_time_mask(
            log_df=log_data,
            target_df=df,
            code_column=oper_col,
            log_start_col=start_date_col,
            log_end_col=end_date_col,
            target_timestamp_col=timestamp_col,
            criticality_filter=[CodeCriticality.MEDIUM, CodeCriticality.HIGH],
        )
        df = df[mask_operating].copy()

        df["theorical_power"] = theorical_power_curve(df[wind_speed_col])
        df["fixed_power"] = np.minimum(df[power_col], P_nom)

        mask_operaing = df[wind_speed_col].between(v_min, v_max, inclusive="both") & (
            df[power_col] > 0.01 * P_nom
        )
        df = df[mask_operaing].copy()

        df["real_energy"] = df["fixed_power"] * dt_hours
        df["theorical_energy"] = df["theorical_power"] * dt_hours
        df["loss_energy"] = np.maximum(0, df["theorical_energy"] - df["real_energy"])

        E_real = df["real_energy"].sum()
        E_theorical = df["theorical_energy"].sum()

        logger.debug(
            "Turbine %s: Total real energy = %.2f kWh, Total theoretical energy = %.2f kWh",
            turbine_config.turbine_id,
            E_real,
            E_theorical,
        )
        df["month"] = df[timestamp_col].dt.to_period("M")
        eba_monthly = (
            df.groupby("month")
            .agg(
                E_real_monthly=("real_energy", "sum"),
                E_theorical_monthly=("theorical_energy", "sum"),
                Loss_energy_monthly=("loss_energy", "sum"),
            )
            .reset_index()
        )
        eba_monthly["performance"] = (
            100.0 * eba_monthly["E_real_monthly"] / eba_monthly["E_theorical_monthly"]
        ).fillna(0.0)
        logger.debug(
            "Turbine %s: Monthly performance:\n%s",
            turbine_config.turbine_id,
            eba_monthly[["month", "performance"]].to_string(index=False),
        )

        # Calculate mean availability for status
        monthly_performances = eba_monthly["performance"].tolist()
        valid_perfs = [p for p in monthly_performances if p > 0]
        mean_availability = sum(valid_perfs) / len(valid_perfs) if valid_perfs else 0.0

        # Determine status level
        from src.wind_turbine_analytics.data_processing.status_levels import StatusLevel
        status_level = StatusLevel.from_percentage(mean_availability)

        logger.debug(
            "Turbine %s: Mean availability = %.2f%%, Status = %s",
            turbine_config.turbine_id,
            mean_availability,
            str(status_level),
        )

        return {
            "total_real_energy": E_real,
            "total_theoretical_energy": E_theorical,
            "total_loss_energy": E_theorical - E_real,
            "performance": 100.0 * E_real / E_theorical if E_theorical > 0 else 0.0,
            "monthly_performance": eba_monthly[["month", "performance"]].to_dict(
                orient="records"
            ),
            "mean_availability_pct": round(mean_availability, 2),
            "status_level": status_level,
        }
