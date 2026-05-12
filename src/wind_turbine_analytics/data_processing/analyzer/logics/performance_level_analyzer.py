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

        # Récupérer les valeurs de cut-in et cut-out depuis validation_criteria
        cut_in_speed = 3.0  # m/s (valeur par défaut)
        cut_out_speed = 25.0  # m/s (valeur par défaut)

        if "cut_in_to_cut_out" in criteria.validation_criterion:
            spec = criteria.validation_criterion["cut_in_to_cut_out"].specification
            if spec and isinstance(spec, (list, tuple)) and len(spec) >= 2:
                cut_in_speed = float(spec[0])
                cut_out_speed = float(spec[1])
                logger.info(
                    f"Turbine {turbine_config.turbine_id}: Using cut-in={cut_in_speed} m/s, "
                    f"cut-out={cut_out_speed} m/s from config"
                )

        # Valeurs typiques des seuils en m/s réel pour définir les zones
        # X0 = cut-in (démarrage turbine)
        # X1 = fin de montée en rotation (typiquement cut-in + 2-3 m/s)
        # X2 = début puissance nominale (typiquement 10-12 m/s ou v_rated)
        # X3 = cut-out (arrêt sécurité)
        X0_real = cut_in_speed
        X1_real = min(cut_in_speed + 3.0, cut_out_speed * 0.3)  # ~5-6 m/s
        X2_real = min(cut_in_speed + 8.0, cut_out_speed * 0.5)  # ~10-12 m/s
        X3_real = cut_out_speed

        # Normalisation Min-Max UNIQUEMENT pour rpm, power, pitch (PAS le vent!)
        # Le vent reste en valeurs réelles (m/s)
        rpm_norm = (rpm - rpm.min()) / (rpm.max() - rpm.min() + 1e-8)
        power_norm = (power - power.min()) / (power.max() - power.min() + 1e-8)
        pitch_norm = (pitch - pitch.min()) / (pitch.max() - pitch.min() + 1e-8)

        # Construire les bounds adaptés pour la calibration (en m/s réel)
        # Bounds pour le modèle de rotation (4 paramètres : a, X0, X1, X3)
        x0_rot = (0.05, X0_real, X1_real, X3_real)
        bounds_rot = (
            (0.0, X0_real * 0.7, X1_real * 0.7, X3_real * 0.8),  # Lower bounds
            (1.0, X0_real * 1.3, X1_real * 1.3, X3_real * 1.2),  # Upper bounds
        )

        # Bounds pour le modèle de puissance (4 paramètres : a, b, X0, X3)
        x0_pwer = (1.0, 5.0, X0_real, X3_real)
        bounds_pwer = (
            (-np.inf, 0, X0_real * 0.7, X3_real * 0.8),  # Lower bounds
            (np.inf, np.inf, X1_real * 1.3, X3_real * 1.2),  # Upper bounds
        )

        logger.info(
            f"Turbine {turbine_config.turbine_id}: Wind thresholds (real values) - "
            f"X0={X0_real:.1f}m/s, X1={X1_real:.1f}m/s, "
            f"X2={X2_real:.1f}m/s, X3={X3_real:.1f}m/s"
        )

        # Créer et calibrer le classificateur
        # y_threshold=0.98 : plateau du modèle à 98% (au lieu de 100%)
        # dr=0.1 : seuil de résidu (10% de tolérance)
        # class_both=True : classification basée sur rotation ET puissance
        classifier = Regime_Classification(dr=0.1, class_both=True, y_threshold=0.98)

        try:
            # Calibration automatique des modèles avec bounds adaptés
            logger.info(
                f"Turbine {turbine_config.turbine_id}: Starting calibration with "
                f"{len(wind_speed)} points..."
            )

            classifier.fit(
                wind_speed,  # Vent en valeurs réelles (m/s)
                rpm_norm,
                power_norm,
                bounds_pwer=bounds_pwer,
                x0_pwer=x0_pwer,
                bounds_rot=bounds_rot,
                x0_rot=x0_rot,
                loss="huber",  # Robust loss pour gérer les outliers
            )

            # Extraire les paramètres après calibration
            X_threshold = classifier.X_threshold
            theta_rot = classifier.theta_rot
            theta_pwer = classifier.theta_pwer

            logger.info(
                f"Turbine {turbine_config.turbine_id}: Calibration completed. "
                f"X_threshold: {[round(x, 3) for x in X_threshold]}, "
                f"theta_rot: {[round(x, 3) for x in theta_rot]}, "
                f"theta_pwer: {[round(x, 3) for x in theta_pwer]}"
            )

            # Classification des points
            clusters = classifier.classify(
                wind_speed, rpm_norm, power_norm
            )  # Vent en valeurs réelles

            # Debug: afficher la distribution des clusters
            unique_clusters, counts = np.unique(clusters, return_counts=True)
            logger.info(
                f"Turbine {turbine_config.turbine_id}: Cluster distribution: "
                f"{dict(zip(unique_clusters.tolist(), counts.tolist()))}"
            )

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
            valid_data["wind_speed"] = wind_speed  # En m/s (valeurs réelles)
            valid_data["rpm"] = rpm
            valid_data["power"] = power
            valid_data["pitch"] = pitch
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
