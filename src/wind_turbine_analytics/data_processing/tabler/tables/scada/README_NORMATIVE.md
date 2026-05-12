# NormativeYieldTabler

## Vue d'ensemble

Le `NormativeYieldTabler` génère un tableau récapitulatif des statistiques de l'analyse normative IEC 61400-12-2 pour chaque turbine.

## Objectif

Fournir une vue consolidée des données filtrées et corrigées, incluant :
- **Statistiques de filtrage** : Operating Period Filter, Environmental Filter
- **Taux de rétention** : Pourcentage de données conservées après filtrage
- **Correction physique** : Densité de l'air et facteur de correction
- **Plages de validation** : Température et vitesse du vent corrigée

## Structure du tableau

### En-têtes

| Colonne | Description | Format |
|---------|-------------|--------|
| WTG | ID de la turbine | String |
| Points initiaux | Nombre de points avant filtrage | Integer |
| Operating Filter | Points supprimés (périodes non-Run) | Integer |
| Environmental Filter | Points supprimés (bridage acoustique FM733) | Integer |
| Points finaux | Nombre de points après filtrage | Integer |
| Rétention (%) | Taux de conservation des données | Float (1 décimale) |
| Densité moy. (kg/m³) | Densité moyenne de l'air | Float (3 décimales) |
| Correction moy. | Facteur de correction moyen (ρ/ρ_ref)^(1/3) | Float (4 décimales) |
| Temp. range (°C) | Plage de température [min, max] | [Float, Float] |
| Wind speed range (m/s) | Plage de vitesse corrigée [min, max] | [Float, Float] |

### Exemple de sortie

```
| WTG | Points initiaux | Operating Filter | Environmental Filter | Points finaux | Rétention (%) | Densité moy. (kg/m³) | Correction moy. | Temp. range (°C) | Wind speed range (m/s) |
|-----|-----------------|------------------|---------------------|---------------|---------------|----------------------|-----------------|------------------|----------------------|
| E1  | 12000           | 800              | 400                 | 10800         | 90.0 %        | 1.192                | 0.9901          | [3.2, 27.8]      | [3.1, 24.2]          |
| E6  | 11800           | 1400             | 1450                | 8950          | 75.8 %        | 1.208                | 0.9938          | [1.5, 28.9]      | [3.2, 23.7]          |
| E8  | 12200           | 3800             | 850                 | 7550          | 61.9 %        | 1.176                | 0.9825          | [-0.5, 29.8]     | [3.3, 24.5]          |
```

## Utilisation

### Importation

```python
from src.wind_turbine_analytics.data_processing.tabler.tables.scada import NormativeYieldTabler
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
```

### Génération du tableau

```python
# Après avoir exécuté NormativeYieldAnalyzer
analyzer = NormativeYieldAnalyzer()
result = analyzer.analyze(turbine_farm, criteria)

# Générer le tableau
tabler = NormativeYieldTabler()
output = tabler.generate(result)

# Accéder aux données
table_data = output["normative_yield_table"]  # Liste de dicts pour docxtpl
table_raw = output["normative_yield_table_raw"]  # Données brutes
```

## Structure des données d'entrée

Le tabler attend un `AnalysisResult` avec la structure suivante dans `detailed_results` :

```python
{
    "E1": {
        "filtering_stats": {
            "original_count": int,
            "operating_period_removed": int,
            "environmental_removed": int,
            "points_corrected": int,
            "final_count": int
        },
        "density_stats": {
            "mean_density": float,
            "min_density": float,
            "max_density": float,
            "mean_correction_factor": float,
            "std_correction_factor": float
        },
        "quality_metrics": {
            "data_retention_percent": float,
            "temperature_range": [float, float],
            "wind_speed_range_corrected": [float, float]
        }
    },
    # ... autres turbines
}
```

## Interprétation des résultats

### Taux de rétention

- **≥ 85%** : ✓ Excellente qualité de données
- **70-85%** : ⚠ Qualité acceptable, surveiller
- **< 70%** : ✗ Qualité problématique, investiguer

### Operating Filter (points supprimés)

- **Critère** : `wind_speed ≤ cut-in` OU `power ≤ 1% P_nom`
- **Valeur élevée** : Beaucoup d'arrêts opérationnels → Vérifier pannes/maintenance

### Environmental Filter (points supprimés)

- **Critère** : Code FM733 (bridage acoustique)
- **Valeur élevée** : Bridage fréquent → Impact sur représentativité de la courbe

### Densité de l'air

- **Plage attendue** : 1.0 - 1.4 kg/m³
- **Densité de référence IEC** : 1.225 kg/m³
- **Correction** : `v_corrected = v_measured × (ρ / ρ_ref)^(1/3)`

## Tests

### Tests unitaires

```bash
# Exécuter les tests du tabler
pytest tests/test_normative_yield_tabler.py -v

# Tests d'intégration analyzer-tabler
pytest tests/test_normative_integration.py -v
```

### Exemple d'utilisation

```bash
# Exécuter l'exemple avec données mockées
python tests/example_normative_yield_tabler.py
```

## Conventions

### Nommage des colonnes (clés docxtpl)

Les clés de colonnes suivent la convention `snake_case` pour compatibilité avec les templates Word :

```python
{
    "wtg": "E1",
    "points_initiaux": "12000",
    "operating_filter": "800",
    "environmental_filter": "400",
    # ...
}
```

### Formatage des valeurs

- **Entiers** : Convertis en string (ex: `"12000"`)
- **Pourcentages** : 1 décimale + unité (ex: `"90.0 %"`)
- **Densité** : 3 décimales (ex: `"1.192"`)
- **Facteur de correction** : 4 décimales (ex: `"0.9901"`)
- **Plages** : Format `[min, max]` avec 1 décimale (ex: `"[3.2, 27.8]"`)

## Compatibilité

- **Analyzer** : `NormativeYieldAnalyzer`
- **Python** : 3.10+
- **Dependencies** : `BaseTabler` (héritage)

## Historique

- **2026-05-11** : Création initiale avec noms explicites (Operating Filter, Environmental Filter)
- **2026-04-29** : Implémentation de `NormativeYieldAnalyzer` (base)

## Voir aussi

- [NormativeYieldAnalyzer](../../analyzer/logics/normative_power_analyzer.py) : Analyseur source
- [BaseTabler](../../base_tabler.py) : Classe de base
- [CLAUDE.md](../../../../../../CLAUDE.md) : Documentation globale du projet
