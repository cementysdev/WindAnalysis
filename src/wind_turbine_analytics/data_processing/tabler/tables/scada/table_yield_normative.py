from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_result_models import (
    AnalysisResult,
)
from src.logger_config import get_logger

logger = get_logger(__name__)


class NormativeYieldTabler(BaseTabler):
    """
    Tabler pour l'analyse normative IEC 61400-12-2 (version simplifiée).

    Génère un tableau avec une ligne par turbine contenant :
    - Taux de rétention des données après filtrage
    - Puissance maximale observée
    - Plages de température et vitesse de vent corrigée
    - Nombre de points supprimés (Operating Filter)

    Structure de sortie:
    | WTG | Rétention (%) | Max Power (kW) | Temp. range (°C) | Wind Speed range (m/s) | Operating Filter |
    """

    def __init__(self):
        super().__init__(table_name="normative_yield_table")

    def _get_table_headers(self) -> List[str]:
        """
        Retourne les en-têtes du tableau pour l'analyse normative.

        Returns:
            Liste des headers avec 7 colonnes
        """
        return [
            "WTG",
            "Rétention (%)",
            "Max Power (kW)",
            "Temp. range (°C)",
            "Wind Speed range (m/s)",
            "Operating Filter",
            "STATUS",
        ]

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Ajoute une ligne au tableau pour une turbine avec ses statistiques normatives simplifiées.

        Args:
            turbine_id: ID de la turbine
            turbine_result: Résultats contenant:
                - filtering_stats: Compteurs de filtrage (operating_period_removed)
                - quality_metrics: Métriques qualité (retention, temp_range, wind_speed_range)
                - chart_data: DataFrame avec colonne activation_power pour extraire max
        """
        # Extraire les statistiques de filtrage
        filtering_stats = turbine_result.get("filtering_stats", {})
        operating_removed = filtering_stats.get("operating_period_removed", 0)

        # Extraire les métriques de qualité
        quality_metrics = turbine_result.get("quality_metrics", {})
        data_retention = quality_metrics.get("data_retention_percent", 0.0)
        temp_range = quality_metrics.get("temperature_range", [0.0, 0.0])
        wind_speed_range = quality_metrics.get("wind_speed_range_corrected", [0.0, 0.0])
        status_level = quality_metrics.get("status_level", None)

        # Extraire la puissance maximale depuis chart_data
        chart_data = turbine_result.get("chart_data", None)
        max_power = 0.0
        if chart_data is not None and not chart_data.empty:
            if "activation_power" in chart_data.columns:
                max_power = float(chart_data["activation_power"].max())

        # Formater le status
        status_str = str(status_level) if status_level is not None else "N/A"

        # Construire la ligne du tableau
        row_data = {
            "wtg": turbine_id,
            "retention": self._format_number(data_retention, decimals=1, unit="%"),
            "max_power": self._format_number(max_power, decimals=2, unit="kW"),
            "temp_range": f"[{temp_range[0]:.1f}, {temp_range[1]:.1f}]",
            "wind_speed_range": f"[{wind_speed_range[0]:.1f}, {wind_speed_range[1]:.1f}]",
            "operating_filter": str(operating_removed),
            "status": status_str,
        }

        self._table_data.append(row_data)
