"""Data Availability Tabler for SCADA analysis."""

from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler


class DataAvailabilityTabler(BaseTabler):
    """
    Generates data availability table showing per-variable availability percentages.

    Table format:
    | WTG | Wind Speed [%] | Wind Dir. [%] | Temperature [%] | Power [%] | Status |

    Status levels based on overall availability average:
    - SUCCESS: > 80%
    - MINOR FIX: 60% < avg ≤ 80%
    - WARNING: 40% < avg ≤ 60%
    - MAJOR RISK: 20% < avg ≤ 40%
    - CRITICAL: 0% ≤ avg ≤ 20%
    """

    def __init__(self):
        super().__init__(table_name="data_availability_table")

    def _get_table_headers(self) -> List[str]:
        """Return column headers for the table."""
        return [
            "WTG",
            "Wind Speed [%]",
            "Wind Dir. [%]",
            "Temperature [%]",
            "Power [%]",
            "Status",
        ]

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Transform turbine availability data into a table row.

        Args:
            turbine_id: Turbine identifier (e.g., "E01", "E02")
            turbine_result: Dict containing "summary" key with availability percentages
        """
        summary = turbine_result.get("summary", {})

        # Extract availability percentages
        wind_speed_pct = summary.get("wind_speed_availability_pct", 0.0)
        wind_dir_pct = summary.get("wind_direction_availability_pct", 0.0)
        temperature_pct = summary.get("temperature_availability_pct", 0.0)
        power_pct = summary.get("active_power_availability_pct", 0.0)

        # Calculate overall availability (average of all variables)
        # Temperature is optional, so only include if > 0
        variables = [wind_speed_pct, wind_dir_pct, power_pct]
        if temperature_pct > 0:
            variables.append(temperature_pct)

        overall_avg = sum(variables) / len(variables) if variables else 0.0

        # Determine status based on overall average
        status = self._determine_status(overall_avg)

        # Append row data
        self._table_data.append({
            "wtg": turbine_id,
            "wind_speed_pct": self._format_number(wind_speed_pct, decimals=1, unit="%"),
            "wind_dir_pct": self._format_number(wind_dir_pct, decimals=1, unit="%"),
            "temperature_pct": self._format_number(temperature_pct, decimals=1, unit="%"),
            "power_pct": self._format_number(power_pct, decimals=1, unit="%"),
            "status": status,
        })

    def _determine_status(self, overall_avg: float) -> str:
        """
        Determine status level based on overall availability average.

        Args:
            overall_avg: Average availability percentage (0-100)

        Returns:
            Status string: SUCCESS, MINOR FIX, WARNING, MAJOR RISK, or CRITICAL
        """
        if overall_avg > 80.0:
            return "✓ SUCCESS"
        elif overall_avg > 60.0:
            return "⚠ MINOR FIX"
        elif overall_avg > 40.0:
            return "⚠ WARNING"
        elif overall_avg > 20.0:
            return "✗ MAJOR RISK"
        else:
            return "✗ CRITICAL"
