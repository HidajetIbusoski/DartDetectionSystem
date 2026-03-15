"""
Player model for dart games.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Player:
    """Represents a dart player."""
    name: str
    id: int = 0
    
    # Current game state (managed by game mode)
    score: int = 0
    darts_thrown: int = 0
    legs_won: int = 0
    sets_won: int = 0
    
    # Statistics
    total_score: int = 0
    total_darts: int = 0
    highest_checkout: int = 0
    num_180s: int = 0
    num_ton_plus: int = 0  # 100+ in a turn
    doubles_attempted: int = 0
    doubles_hit: int = 0
    
    # Turn tracking
    turn_scores: list = field(default_factory=list)
    
    @property
    def average_per_dart(self) -> float:
        """Average score per dart thrown."""
        if self.total_darts == 0:
            return 0.0
        return self.total_score / self.total_darts
    
    @property
    def three_dart_average(self) -> float:
        """Three-dart average (standard darts statistic)."""
        return self.average_per_dart * 3
    
    @property
    def checkout_percentage(self) -> float:
        """Percentage of doubles hit when attempting checkout."""
        if self.doubles_attempted == 0:
            return 0.0
        return (self.doubles_hit / self.doubles_attempted) * 100
    
    def reset_game(self, starting_score: int = 0):
        """Reset for a new game/leg."""
        self.score = starting_score
        self.darts_thrown = 0
        self.turn_scores.clear()
    
    def reset_stats(self):
        """Full statistics reset."""
        self.total_score = 0
        self.total_darts = 0
        self.highest_checkout = 0
        self.num_180s = 0
        self.num_ton_plus = 0
        self.doubles_attempted = 0
        self.doubles_hit = 0
