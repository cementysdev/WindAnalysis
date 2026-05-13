"""Status level system for performance evaluation."""

from enum import Enum
from typing import Optional


class StatusLevel(Enum):
    """5-level status system for SCADA analysis."""

    SUCCESS = "✓ SUCCESS"
    MINOR_FIX = "⚠ MINOR FIX"
    WARNING = "⚠ WARNING"
    MAJOR_RISK = "✗ MAJOR RISK"
    CRITICAL = "✗ CRITICAL"

    @classmethod
    def from_percentage(
        cls, value: float, thresholds: Optional[dict] = None
    ) -> "StatusLevel":
        """
        Map percentage value to status level.

        Args:
            value: Percentage value (0-100)
            thresholds: Custom thresholds dict {success: 80, minor: 60, warning: 40, major: 20}
                       Default: 80/60/40/20

        Returns:
            StatusLevel enum
        """
        if thresholds is None:
            thresholds = {
                "success": 80.0,
                "minor": 60.0,
                "warning": 40.0,
                "major": 20.0,
            }

        if value > thresholds["success"]:
            return cls.SUCCESS
        elif value > thresholds["minor"]:
            return cls.MINOR_FIX
        elif value > thresholds["warning"]:
            return cls.WARNING
        elif value > thresholds["major"]:
            return cls.MAJOR_RISK
        else:
            return cls.CRITICAL

    @classmethod
    def from_angle_error(
        cls, value: float, thresholds: Optional[dict] = None
    ) -> "StatusLevel":
        """
        Map angle error (degrees) to status level.

        Args:
            value: Angle error in degrees
            thresholds: Custom thresholds dict {success: 3, minor: 5, warning: 7, major: 10}
                       Default: 3/5/7/10

        Returns:
            StatusLevel enum
        """
        if thresholds is None:
            thresholds = {
                "success": 3.0,
                "minor": 5.0,
                "warning": 7.0,
                "major": 10.0,
            }

        if value < thresholds["success"]:
            return cls.SUCCESS
        elif value < thresholds["minor"]:
            return cls.MINOR_FIX
        elif value < thresholds["warning"]:
            return cls.WARNING
        elif value < thresholds["major"]:
            return cls.MAJOR_RISK
        else:
            return cls.CRITICAL

    def __str__(self) -> str:
        """Return display value with icon."""
        return self.value
