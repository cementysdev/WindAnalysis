"""SCADA report tables."""

from .table_eba_cut_in_cut_out import EbaCutInCutOutTabler
from .table_tba_cut_in_cut_out import TbaCutInCutOutTabler
from .table_eba_manifacturer import EbaManufacturerTabler
from .table_tba_manufacturer import TbaManufacturerTabler
from .table_eba_loss import EbaLossTabler
from .table_scada_summary import ScadaSummaryTabler
from .table_error_code_pareto_frequecy import ErrorCodeParetoFrequencyTabler
from .table_error_code_pareto_duration import ErrorCodeParetoDurationTabler
from .table_yield_normative import NormativeYieldTabler
from .table_wind_direction_calibration import WindDirectionCalibrationTabler
from .tip_speed_ratio import TipSpeedRatioTabler
from .table_pitch import PitchTabler
from .table_data_availability import DataAvailabilityTabler
from .table_performance_level import PerformanceLevelTabler
from .table_status_summary import StatusSummaryTabler
from .table_gps_coordinates import GpsCoordinatesTabler

__all__ = [
    "EbaCutInCutOutTabler",
    "TbaCutInCutOutTabler",
    "EbaManufacturerTabler",
    "TbaManufacturerTabler",
    "EbaLossTabler",
    "ScadaSummaryTabler",
    "ErrorCodeParetoFrequencyTabler",
    "ErrorCodeParetoDurationTabler",
    "NormativeYieldTabler",
    "WindDirectionCalibrationTabler",
    "TipSpeedRatioTabler",
    "PitchTabler",
    "DataAvailabilityTabler",
    "PerformanceLevelTabler",
    "StatusSummaryTabler",
    "GpsCoordinatesTabler",
]
