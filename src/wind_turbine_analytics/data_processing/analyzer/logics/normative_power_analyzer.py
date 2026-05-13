# Standard library
from typing import Dict, Any

# Third-party
import pandas as pd

# Local imports
from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineConfig,
    ValidationCriteria,
    Criterion,
)
from src.wind_turbine_analytics.data_processing.log_code.generator_type.nordex_n311_log_code_manager import (
    NordexN311LogCodeManager,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class NormativeYieldAnalyzer(BaseAnalyzer):
    """
    L’analyse des courbes de puissance vise à évaluer la performances
    des éoliennes en comparant la production électrique en
    fonction de la vitesse du vent, dans des conditions d’exploitation
    homogènes.

    Elle permet d’identifier d’éventuels écarts de performance entre les
    éoliennes,ainsi que des situations de sous-performance susceptibles
    d’impacter la production du parc

    La comparaison des courbes de puissance est réalisée conformément aux principes de la norme IEC 61400-12,
    en s’appuyant sur des données SCADA filtrées afin de garantir des conditions de comparaison homogènes.
    Les traitements suivants sont appliqués :
    - exclusion des périodes affectées par des limitations environnementales (bruit, chauves-souris, etc.),
    - exclusion des situations de sillage (wake effect),
    - sélection de périodes communes de fonctionnement (éoliennes en état “run” simultanément),
    - correction des vitesses de vent à une densité de référence,
    - homogénéisation des conditions de vent entre éoliennes afin de permettre une
    comparaison équitable des performances.


    INPUT : Charger les données SCADA (Vitesse vent, Puissance, Direction, Température, Pression, Statut).
    STEP 1 (Nettoyage) : Supprimer les lignes où Status != 'Run'.
    STEP 2 (Environnement) : Supprimer les lignes où Bridage_Acoustique == True.
    STEP 3 (Sillage) : Supprimer les points selon la Direction_Vent (ex: entre 180° et 210° si une voisine est là).
    STEP 4 (Physique) : Calculer la densité de l'air et appliquer la formule de correction sur la vitesse du vent.
    STEP 5 (Synchro) : Faire une intersection des index (timestamps) pour ne garder que les moments où tout le parc est "propre".
    OUTPUT : Tracer la courbe de puissance (Power Curve) finale.
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
        Implémente l'analyse normative selon IEC 61400-12-2.

        Pipeline de traitement :
        1. Operating Period Filter : Filtrer périodes "Run" (wind_speed > cut-in, power > 1% P_nom)
        2. Environmental Filter : Exclure bridage acoustique (code FM733)
        3. Sillage : Ignoré dans cette version
        4. Physique : Corriger vitesse du vent à densité de référence
        5. Synchro : Retourner timestamps valides pour intersection externe

        Args:
            operation_data: DataFrame SCADA avec colonnes wind_speed, activation_power, temperature
            log_data: DataFrame logs avec codes d'erreur et plages temporelles
            turbine_config: Configuration turbine (mappings, test_start, test_end, P_nom)
            criteria: Critères de validation (cut_in_to_cut_out specification)

        Returns:
            Dict contenant chart_data, valid_timestamps, filtering_stats, density_stats, quality_metrics
        """
        # Constantes physiques IEC 61400-12-2
        R_AIR = 287.05  # J/(kg·K) - Constante gaz parfait air sec
        RHO_REF = 1.225  # kg/m³ - Densité de référence IEC
        P0 = 101325  # Pa - Pression atmosphérique standard (niveau mer)

        # ========== ÉTAPE 1 : OPERATING PERIOD FILTER - Filtrer périodes "Run" ==========
        logger.debug(f"STEP 1 - Operating Period Filter: Filtrage périodes 'Run' pour turbine {turbine_config.turbine_id}")

        # Extraire colonnes et configuration
        mapping = turbine_config.mapping_operation_data
        timestamp_col = mapping.timestamp
        wind_speed_col = mapping.wind_speed
        power_col = mapping.activation_power
        temperature_col = mapping.temperature

        test_start = turbine_config.test_start
        test_end = turbine_config.test_end
        P_nom = turbine_config.general_information.nominal_power

        # Gestion puissance nominale
        if P_nom is None:
            logger.warning(
                f"Nominal power not provided for turbine {turbine_config.turbine_id}. "
                f"Defaulting to 3780.0 kW."
            )
            P_nom = 3780.0
        if P_nom <= 100:
            logger.debug(
                f"Nominal power for turbine {turbine_config.turbine_id} is very low ({P_nom} kW). "
                f"Multiplying by 1000 to convert to kW."
            )
            P_nom = P_nom * 1000

        # Filtrer période de test
        df = operation_data[[timestamp_col, wind_speed_col, power_col, temperature_col]].copy()
        df = df[(df[timestamp_col] >= test_start) & (df[timestamp_col] <= test_end)]

        original_count = len(df)
        logger.debug(f"Points dans période de test [{test_start} - {test_end}]: {original_count}")

        # Convertir types numériques
        df[wind_speed_col] = pd.to_numeric(df[wind_speed_col], errors="coerce")
        df[power_col] = pd.to_numeric(df[power_col], errors="coerce")
        df[temperature_col] = pd.to_numeric(df[temperature_col], errors="coerce")

        # Supprimer NaN
        df = df.dropna(subset=[wind_speed_col, power_col, temperature_col])
        after_nan_removal = len(df)
        logger.debug(f"Points après suppression NaN: {after_nan_removal} (removed: {original_count - after_nan_removal})")

        # Récupérer cut-in depuis critères
        criterion = criteria.validation_criterion.get("cut_in_to_cut_out", Criterion())
        specification = getattr(criterion, "specification", None)
        if (
            specification is None
            or not isinstance(specification, (list, tuple))
            or len(specification) != 2
        ):
            logger.warning(
                f"Invalid specification for cut_in_to_cut_out criterion. Using default [3.0, 25.0]"
            )
            v_cut_in, v_cut_out = 3.0, 25.0
        else:
            v_cut_in, v_cut_out = specification

        # Critère "Run" : cut-in et production effective
        mask_run = (df[wind_speed_col] > v_cut_in) & (df[power_col] > 0.01 * P_nom)
        df = df[mask_run].copy()
        operating_period_removed = after_nan_removal - len(df)
        logger.debug(f"STEP 1 - Operating Period Filter complete: {len(df)} points retained (removed: {operating_period_removed})")

        # ========== ÉTAPE 2 : ENVIRONMENTAL FILTER - Exclure bridage acoustique ==========
        logger.debug(f"STEP 2 - Environmental Filter: Exclusion bridage acoustique (FM733) pour turbine {turbine_config.turbine_id}")

        # Initialiser manager
        manager = NordexN311LogCodeManager()

        # Colonnes des logs
        start_date_col = turbine_config.mapping_log_data.start_date
        end_date_col = turbine_config.mapping_log_data.end_date
        oper_col = turbine_config.mapping_log_data.oper

        # Créer masque pour exclure périodes FM733 (bridage acoustique)
        # Note: create_time_mask retourne True pour périodes normales, False pour périodes avec erreur
        # On utilise le masque directement car on veut garder les périodes normales (sans FM733)
        environmental_count_before = len(df)
        mask_no_curtailment = manager.create_time_mask(
            log_df=log_data,
            target_df=df,
            code_column=oper_col,
            log_start_col=start_date_col,
            log_end_col=end_date_col,
            target_timestamp_col=timestamp_col,
            codes_to_filter=["FM733"],  # Code bridage acoustique uniquement
        )

        df = df[mask_no_curtailment].copy()
        environmental_removed = environmental_count_before - len(df)
        logger.debug(f"STEP 2 - Environmental Filter complete: {len(df)} points retained (removed: {environmental_removed})")

        # ========== ÉTAPE 3 : SILLAGE - IGNORÉ ==========
        logger.debug("STEP 3: Wake filtering skipped (user decision)")

        # ========== ÉTAPE 4 : CORRECTION PHYSIQUE - Densité de l'air ==========
        logger.debug(f"STEP 4: Correction densité de l'air (IEC 61400-12-2) pour turbine {turbine_config.turbine_id}")

        # Vérifier plausibilité température
        temp_min, temp_max = df[temperature_col].min(), df[temperature_col].max()
        if temp_min < -40 or temp_max > 50:
            logger.warning(
                f"Température hors plage attendue [-40°C, +50°C] pour turbine {turbine_config.turbine_id}: "
                f"min={temp_min:.1f}°C, max={temp_max:.1f}°C"
            )

        # Conversion Celsius → Kelvin
        df["temperature_kelvin"] = df[temperature_col] + 273.15

        # Calcul densité de l'air : ρ = P / (R * T)
        df["air_density"] = P0 / (R_AIR * df["temperature_kelvin"])

        # Calcul facteur de correction : (ρ / ρ_ref)^(1/3)
        df["correction_factor"] = (df["air_density"] / RHO_REF) ** (1/3)

        # Conserver vitesse brute et créer vitesse corrigée
        df["wind_speed_raw"] = df[wind_speed_col]
        df["wind_speed_corrected"] = df[wind_speed_col] * df["correction_factor"]

        # Statistiques densité
        mean_density = df["air_density"].mean()
        min_density = df["air_density"].min()
        max_density = df["air_density"].max()
        mean_correction = df["correction_factor"].mean()
        std_correction = df["correction_factor"].std()

        step4_corrected = len(df)
        logger.debug(
            f"STEP 4 complete: {step4_corrected} points corrected "
            f"(mean_correction_factor={mean_correction:.4f}, std={std_correction:.4f})"
        )

        # ========== ÉTAPE 5 : SYNCHRONISATION - Préparer timestamps valides ==========
        logger.debug("STEP 5: Preparing valid timestamps for multi-turbine synchronization")

        valid_timestamps = pd.DatetimeIndex(df[timestamp_col])
        logger.debug(f"Valid timestamps extracted: {len(valid_timestamps)} points")

        # ========== ÉTAPE 6 : PRÉPARER RÉSULTATS ET STATISTIQUES ==========
        logger.debug("STEP 6: Building output structure")

        # Préparer DataFrame pour visualisation
        chart_data = df[[
            timestamp_col,
            "wind_speed_corrected",
            "wind_speed_raw",
            power_col,
            temperature_col,
            "air_density",
            "correction_factor"
        ]].copy()

        chart_data = chart_data.rename(columns={
            timestamp_col: "timestamp",
            power_col: "activation_power",
            temperature_col: "temperature"
        })

        # Ajouter des alias pour compatibilité avec PowerCurveChartVisualizer
        # Ce visualizer est utilisé dans RunTestWorkflow et ScadaWorkflow
        chart_data["wind_speed"] = chart_data["wind_speed_corrected"]  # Alias pour le visualizer
        chart_data["power"] = chart_data["activation_power"]  # Alias pour le visualizer

        final_count = len(chart_data)
        data_retention = (final_count / original_count * 100) if original_count > 0 else 0.0

        # Construire dictionnaire de résultats
        result = {
            "chart_data": chart_data,
            "valid_timestamps": valid_timestamps,
            "filtering_stats": {
                "original_count": original_count,
                "operating_period_removed": operating_period_removed,
                "environmental_removed": environmental_removed,
                "points_corrected": step4_corrected,
                "final_count": final_count
            },
            "density_stats": {
                "mean_density": float(mean_density),
                "min_density": float(min_density),
                "max_density": float(max_density),
                "mean_correction_factor": float(mean_correction),
                "std_correction_factor": float(std_correction)
            },
            "quality_metrics": {
                "data_retention_percent": float(data_retention),
                "temperature_range": [float(temp_min), float(temp_max)],
                "wind_speed_range_corrected": [
                    float(chart_data["wind_speed_corrected"].min()),
                    float(chart_data["wind_speed_corrected"].max())
                ]
            }
        }

        logger.debug(
            f"Normative yield analysis completed for {turbine_config.turbine_id}: "
            f"{final_count}/{original_count} points retained ({data_retention:.1f}%)"
        )

        return result
