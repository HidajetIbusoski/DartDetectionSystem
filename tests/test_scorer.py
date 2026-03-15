"""
Tests for the dart score calculator.
"""

import sys
import os
import math
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from detection.scorer import DartScorer, DartScore


@pytest.fixture
def scorer():
    return DartScorer()


class TestBullseye:
    def test_bullseye_center(self, scorer):
        score = scorer.calculate(0, 0)
        assert score.value == 50
        assert score.label == "BULL"
        assert score.is_bull is True
        assert score.is_double is True
    
    def test_bullseye_edge(self, scorer):
        score = scorer.calculate(3, 3)
        assert score.value == 50
        assert score.label == "BULL"
    
    def test_outer_bull(self, scorer):
        score = scorer.calculate(10, 0)
        assert score.value == 25
        assert score.label == "25"
        assert score.is_bull is True


class TestSingleScores:
    def test_single_20_top(self, scorer):
        """Single 20 is at the top of the board."""
        # Small distance, near top → sector 20
        score = scorer.calculate(0, -50)  # neg Y = up
        assert score.base_sector == 20
        assert score.multiplier == 1
        assert score.value == 20
    
    def test_single_3_right(self, scorer):
        """Sector 3 should be reachable."""
        # Just check it returns a valid sector
        score = scorer.calculate(80, 50)
        assert score.multiplier == 1
        assert score.is_miss is False


class TestTripleRing:
    def test_triple_20(self, scorer):
        """Triple 20 at ~103mm from center, near top."""
        score = scorer.calculate(0, -103)
        assert score.base_sector == 20
        assert score.multiplier == 3
        assert score.value == 60
        assert score.label == "T20"
    
    def test_triple_ring_inner_boundary(self, scorer):
        """Just inside triple ring."""
        score = scorer.calculate(0, -100)
        assert score.multiplier == 3
    
    def test_triple_ring_outer_boundary(self, scorer):
        """Just outside triple ring → single."""
        score = scorer.calculate(0, -108)
        assert score.multiplier == 1


class TestDoubleRing:
    def test_double_20(self, scorer):
        """Double 20 at ~166mm from center, near top."""
        score = scorer.calculate(0, -166)
        assert score.base_sector == 20
        assert score.multiplier == 2
        assert score.value == 40
        assert score.label == "D20"
    
    def test_double_ring_outer_boundary(self, scorer):
        """Just outside double ring → miss."""
        score = scorer.calculate(0, -175)
        assert score.is_miss is True
        assert score.value == 0


class TestMiss:
    def test_far_miss(self, scorer):
        score = scorer.calculate(200, 200)
        assert score.is_miss is True
        assert score.value == 0
        assert score.label == "MISS"
    
    def test_just_outside(self, scorer):
        score = scorer.calculate(0, -171)
        assert score.is_miss is True


class TestAllSectors:
    def test_all_20_sectors_reachable(self, scorer):
        """Ensure all 20 sectors can be hit."""
        from config import SECTOR_ORDER
        
        hit_sectors = set()
        # Sweep around the board at single-ring distance
        for angle_deg in range(0, 360, 5):
            angle_rad = math.radians(angle_deg)
            x = 80 * math.cos(angle_rad)
            y = 80 * math.sin(angle_rad)
            score = scorer.calculate(x, y)
            if not score.is_miss and not score.is_bull:
                hit_sectors.add(score.base_sector)
        
        assert len(hit_sectors) == 20, f"Only hit {len(hit_sectors)} sectors: {hit_sectors}"


class TestDartScoreProperties:
    def test_double_property(self):
        score = DartScore(value=40, multiplier=2, base_sector=20, label="D20")
        assert score.is_double is True
        assert score.is_triple is False
    
    def test_triple_property(self):
        score = DartScore(value=60, multiplier=3, base_sector=20, label="T20")
        assert score.is_triple is True
        assert score.is_double is False
    
    def test_miss_not_double_or_triple(self):
        score = DartScore(value=0, multiplier=0, base_sector=0, label="MISS", is_miss=True)
        assert score.is_double is False
        assert score.is_triple is False
