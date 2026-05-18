"""TBA Cut-In/Cut-Out Tabler for SCADA analysis."""

from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler


class TbaCutInCutOutTabler(BaseTabler):
    """
    Generates Time-Based Availability (TBA) table for cut-in/cut-out analysis.

    Structure: Pivot table with months in rows and turbines in columns.
    - Each cell shows the availability percentage for that month/turbine
    - Summary rows: MEAN (average) and STATUS (status level)

    Similar to EbaCutInCutOutTabler but shows time-based availability instead of energy-based.
    """

    def __init__(self):
        super().__init__(table_name="tba_cut_in_cut_out_table")
        self._monthly_data = {}  # {period: {turbine_id: availability_pct}}
        self._turbine_ids = set()

    def _get_table_headers(self) -> List[str]:
        """Return column headers (dynamically built in generate)."""
        headers = ["Period"]

        # Ajouter une colonne par turbine (ordre alphabétique)
        for turbine_id in sorted(self._turbine_ids):
            headers.append(f"WTG {turbine_id}")

        # Ajouter colonne WindFarm (moyenne)
        headers.append("WindFarm")

        return headers

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Process monthly availability data for one turbine.

        Args:
            turbine_id: Turbine identifier
            turbine_result: Dict containing monthly_availability list
        """
        self._turbine_ids.add(turbine_id)

        monthly_data = turbine_result.get("monthly_availability", [])

        for month_entry in monthly_data:
            period = month_entry.get("month", "Unknown")
            availability_pct = month_entry.get("availability_pct", 0.0)

            if period not in self._monthly_data:
                self._monthly_data[period] = {}

            self._monthly_data[period][turbine_id] = availability_pct

    def generate(self, result) -> Dict[str, Any]:
        """
        Generate pivot table with turbines as columns.

        Returns:
            Dict with table_name as key and list of row dicts as value
        """
        # First, populate internal data structure
        super().generate(result)

        # Now build pivot table
        self._table_data = []
        self._pivot_monthly_data()

        return {
            self.table_name: self._table_data,
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),
        }

    def _pivot_monthly_data(self) -> None:
        """Transform monthly data into pivot table format with summary rows."""
        if not self._turbine_ids:
            return

        # Sort periods chronologically
        sorted_periods = sorted(self._monthly_data.keys())

        # Build rows: one per period
        for period in sorted_periods:
            row = {"period": period}
            turbine_availabilities = self._monthly_data[period]

            # Add each turbine's availability as a column
            for turbine_id in sorted(self._turbine_ids):
                col_key = f"wtg_{turbine_id.lower()}"
                availability = turbine_availabilities.get(turbine_id, None)

                if availability is not None:
                    row[col_key] = self._format_number(
                        availability, decimals=2, unit="%"
                    )
                else:
                    row[col_key] = "N/A"

            # Calculate WindFarm average for this period
            valid_availabilities = [
                avail for avail in turbine_availabilities.values() if avail is not None
            ]
            if valid_availabilities:
                avg_availability = sum(valid_availabilities) / len(valid_availabilities)
                row["windfarm"] = self._format_number(
                    avg_availability, decimals=2, unit="%"
                )
            else:
                row["windfarm"] = "N/A"

            self._table_data.append(row)

        # Add summary rows at the end
        self._add_summary_rows()

    def _add_summary_rows(self) -> None:
        """Add MEAN and STATUS rows after all period data."""
        if not self._turbine_ids:
            return

        # Collect all availabilities per turbine
        turbine_all_availabilities = {tid: [] for tid in self._turbine_ids}

        for period, turbine_availabilities in self._monthly_data.items():
            for turbine_id, availability in turbine_availabilities.items():
                if availability is not None and availability > 0:
                    turbine_all_availabilities[turbine_id].append(availability)

        # Calculate means
        turbine_means = {}
        for turbine_id in sorted(self._turbine_ids):
            availabilities = turbine_all_availabilities[turbine_id]
            if availabilities:
                turbine_means[turbine_id] = sum(availabilities) / len(availabilities)

        # MEAN row
        mean_row = {"period": "MEAN"}
        for turbine_id in sorted(self._turbine_ids):
            col_key = f"wtg_{turbine_id.lower()}"
            if turbine_id in turbine_means:
                mean_row[col_key] = self._format_number(
                    turbine_means[turbine_id], decimals=2, unit="%"
                )
            else:
                mean_row[col_key] = "N/A"

        # WindFarm mean
        if turbine_means:
            wf_mean = sum(turbine_means.values()) / len(turbine_means)
            mean_row["windfarm"] = self._format_number(wf_mean, decimals=2, unit="%")
        else:
            mean_row["windfarm"] = "N/A"

        self._table_data.append(mean_row)

        # STATUS row
        from src.wind_turbine_analytics.data_processing.status_levels import (
            StatusLevel,
        )

        status_row = {"period": "STATUS"}

        for turbine_id in sorted(self._turbine_ids):
            col_key = f"wtg_{turbine_id.lower()}"
            if turbine_id in turbine_means:
                status = StatusLevel.from_percentage(turbine_means[turbine_id])
                status_row[col_key] = str(status)
            else:
                status_row[col_key] = "N/A"

        # WindFarm status
        if turbine_means:
            wf_mean = sum(turbine_means.values()) / len(turbine_means)
            wf_status = StatusLevel.from_percentage(wf_mean)
            status_row["windfarm"] = str(wf_status)
        else:
            status_row["windfarm"] = "N/A"

        self._table_data.append(status_row)
