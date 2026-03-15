"""
Score calculation module.
Converts a dart position (x, y) on the dartboard to a score using polar coordinates.
"""

import math
import numpy as np
from dataclasses import dataclass

from config import (
    SECTOR_ORDER, NUM_SECTORS, SECTOR_ANGLE,
    BULLSEYE_RADIUS_MM, OUTER_BULL_RADIUS_MM,
    TRIPLE_RING_INNER_RADIUS_MM, TRIPLE_RING_OUTER_RADIUS_MM,
    DOUBLE_RING_INNER_RADIUS_MM, DOUBLE_RING_OUTER_RADIUS_MM,
)


@dataclass
class DartScore:
    """Represents the score of a single dart throw."""
    value: int                # Numeric score value (0-60)
    multiplier: int           # 1=single, 2=double, 3=triple
    base_sector: int          # The base sector number (1-20, 25 for bull)
    label: str                # Human-readable label (e.g., "T20", "D16", "BULL")
    is_bull: bool = False     # True if bullseye or outer bull
    is_miss: bool = False     # True if outside the board
    
    @property
    def is_double(self) -> bool:
        return self.multiplier == 2
    
    @property
    def is_triple(self) -> bool:
        return self.multiplier == 3


class DartScorer:
    """
    Calculates dart scores from (x, y) coordinates on the dartboard.
    Coordinates are in mm relative to the board center (0, 0).
    """
    
    def __init__(self):
        self.sector_order = SECTOR_ORDER
        self.num_sectors = NUM_SECTORS
        self.sector_angle_rad = math.radians(SECTOR_ANGLE)
        
        # Radii boundaries
        self.bullseye_r = BULLSEYE_RADIUS_MM
        self.outer_bull_r = OUTER_BULL_RADIUS_MM
        self.triple_inner_r = TRIPLE_RING_INNER_RADIUS_MM
        self.triple_outer_r = TRIPLE_RING_OUTER_RADIUS_MM
        self.double_inner_r = DOUBLE_RING_INNER_RADIUS_MM
        self.double_outer_r = DOUBLE_RING_OUTER_RADIUS_MM
    
    def calculate(self, x: float, y: float) -> DartScore:
        """
        Calculate the score for a dart at position (x, y) in mm.
        Origin (0, 0) is the center of the dartboard.
        Positive X is right, positive Y is down.
        """
        # Convert to polar coordinates
        distance = math.sqrt(x ** 2 + y ** 2)
        angle = math.atan2(-y, x)  # Negate y because screen Y is inverted
        
        # Normalize angle to [0, 2π)
        if angle < 0:
            angle += 2 * math.pi
        
        # Check for miss (outside the board)
        if distance > self.double_outer_r:
            return DartScore(
                value=0, multiplier=0, base_sector=0,
                label="MISS", is_miss=True
            )
        
        # Check for bullseye
        if distance <= self.bullseye_r:
            return DartScore(
                value=50, multiplier=2, base_sector=25,
                label="BULL", is_bull=True
            )
        
        # Check for outer bull
        if distance <= self.outer_bull_r:
            return DartScore(
                value=25, multiplier=1, base_sector=25,
                label="25", is_bull=True
            )
        
        # Determine sector
        # Sector 20 is at the top (12 o'clock). Angle 0 is at 3 o'clock.
        # Rotate angle so that the middle of sector 20 is at angle 0
        # Sector 20 center is at 90 degrees (π/2) from the 3 o'clock reference
        adjusted_angle = angle - math.pi / 2 + self.sector_angle_rad / 2
        if adjusted_angle < 0:
            adjusted_angle += 2 * math.pi
        
        sector_index = int(adjusted_angle / self.sector_angle_rad) % self.num_sectors
        base_score = self.sector_order[sector_index]
        
        # Determine ring/multiplier
        if distance <= self.triple_inner_r:
            # Inner single
            multiplier = 1
            label = f"S{base_score}"
        elif distance <= self.triple_outer_r:
            # Triple
            multiplier = 3
            label = f"T{base_score}"
        elif distance <= self.double_inner_r:
            # Outer single
            multiplier = 1
            label = f"S{base_score}"
        elif distance <= self.double_outer_r:
            # Double
            multiplier = 2
            label = f"D{base_score}"
        else:
            # Miss (shouldn't reach here, handled above)
            return DartScore(
                value=0, multiplier=0, base_sector=0,
                label="MISS", is_miss=True
            )
        
        return DartScore(
            value=base_score * multiplier,
            multiplier=multiplier,
            base_sector=base_score,
            label=label,
        )
    
    def calculate_from_pixels(self, x: float, y: float,
                               center_x: float, center_y: float,
                               pixels_per_mm: float) -> DartScore:
        """
        Calculate score from pixel coordinates.
        Converts pixel position to mm relative to board center first.
        """
        mm_x = (x - center_x) / pixels_per_mm
        mm_y = (y - center_y) / pixels_per_mm
        return self.calculate(mm_x, mm_y)


# Module-level convenience instance
scorer = DartScorer()


def calculate_score(x: float, y: float) -> DartScore:
    """Convenience function to calculate score from mm coordinates."""
    return scorer.calculate(x, y)
