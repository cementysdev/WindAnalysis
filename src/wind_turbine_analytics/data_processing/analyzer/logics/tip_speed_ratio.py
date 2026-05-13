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

# Mapping des modèles de turbines avec leur rayon de rotor (en mètres)
TURBINE_ROTOR_RADIUS = {
    "N131": 65.5,  # Nordex N131 - Diamètre 131m
    "N117": 58.5,  # Nordex N117 - Diamètre 117m
    "V117": 58.5,  # Vestas V117 - Diamètre 117m
    "V126": 63.0,  # Vestas V126 - Diamètre 126m
    "V136": 68.0,  # Vestas V136 - Diamètre 136m
    "SWT130": 65.0,  # Siemens SWT-3.0-130 - Diamètre 130m
}


class TipSpeedRatioAnalyzer(BaseAnalyzer):
    """
    Analyseur du Tip Speed Ratio (TSR).

    Le TSR est le ratio entre la vitesse linéaire du bout de la pale et la vitesse du vent.
    Formule: TSR = (ω × R) / V
    où:
        ω = vitesse de rotation (rad/s) = (RPM × 2π) / 60
        R = rayon du rotor (m)
        V = vitesse du vent (m/s)

    Critère: TSR optimal entre 7 et 9 pour les turbines modernes.
    - TSR < 7 : turbine "paresseuse" (sous-performante)
    - TSR > 9 : perte d'efficacité aérodynamique
    """

    def __init__(self):
        super().__init__()

    def _compute(
        self,
        operation_data: pd.DataFrame,
        log_data: pd.DataFrame,
        turbine_config: TurbineConfig,
        criteria: ValidationCriteria,
    ) -> Dict[str, Any]:
        """
        Calcule le Tip Speed Ratio pour une turbine.

        Args:
            operation_data: Données d'opération (doit contenir rpm, wind_speed, activation_power)
            log_data: Données de logs (non utilisé ici)
            turbine_config: Configuration de la turbine
            criteria: Critères de validation (tsr_optimal avec specification [min, max])

        Returns:
            Dictionnaire avec:
                - mean_tsr: TSR moyen
                - std_tsr: Écart-type du TSR
                - min_tsr: TSR minimum
                - max_tsr: TSR maximum
                - optimal_range: Plage optimale [min, max]
                - criterion_met: True si TSR moyen dans la plage optimale
                - percentage_in_range: % de mesures dans la plage optimale
                - chart_data: DataFrame pour visualisation (rpm, wind_speed, activation_power, tsr)
        """
        test_start = turbine_config.test_start
        test_end = turbine_config.test_end
        mapping = turbine_config.mapping_operation_data
        timestamp_col = mapping.timestamp

        # Colonnes nécessaires
        rpm_col = mapping.rpm
        wind_speed_col = mapping.wind_speed
        activation_power_col = mapping.activation_power

        # Vérifier que les colonnes nécessaires existent
        if not rpm_col:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: rpm column not configured"
            )
            return {"error": "rpm column not configured"}

        if not wind_speed_col:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: wind_speed column not configured"
            )
            return {"error": "wind_speed column not configured"}

        if rpm_col not in operation_data.columns:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: rpm column '{rpm_col}' not found in data"
            )
            return {"error": f"rpm column '{rpm_col}' not found in data"}

        # Obtenir le rayon du rotor
        turbine_model = (
            turbine_config.general_information.model
            if turbine_config.general_information
            else None
        )
        rotor_radius = TURBINE_ROTOR_RADIUS.get(turbine_model)

        if rotor_radius is None:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: Unknown turbine model '{turbine_model}'. "
                f"Supported models: {list(TURBINE_ROTOR_RADIUS.keys())}"
            )
            return {
                "error": f"Unknown turbine model '{turbine_model}'",
                "supported_models": list(TURBINE_ROTOR_RADIUS.keys()),
            }

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Using rotor radius {rotor_radius}m for model {turbine_model}"
        )

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

        # Convertir les colonnes en numeric
        test_data[rpm_col] = pd.to_numeric(test_data[rpm_col], errors="coerce")
        test_data[wind_speed_col] = pd.to_numeric(
            test_data[wind_speed_col], errors="coerce"
        )

        # Filtrer les données valides (rpm > 0, wind_speed > cut-in)
        cut_in_speed = 3.0  # m/s (valeur standard)
        if "cut_in_to_cut_out" in criteria.validation_criterion:
            cut_in_speed = criteria.validation_criterion[
                "cut_in_to_cut_out"
            ].specification[0]

        valid_data = test_data[
            (test_data[rpm_col] > 0) & (test_data[wind_speed_col] > cut_in_speed)
        ].copy()

        if len(valid_data) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No valid data (rpm > 0 and wind_speed > {cut_in_speed} m/s)"
            )
            return {
                "error": f"No valid data (rpm > 0 and wind_speed > {cut_in_speed} m/s)"
            }

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Analyzing {len(valid_data)} valid measurements"
        )

        # Calcul du TSR
        # ω (rad/s) = (RPM × 2π) / 60
        omega = (valid_data[rpm_col] * 2 * np.pi) / 60

        # TSR = (ω × R) / V
        valid_data["tsr"] = (omega * rotor_radius) / valid_data[wind_speed_col]

        # Ajouter une colonne pour le mois
        valid_data["month"] = pd.to_datetime(valid_data[timestamp_col]).dt.to_period(
            "M"
        )

        # Plage optimale (critère ou défaut 7-9)
        optimal_range = [7.0, 9.0]
        if "tsr_optimal" in criteria.validation_criterion:
            optimal_range = criteria.validation_criterion["tsr_optimal"].specification

        # --- Agrégation mensuelle ---
        monthly_results = []
        for month_period in sorted(valid_data["month"].unique()):
            month_data = valid_data[valid_data["month"] == month_period]

            mean_tsr_month = month_data["tsr"].mean()
            std_tsr_month = month_data["tsr"].std()
            min_tsr_month = month_data["tsr"].min()
            max_tsr_month = month_data["tsr"].max()

            # Pourcentage dans la plage optimale pour ce mois
            in_range_month = month_data[
                (month_data["tsr"] >= optimal_range[0])
                & (month_data["tsr"] <= optimal_range[1])
            ]
            percentage_in_range_month = (len(in_range_month) / len(month_data)) * 100

            monthly_results.append(
                {
                    "month": str(month_period),  # Format YYYY-MM
                    "mean_tsr": round(mean_tsr_month, 2),
                    "std_tsr": round(std_tsr_month, 2),
                    "min_tsr": round(min_tsr_month, 2),
                    "max_tsr": round(max_tsr_month, 2),
                    "percentage_in_range": round(percentage_in_range_month, 1),
                    "num_measurements": len(month_data),
                }
            )

        # Statistiques globales
        mean_tsr = valid_data["tsr"].mean()
        std_tsr = valid_data["tsr"].std()
        min_tsr = valid_data["tsr"].min()
        max_tsr = valid_data["tsr"].max()

        # Pourcentage global dans la plage optimale
        in_range = valid_data[
            (valid_data["tsr"] >= optimal_range[0])
            & (valid_data["tsr"] <= optimal_range[1])
        ]
        percentage_in_range = (len(in_range) / len(valid_data)) * 100

        # Critère satisfait si le TSR moyen global est dans la plage
        criterion_met = optimal_range[0] <= mean_tsr <= optimal_range[1]

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: TSR analysis completed. "
            f"Mean TSR: {mean_tsr:.2f}, Optimal range: {optimal_range}, "
            f"Criterion met: {criterion_met}, In range: {percentage_in_range:.1f}%, "
            f"Months analyzed: {len(monthly_results)}"
        )

        # Préparer chart_data pour visualisation RPM (avec mois)
        chart_data_columns = [rpm_col, wind_speed_col, timestamp_col]
        chart_data_names = ["rpm", "wind_speed", "timestamp"]

        if activation_power_col and activation_power_col in valid_data.columns:
            chart_data_columns.append(activation_power_col)
            chart_data_names.append("activation_power")

        chart_data_df = valid_data[chart_data_columns + ["tsr", "month"]].copy()
        chart_data_df.columns = chart_data_names + ["tsr", "month"]

        return {
            "mean_tsr": round(mean_tsr, 2),
            "std_tsr": round(std_tsr, 2),
            "min_tsr": round(min_tsr, 2),
            "max_tsr": round(max_tsr, 2),
            "optimal_range": optimal_range,
            "criterion_met": criterion_met,
            "percentage_in_range": round(percentage_in_range, 1),
            "total_measurements": len(valid_data),
            "monthly_tsr": monthly_results,  # Ajout des résultats mensuels
            "chart_data": chart_data_df,
        }
