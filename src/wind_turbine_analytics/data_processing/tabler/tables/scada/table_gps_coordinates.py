"""GPS Coordinates Tabler for SCADA analysis."""

from typing import Dict, Any, List
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler


class GpsCoordinatesTabler(BaseTabler):
    """
    Generates GPS coordinates table showing turbine location and physical characteristics.

    Table format:
    | WTG | Hub Height | Rotor Diameter | GPS Coordinates (X) | GPS Coordinates (Y) |

    Data extracted from TurbineConfig.general_information:
    - hub_height: Height of the turbine hub (meters)
    - rotor_diameter: Diameter of the rotor (meters)
    - gps_coordinates: [latitude, longitude] or [X, Y]
    """

    def __init__(self):
        super().__init__(table_name="gps_coordinates_table")

    def _get_table_headers(self) -> List[str]:
        """Return column headers for the table."""
        return [
            "WTG",
            "Hub Height",
            "Rotor Diameter",
            "GPS Coordinates (X)",
            "GPS Coordinates (Y)",
        ]

    def generate_from_turbine_farm(self, turbine_farm) -> Dict[str, Any]:
        """
        Generate GPS coordinates table from TurbineFarm configuration.

        Args:
            turbine_farm: TurbineFarm object containing turbine configurations

        Returns:
            Dict with table_name as key and list of row dicts as value
        """
        self._table_data = []

        # Sort turbine IDs for consistent ordering
        turbine_ids = sorted(turbine_farm.farm.keys())

        for turbine_id in turbine_ids:
            turbine_config = turbine_farm.farm[turbine_id]
            general_info = turbine_config.general_information

            # Extract data from general_information
            hub_height = general_info.hub_height if general_info else "N/A"
            rotor_diameter = general_info.rotor_diameter if general_info else "N/A"
            gps_coords = general_info.gps_coordinates if general_info else []

            # Extract GPS coordinates
            gps_x = "N/A"
            gps_y = "N/A"
            if gps_coords and isinstance(gps_coords, list) and len(gps_coords) >= 2:
                gps_x = self._format_number(gps_coords[0], decimals=6, unit="")
                gps_y = self._format_number(gps_coords[1], decimals=6, unit="")

            # Format hub_height and rotor_diameter with units
            if hub_height != "N/A":
                hub_height = self._format_number(
                    float(hub_height), decimals=1, unit="m"
                )
            if rotor_diameter != "N/A":
                rotor_diameter = self._format_number(
                    float(rotor_diameter), decimals=1, unit="m"
                )

            self._table_data.append(
                {
                    "wtg": turbine_id,
                    "hub_height": hub_height,
                    "rotor_diameter": rotor_diameter,
                    "gps_x": gps_x,
                    "gps_y": gps_y,
                }
            )

        return {
            self.table_name: self._table_data,
            f"{self.table_name}_raw": self._table_data,
            f"{self.table_name}_headers": self._get_table_headers(),
        }

    def _add_table_row(self, turbine_id: str, turbine_result: Dict[str, Any]) -> None:
        """
        Not used for this tabler - data comes from configuration, not analysis results.
        Use generate_from_turbine_farm() instead.
        """
        pass
