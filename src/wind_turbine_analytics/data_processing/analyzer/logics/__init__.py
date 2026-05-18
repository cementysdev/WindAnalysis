"""RunTest analysis logics."""

from src.wind_turbine_analytics.data_processing.analyzer.logics.consecutive_hours_analyzer import (
    ConsecutiveHoursAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.test_cut_in_cut_out_analyzer import (
    TestCutInCutOutAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.nominal_power_analyzer import (
    NominalPowerAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.autonomous_operation import (
    AutonomousOperationAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.test_availability_analyzer import (
    TestAvailabilityAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.data_availability_analyzer import (
    DataAvailabilityAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.eba_cut_in_cut_out_analyzer import (
    EbACutInCutOutAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.tba_cut_in_cut_out_analyzer import (
    TbACutInCutOutAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.eba_manifacturer_analyzer import (
    EbaManufacturerAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.tba_manifacturer_analyzer import (
    TbaManufacturerAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.code_error_analyzer import (
    CodeErrorAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.wind_direction_calibration_analyzer import (
    WindDirectionCalibrationAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.tip_speed_ratio import (
    TipSpeedRatioAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.normative_power_analyzer import (
    NormativeYieldAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.performance_level_analyzer import (
    PerformanceLevelAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.pitch_analyzer import (
    PitchAnalyzer,
)

__all__ = [
    # RunTest analyzers
    "ConsecutiveHoursAnalyzer",
    "TestCutInCutOutAnalyzer",
    "NominalPowerAnalyzer",
    "AutonomousOperationAnalyzer",
    "TestAvailabilityAnalyzer",
    # SCADA analyzers
    "DataAvailabilityAnalyzer",
    "EbACutInCutOutAnalyzer",
    "TbACutInCutOutAnalyzer",
    "EbaManufacturerAnalyzer",
    "TbaManufacturerAnalyzer",
    "CodeErrorAnalyzer",
    "WindDirectionCalibrationAnalyzer",
    "TipSpeedRatioAnalyzer",
    "NormativeYieldAnalyzer",
    "PerformanceLevelAnalyzer",
    "PitchAnalyzer",
]
