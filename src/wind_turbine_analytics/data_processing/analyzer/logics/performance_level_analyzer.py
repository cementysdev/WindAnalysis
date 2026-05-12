from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
from src.logger_config import get_logger
import pandas as pd
import numpy as np
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineConfig,
    ValidationCriteria,
)
from typing import Dict, Any
from src.wind_turbine_analytics.data_processing.classifier.classifier import (
    Regime_Classification,
)

logger = get_logger(__name__)


class PerformanceLevelAnalyzer(BaseAnalyzer):
    """
    Analyseur des niveaux de performance basé sur la classification des régimes de fonctionnement.

    Utilise le classificateur Regime_Classification pour identifier les zones opérationnelles:
    - Zone 0: Outliers (données aberrantes)
    - Zone 1: Arrêt (vitesse de vent faible, < cut-in)
    - Zone 2: Démarrage (montée en puissance)
    - Zone 3: Rotation max mais puissance partielle
    - Zone 4: Puissance max (production nominale)
    - Zone 5: Arrêt (vitesse de vent élevée, > cut-out)
    - Zone 6: Données hors modèle (résidus élevés)

    L'analyse calibre automatiquement les modèles de rotation et puissance en fonction
    de la vitesse du vent, puis classifie chaque point de mesure.
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
        Analyse les niveaux de performance en classifiant les régimes de fonctionnement.

        Args:
            operation_data: Données d'opération (wind_speed, rpm, activation_power, pitch)
            log_data: Données de logs (non utilisé ici)
            turbine_config: Configuration de la turbine
            criteria: Critères de validation

        Returns:
            Dictionnaire avec:
                - clusters: Classification de chaque point (zones 0-6)
                - X_threshold: Seuils de vitesse de vent [X0, X1, X2, X3]
                - theta_rot: Paramètres du modèle de rotation
                - theta_pwer: Paramètres du modèle de puissance
                - zone_distribution: Pourcentage de points par zone
                - chart_data: DataFrame pour visualisation (wind_speed, rpm, power, pitch, cluster)
        """
        test_start = turbine_config.test_start
        test_end = turbine_config.test_end
        mapping = turbine_config.mapping_operation_data
        timestamp_col = mapping.timestamp

        # Colonnes nécessaires
        wind_speed_col = mapping.wind_speed
        rpm_col = mapping.rpm
        activation_power_col = mapping.activation_power
        pitch_col = mapping.pitch_pale1  # Utiliser la première pale pour le pitch

        # Vérifier que les colonnes nécessaires existent
        missing_cols = []
        for name, col in [
            ("wind_speed", wind_speed_col),
            ("rpm", rpm_col),
            ("activation_power", activation_power_col),
            ("pitch", pitch_col),
        ]:
            if not col:
                missing_cols.append(name)
            elif col not in operation_data.columns:
                missing_cols.append(f"{name} ('{col}')")

        if missing_cols:
            error_msg = f"Missing columns: {', '.join(missing_cols)}"
            logger.error(f"Turbine {turbine_config.turbine_id}: {error_msg}")
            return {"error": error_msg}

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
        test_data[wind_speed_col] = pd.to_numeric(
            test_data[wind_speed_col], errors="coerce"
        )
        test_data[rpm_col] = pd.to_numeric(test_data[rpm_col], errors="coerce")
        test_data[activation_power_col] = pd.to_numeric(
            test_data[activation_power_col], errors="coerce"
        )
        test_data[pitch_col] = pd.to_numeric(test_data[pitch_col], errors="coerce")

        # Filtrer les données valides
        valid_data = test_data[
            test_data[wind_speed_col].notna()
            & test_data[rpm_col].notna()
            & test_data[activation_power_col].notna()
            & test_data[pitch_col].notna()
        ].copy()

        if len(valid_data) == 0:
            logger.warning(
                f"Turbine {turbine_config.turbine_id}: No valid data (all columns not null)"
            )
            return {"error": "No valid data (all columns not null)"}

        logger.info(
            f"Turbine {turbine_config.turbine_id}: Analyzing {len(valid_data)} valid measurements"
        )

        # Extraire les données
        wind_speed = valid_data[wind_speed_col].values
        rpm = valid_data[rpm_col].values
        power = valid_data[activation_power_col].values
        pitch = valid_data[pitch_col].values

        # Normalisation Min-Max pour le classificateur
        wind_speed_norm = (wind_speed - wind_speed.min()) / (
            wind_speed.max() - wind_speed.min() + 1e-8
        )
        rpm_norm = (rpm - rpm.min()) / (rpm.max() - rpm.min() + 1e-8)
        power_norm = (power - power.min()) / (power.max() - power.min() + 1e-8)
        pitch_norm = (pitch - pitch.min()) / (pitch.max() - pitch.min() + 1e-8)

        # Créer et calibrer le classificateur
        classifier = Regime_Classification(
            id=turbine_config.turbine_id, y_threshold=1.0, dr=0.1, class_both=True
        )

        try:
            # Calibration automatique des modèles
            classifier.fit(wind_speed_norm, rpm_norm, power_norm)

            # Classification des points
            clusters = classifier.classify(wind_speed_norm, rpm_norm, power_norm)

            # Extraire les paramètres
            X_threshold = classifier.X_threshold
            theta_rot = classifier.theta_rot
            theta_pwer = classifier.theta_pwer

            # Distribution par zone
            unique, counts = np.unique(clusters, return_counts=True)
            zone_distribution = {
                f"zone_{int(zone)}": round((count / len(clusters)) * 100, 2)
                for zone, count in zip(unique, counts)
            }

            logger.info(
                f"Turbine {turbine_config.turbine_id}: Performance level analysis completed. "
                f"Thresholds: {[round(x, 2) for x in X_threshold]}, "
                f"Distribution: {zone_distribution}"
            )

            # Préparer chart_data pour visualisation
            valid_data["wind_speed"] = wind_speed
            valid_data["rpm"] = rpm
            valid_data["power"] = power
            valid_data["pitch"] = pitch
            valid_data["wind_speed_norm"] = wind_speed_norm
            valid_data["rpm_norm"] = rpm_norm
            valid_data["power_norm"] = power_norm
            valid_data["pitch_norm"] = pitch_norm
            valid_data["cluster"] = clusters

            chart_data_df = valid_data[
                [
                    "wind_speed",
                    "rpm",
                    "power",
                    "pitch",
                    "wind_speed_norm",
                    "rpm_norm",
                    "power_norm",
                    "pitch_norm",
                    "cluster",
                ]
            ].copy()

            return {
                "clusters": clusters.tolist(),
                "X_threshold": [float(x) for x in X_threshold],
                "theta_rot": [float(x) for x in theta_rot],
                "theta_pwer": [float(x) for x in theta_pwer],
                "zone_distribution": zone_distribution,
                "total_measurements": len(valid_data),
                "normalization": {
                    "wind_speed_min": float(wind_speed.min()),
                    "wind_speed_max": float(wind_speed.max()),
                    "rpm_min": float(rpm.min()),
                    "rpm_max": float(rpm.max()),
                    "power_min": float(power.min()),
                    "power_max": float(power.max()),
                    "pitch_min": float(pitch.min()),
                    "pitch_max": float(pitch.max()),
                },
                "chart_data": chart_data_df,
            }

        except Exception as e:
            logger.error(
                f"Turbine {turbine_config.turbine_id}: Classification failed: {str(e)}"
            )
            return {"error": f"Classification failed: {str(e)}"}
