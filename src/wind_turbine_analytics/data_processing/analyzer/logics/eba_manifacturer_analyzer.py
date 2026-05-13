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

logger = get_logger(__name__)


class EbaManufacturerAnalyzer(BaseAnalyzer):
    """
    Analyse EBA (Energy-Based Availability) sans filtrage des codes d'erreur.

    Contrairement à EbACutInCutOutAnalyzer qui filtre les périodes d'erreur,
    cette classe calcule la performance en incluant TOUTES les périodes,
    y compris les downtimes (arrêts, maintenance, problèmes réseau, etc.).
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
        Calcule l'EBA sans filtrage des codes d'erreur.

        Logique:
        - Production > 0
        - Vitesse de vent entre cut-in et cut-out
        - INCLUT tous les downtimes (curtailments, maintenance, problèmes réseau, etc.)
        """
        logger.debug(
            "Starting EBA analysis for turbine %s (Manufacturer EBA) without error code filtering.",
            turbine_config.turbine_id,
        )
        logger.debug("=" * 80)
        mapping = turbine_config.mapping_operation_data
        wind_speed_col = mapping.wind_speed
        timestamp_col = mapping.timestamp
        power_col = mapping.activation_power
        P_nom = turbine_config.general_information.nominal_power
        test_start = turbine_config.test_start
        test_end = turbine_config.test_end

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
        dt_minutes = 10
        dt_hours = dt_minutes / 60.0

        theorical_power_curve = None
        if (
            turbine_config.general_information is not None
            and getattr(
                turbine_config.general_information, "path_guaranteed_power_curve", None
            )
            is not None
        ):
            logger.debug(
                "Guaranteed power curve provided for turbine %s. "
                "Loading and identifying cut-in and cut-out points.",
                turbine_config.turbine_id,
            )
            # TODO: Implémenter le chargement de la courbe garantie
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

        # Préparer les données
        operation_data[timestamp_col] = pd.to_datetime(
            operation_data[timestamp_col], errors="coerce"
        )
        df = (
            operation_data[[timestamp_col, wind_speed_col, power_col]]
            .where(lambda x: x[timestamp_col].between(test_start, test_end))
            .copy()
            .dropna(subset=[wind_speed_col, power_col])
        )

        # PAS DE FILTRAGE DES CODES D'ERREUR ICI
        # C'est la différence principale avec EbACutInCutOutAnalyzer

        # DIFFÉRENCE CLÉ : On filtre SEULEMENT sur la vitesse de vent,
        # PAS sur la production. Cela permet d'inclure les périodes où la turbine
        # ne produit pas (downtime, maintenance, pannes) dans le calcul de l'EBA.
        # L'énergie théorique sera calculée même si production = 0.

        df["theorical_power"] = theorical_power_curve(df[wind_speed_col])
        df["fixed_power"] = np.minimum(df[power_col], P_nom)

        # Filtrer UNIQUEMENT sur la plage de vitesse (PAS sur la production)
        # Cela inclut les périodes de downtime où power ≈ 0 mais vent dans la plage
        mask_wind_range = df[wind_speed_col].between(v_min, v_max, inclusive="both")
        df = df[mask_wind_range].copy()

        logger.debug(
            "Turbine %s (Manufacturer EBA): Including ALL periods with wind in range [%.1f, %.1f] m/s, "
            "even with low/zero production (downtimes included)",
            turbine_config.turbine_id,
            v_min,
            v_max,
        )

        # Calcul des énergies (énergie réelle peut être 0 pendant downtimes)
        df["real_energy"] = df["fixed_power"] * dt_hours
        df["theorical_energy"] = df["theorical_power"] * dt_hours
        df["loss_energy"] = np.maximum(0, df["theorical_energy"] - df["real_energy"])

        # Statistiques sur les périodes de faible production (probables downtimes)
        downtime_mask = df[power_col] <= 0.01 * P_nom
        downtime_periods = downtime_mask.sum()
        total_periods = len(df)
        downtime_percent = (downtime_periods / total_periods * 100) if total_periods > 0 else 0

        logger.debug(
            "Turbine %s (Manufacturer EBA): %d/%d periods (%.2f%%) with production <= 1%% of P_nom (likely downtimes)",
            turbine_config.turbine_id,
            downtime_periods,
            total_periods,
            downtime_percent,
        )

        E_real = df["real_energy"].sum()
        E_theorical = df["theorical_energy"].sum()

        logger.debug(
            "Turbine %s (Manufacturer EBA): Total real energy = %.2f kWh, "
            "Total theoretical energy = %.2f kWh",
            turbine_config.turbine_id,
            E_real,
            E_theorical,
        )

        # Calcul par mois
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
            "Turbine %s (Manufacturer EBA): Monthly performance:\n%s",
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
            "Turbine %s (Manufacturer EBA): Mean availability = %.2f%%, Status = %s",
            turbine_config.turbine_id,
            mean_availability,
            str(status_level),
        )
        logger.debug(
            "Completed EBA analysis for turbine %s (Manufacturer EBA) without error code filtering.",
            turbine_config.turbine_id,
        )
        logger.debug("-" * 80)
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
