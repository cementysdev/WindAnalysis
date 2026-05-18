"""Status Summary Tabler - Global overview of all analyses per turbine."""

from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.data_processing.data_processing import AnalysisResult


class StatusSummaryTabler(BaseTabler):
    """
    Generates a summary table showing the status of each analysis for each turbine.

    Structure (TRANSPOSED - criteria in rows, turbines in columns):
    | Criterion              | LU09        | LU10        | LU11        | LU12        |
    |------------------------|-------------|-------------|-------------|-------------|
    | Data Availability      | ✓ SUCCESS   | ✓ SUCCESS   | ✓ SUCCESS   | ✓ SUCCESS   |
    | EBA Manufacturer       | ⚠ MINOR FIX | ⚠ MINOR FIX | ⚠ MINOR FIX | ✓ SUCCESS   |
    | ...                    | ...         | ...         | ...         | ...         |

    This table provides a quick overview of turbine health across all analyses.
    """

    def __init__(self):
        super().__init__(table_name="status_summary_table")
        self._analysis_results = {}

    def add_analysis_result(self, analysis_name: str, result: AnalysisResult) -> None:
        """
        Store analysis result for later processing.

        Args:
            analysis_name: Name of the analysis (e.g., "data_availability", "eba_manufacturer")
            result: AnalysisResult containing status_level for each turbine
        """
        self._analysis_results[analysis_name] = result

    def _get_table_headers(self) -> List[str]:
        """
        Return column headers.

        Note: Headers are dynamically generated in generate() based on available turbines.
        This method returns a placeholder to satisfy BaseTabler's abstract method.
        """
        return ["Criterion"]

    def generate(self) -> Dict[str, Any]:
        """
        Generate the status summary table from all stored analysis results.

        Returns:
            Dict with table_name as key and list of row dicts as value
        """
        # Get all turbine IDs from the first analysis result
        if not self._analysis_results:
            return {self.table_name: []}

        # Extract turbine IDs from first available result
        first_result = next(iter(self._analysis_results.values()))
        turbine_ids = sorted(first_result.detailed_results.keys())

        # Define criteria with their display names and extraction logic
        criteria = [
            {
                "name": "Data Availability",
                "analysis": "data_availability",
                "extractor": lambda result, tid: self._get_status_with_fallback(
                    result, tid, ["status_level", "avg_availability_status"]
                ),
            },
            {
                "name": "EBA Manufacturer",
                "analysis": "eba_manufacturer",
                "extractor": lambda result, tid: self._get_status(
                    result, tid, "status_level"
                ),
            },
            {
                "name": "EBA Cut-In/Cut-Out",
                "analysis": "eba_cut_in_cut_out",
                "extractor": lambda result, tid: self._get_status(
                    result, tid, "status_level"
                ),
            },
            {
                "name": "Wind Calibration",
                "analysis": "wind_calibration",
                "extractor": lambda result, tid: self._get_status(
                    result, tid, "status_level"
                ),
            },
            {
                "name": "Tip Speed Ratio",
                "analysis": "tip_speed_ratio",
                "extractor": lambda result, tid: self._get_status(
                    result, tid, "status_level"
                ),
            },
            {
                "name": "Pitch Angle",
                "analysis": "pitch_angle",
                "extractor": lambda result, tid: self._get_status(
                    result, tid, "status_level"
                ),
            },
            {
                "name": "Performance Level",
                "analysis": "performance_level",
                "extractor": lambda result, tid: self._get_status(
                    result, tid, "status_level"
                ),
            },
            {
                "name": "Normative Yield",
                "analysis": "normative_yield",
                "extractor": lambda result, tid: self._get_status_nested(
                    result, tid, ["quality_metrics", "status_level"]
                ),
            },
        ]

        # Build rows (one row per criterion)
        self._table_data = []
        for criterion in criteria:
            row = {"criterion": criterion["name"]}

            # Get analysis result
            if criterion["analysis"] not in self._analysis_results:
                # If analysis not available, mark all turbines as N/A
                for turbine_id in turbine_ids:
                    row[turbine_id] = "N/A"
            else:
                result = self._analysis_results[criterion["analysis"]]
                # Extract status for each turbine
                for turbine_id in turbine_ids:
                    status = criterion["extractor"](result, turbine_id)
                    row[turbine_id] = status

            self._table_data.append(row)

        return {self.table_name: self._table_data}

    def _get_status(self, result: AnalysisResult, turbine_id: str, key: str) -> str:
        """
        Extract status from analysis result.

        Args:
            result: AnalysisResult object
            turbine_id: Turbine identifier
            key: Key to extract status from (e.g., "status_level")

        Returns:
            Status string or "N/A" if not found
        """
        if turbine_id not in result.detailed_results:
            return "N/A"

        turbine_result = result.detailed_results[turbine_id]
        status = turbine_result.get(key, None)

        if status is None:
            return "N/A"

        return str(status)

    def _get_status_with_fallback(
        self, result: AnalysisResult, turbine_id: str, keys: List[str]
    ) -> str:
        """
        Extract status with multiple fallback keys.

        Args:
            result: AnalysisResult object
            turbine_id: Turbine identifier
            keys: List of keys to try in order

        Returns:
            Status string or "N/A" if not found
        """
        if turbine_id not in result.detailed_results:
            return "N/A"

        turbine_result = result.detailed_results[turbine_id]

        for key in keys:
            status = turbine_result.get(key, None)
            if status is not None:
                return str(status)

        return "N/A"

    def _get_status_nested(
        self, result: AnalysisResult, turbine_id: str, keys: List[str]
    ) -> str:
        """
        Extract status from nested dict structure.

        Args:
            result: AnalysisResult object
            turbine_id: Turbine identifier
            keys: List of keys to traverse (e.g., ["quality_metrics", "status_level"])

        Returns:
            Status string or "N/A" if not found
        """
        if turbine_id not in result.detailed_results:
            return "N/A"

        # Traverse nested dict
        current = result.detailed_results[turbine_id]
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return "N/A"
            current = current[key]

        if current is None:
            return "N/A"

        return str(current)

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """Not used - generate() builds all rows at once."""
        pass
