from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
from src.logger_config import get_logger
import pandas as pd
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineConfig,
    ValidationCriteria,
)
from typing import Dict, Any

logger = get_logger(__name__)


class PitchAnalyzer(BaseAnalyzer):
    """
    Analyseur de l'angle de pitch des 3 pales.

    Le pitch est l'angle des pales par rapport au plan du rotor.
    - Pitch = 0° : Pales perpendiculaires au vent (production maximale)
    - Pitch > 0° : Pales orientées pour réduire la prise au vent (régulation ou arrêt)

    Analyse pour chaque pale individuellement:
    - Distribution du pitch selon la vitesse du vent
    - Identification des modes de fonctionnement (production, régulation, arrêt)
    - Détection d'anomalies (pitch instable, valeurs aberrantes, désynchronisation entre pales)

    Critère typique:
    - Les 3 pales doivent avoir des angles synchronisés (écart < 2°)
    - À vitesse nominale (>10 m/s), pitch doit être stable et proche de 0°
    - Au-delà de cut-out, pitch doit augmenter (régulation/arrêt)
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
        Analyse l'angle de pitch des 3 pales en fonction de la vitesse du vent.

        Args:
            operation_data: Données d'opération (pitch_pale1/2/3, wind_speed, activation_power)
            log_data: Données de logs (non utilisé ici)
            turbine_config: Configuration de la turbine
            criteria: Critères de validation

        Returns:
            Dictionnaire avec:
                - blade1/2/3: Statistiques par pale (mean, std, min, max, mean_production, std_production)
                - mean_pitch_all: Pitch moyen global (moyenne des 3 pales)
                - max_desync: Écart maximum entre pales
                - monthly_pitch: Statistiques mensuelles par pale
                - chart_data: DataFrame pour visualisation (wind_speed, pitch1/2/3, activation_power, month)
        """
        test_start = turbine_config.test_start
        test_end = turbine_config.test_end
        mapping = turbine_config.mapping_operation_data
        timestamp_col = mapping.timestamp

        # Colonnes nécessaires - 3 pales
        pitch_pale1_col = mapping.pitch_pale1
        pitch_pale2_col = mapping.pitch_pale2
        pitch_pale3_col = mapping.pitch_pale3
        wind_speed_col = mapping.wind_speed
        activation_power_col = mapping.activation_power

        # Vérifier que les colonnes nécessaires existent
        if not pitch_pale1_col or not pitch_pale2_col or not pitch_pale3_col:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: pitch_pale1/2/3 columns not configured"
            )
            return {"error": "pitch_pale1/2/3 columns not configured"}

        if not wind_speed_col:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: wind_speed column not configured"
            )
            return {"error": "wind_speed column not configured"}

        missing_cols = []
        for col in [pitch_pale1_col, pitch_pale2_col, pitch_pale3_col]:
            if col not in operation_data.columns:
                missing_cols.append(col)

        if missing_cols:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: pitch columns not found in data: {missing_cols}"
            )
            return {"error": f"pitch columns not found in data: {missing_cols}"}

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
        test_data[pitch_pale1_col] = pd.to_numeric(test_data[pitch_pale1_col], errors="coerce")
        test_data[pitch_pale2_col] = pd.to_numeric(test_data[pitch_pale2_col], errors="coerce")
        test_data[pitch_pale3_col] = pd.to_numeric(test_data[pitch_pale3_col], errors="coerce")
        test_data[wind_speed_col] = pd.to_numeric(test_data[wind_speed_col], errors="coerce")

        # Filtrer les données valides (toutes les pales + wind_speed valides)
        valid_data = test_data[
            test_data[pitch_pale1_col].notna()
            & test_data[pitch_pale2_col].notna()
            & test_data[pitch_pale3_col].notna()
            & test_data[wind_speed_col].notna()
        ].copy()

        if len(valid_data) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No valid data (pitch1/2/3 and wind_speed not null)"
            )
            return {"error": "No valid data (pitch1/2/3 and wind_speed not null)"}

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Analyzing {len(valid_data)} valid measurements"
        )

        # Récupérer cut-in speed depuis critères
        cut_in_speed = 3.0  # m/s (valeur standard)
        if "cut_in_to_cut_out" in criteria.validation_criterion:
            cut_in_speed = criteria.validation_criterion[
                "cut_in_to_cut_out"
            ].specification[0]

        # Ajouter une colonne pour le mois
        valid_data["month"] = pd.to_datetime(valid_data[timestamp_col]).dt.to_period("M")

        # Renommer les colonnes pour uniformité
        valid_data = valid_data.rename(
            columns={
                pitch_pale1_col: "pitch1",
                pitch_pale2_col: "pitch2",
                pitch_pale3_col: "pitch3",
                wind_speed_col: "wind_speed",
                timestamp_col: "timestamp",
            }
        )

        # Calculer la désynchronisation maximale entre pales
        valid_data["pitch_max"] = valid_data[["pitch1", "pitch2", "pitch3"]].max(axis=1)
        valid_data["pitch_min"] = valid_data[["pitch1", "pitch2", "pitch3"]].min(axis=1)
        valid_data["desync"] = valid_data["pitch_max"] - valid_data["pitch_min"]
        max_desync = valid_data["desync"].max()
        mean_desync = valid_data["desync"].mean()

        # Calculer pitch moyen des 3 pales
        valid_data["pitch_mean"] = valid_data[["pitch1", "pitch2", "pitch3"]].mean(axis=1)

        # Données en production (wind_speed > cut_in)
        production_data = valid_data[valid_data["wind_speed"] > cut_in_speed]

        # Fonction pour calculer les statistiques d'une pale
        def compute_blade_stats(blade_col: str) -> Dict[str, Any]:
            stats = {
                "mean_pitch": round(valid_data[blade_col].mean(), 2),
                "std_pitch": round(valid_data[blade_col].std(), 2),
                "min_pitch": round(valid_data[blade_col].min(), 2),
                "max_pitch": round(valid_data[blade_col].max(), 2),
            }

            if len(production_data) > 0:
                stats["mean_pitch_production"] = round(production_data[blade_col].mean(), 2)
                stats["std_pitch_production"] = round(production_data[blade_col].std(), 2)
            else:
                stats["mean_pitch_production"] = 0.0
                stats["std_pitch_production"] = 0.0

            return stats

        # Statistiques par pale
        blade1_stats = compute_blade_stats("pitch1")
        blade2_stats = compute_blade_stats("pitch2")
        blade3_stats = compute_blade_stats("pitch3")

        # Statistiques globales (moyenne des 3 pales)
        mean_pitch_all = round(valid_data["pitch_mean"].mean(), 2)
        std_pitch_all = round(valid_data["pitch_mean"].std(), 2)

        # --- Agrégation mensuelle par pale ---
        monthly_results = []
        for month_period in sorted(valid_data["month"].unique()):
            month_data = valid_data[valid_data["month"] == month_period]

            # Désynchronisation du mois
            max_desync_month = month_data["desync"].max()
            mean_desync_month = month_data["desync"].mean()

            month_dict = {
                "month": str(month_period),
                "blade1": {
                    "mean": round(month_data["pitch1"].mean(), 2),
                    "std": round(month_data["pitch1"].std(), 2),
                },
                "blade2": {
                    "mean": round(month_data["pitch2"].mean(), 2),
                    "std": round(month_data["pitch2"].std(), 2),
                },
                "blade3": {
                    "mean": round(month_data["pitch3"].mean(), 2),
                    "std": round(month_data["pitch3"].std(), 2),
                },
                "mean_pitch_all": round(month_data["pitch_mean"].mean(), 2),
                "max_desync": round(max_desync_month, 2),
                "mean_desync": round(mean_desync_month, 2),
                "num_measurements": len(month_data),
            }

            monthly_results.append(month_dict)

        # Determine status level based on max desync angle
        from src.wind_turbine_analytics.data_processing.status_levels import StatusLevel
        status_level = StatusLevel.from_angle_error(
            max_desync,
            thresholds={"success": 2.0, "minor": 5.0, "warning": 10.0, "major": 20.0}
        )

        logger.debug(
            f"Turbine {turbine_config.turbine_id}: Pitch analysis completed. "
            f"Mean pitch (all blades): {mean_pitch_all:.2f}°, "
            f"Max desync: {max_desync:.2f}°, Mean desync: {mean_desync:.2f}°, "
            f"Status: {str(status_level)}, Months analyzed: {len(monthly_results)}"
        )

        # Préparer chart_data pour visualisation (avec les 3 pales)
        chart_data_columns = ["wind_speed", "pitch1", "pitch2", "pitch3", "pitch_mean", "timestamp"]

        if activation_power_col and activation_power_col in valid_data.columns:
            valid_data = valid_data.rename(columns={activation_power_col: "activation_power"})
            chart_data_columns.append("activation_power")

        chart_data_df = valid_data[chart_data_columns + ["month"]].copy()

        return {
            "blade1": blade1_stats,
            "blade2": blade2_stats,
            "blade3": blade3_stats,
            "mean_pitch_all": mean_pitch_all,
            "std_pitch_all": std_pitch_all,
            "max_desync": round(max_desync, 2),
            "mean_desync": round(mean_desync, 2),
            "status_level": status_level,
            "total_measurements": len(valid_data),
            "monthly_pitch": monthly_results,
            "chart_data": chart_data_df,
        }
