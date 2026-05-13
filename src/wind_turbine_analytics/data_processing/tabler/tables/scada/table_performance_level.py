"""Performance Level Distribution Tabler for SCADA analysis."""

from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler


class PerformanceLevelTabler(BaseTabler):
    """
    Generates performance level distribution table.

    Shows percentage of measurements in each zone (1-6) per turbine.

    Structure:
    | WTG | Zone 1 (%) | Zone 2 (%) | Zone 3 (%) | Zone 4 (%) | Zone 5 (%) | Zone 6 (%) | Outside Z6 (%) | STATUS |
    """

    def __init__(self):
        super().__init__(table_name="performance_level_table")

    def _get_table_headers(self) -> List[str]:
        """Return column headers."""
        return [
            "WTG",
            "Zone 1 (%)",
            "Zone 2 (%)",
            "Zone 3 (%)",
            "Zone 4 (%)",
            "Zone 5 (%)",
            "Zone 6 (%)",
            "Outside Z6 (%)",
            "STATUS",
        ]

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Transform turbine performance level data into table row.

        Args:
            turbine_id: Turbine identifier (e.g., "E01", "E02")
            turbine_result: Dict containing:
                - zone_distribution: Dict with zone_1_pct, zone_2_pct, ..., zone_6_pct
                - percentage_outside_zone6: Percentage of points outside zone 6
                - status_level: StatusLevel enum
        """
        zone_dist = turbine_result.get("zone_distribution", {})
        outside_z6 = turbine_result.get("percentage_outside_zone6", 0.0)
        status_level = turbine_result.get("status_level", None)

        # Formater le status
        status_str = str(status_level) if status_level is not None else "N/A"

        self._table_data.append(
            {
                "wtg": turbine_id,
                "zone1_pct": self._format_number(
                    zone_dist.get("zone_1_pct", 0.0), decimals=1, unit="%"
                ),
                "zone2_pct": self._format_number(
                    zone_dist.get("zone_2_pct", 0.0), decimals=1, unit="%"
                ),
                "zone3_pct": self._format_number(
                    zone_dist.get("zone_3_pct", 0.0), decimals=1, unit="%"
                ),
                "zone4_pct": self._format_number(
                    zone_dist.get("zone_4_pct", 0.0), decimals=1, unit="%"
                ),
                "zone5_pct": self._format_number(
                    zone_dist.get("zone_5_pct", 0.0), decimals=1, unit="%"
                ),
                "zone6_pct": self._format_number(
                    zone_dist.get("zone_6_pct", 0.0), decimals=1, unit="%"
                ),
                "outside_z6_pct": self._format_number(
                    outside_z6, decimals=1, unit="%"
                ),
                "status": status_str,
            }
        )
