"""
Abstract base class for game modes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from game.player import Player
from detection.scorer import DartScore


class TurnResult(Enum):
    """Result of processing a dart throw in a turn."""
    SCORED = "scored"          # Normal valid score
    BUST = "bust"              # Score exceeds remaining (501 specific)
    CHECKOUT = "checkout"      # Player finished the game
    INVALID = "invalid"        # Score rejected for some reason
    TURN_COMPLETE = "turn_complete"  # 3 darts thrown, turn is over


@dataclass
class TurnState:
    """Current state of a player's turn."""
    player: Player
    darts_thrown: int = 0
    darts_scores: list = None
    turn_total: int = 0
    result: TurnResult = TurnResult.SCORED
    message: str = ""
    
    def __post_init__(self):
        if self.darts_scores is None:
            self.darts_scores = []


class GameMode(ABC):
    """Abstract base class for all game modes."""
    
    def __init__(self, players: list[Player]):
        self.players = players
        self.current_player_index = 0
        self.current_turn = TurnState(player=players[0])
        self.game_over = False
        self.winner: Player | None = None
        self._turn_history: list[TurnState] = []
    
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]
    
    @property
    def num_players(self) -> int:
        return len(self.players)
    
    @abstractmethod
    def process_dart(self, score: DartScore) -> TurnState:
        """
        Process a single dart throw.
        Returns the updated turn state.
        """
        pass
    
    @abstractmethod
    def get_display_scores(self) -> dict[str, any]:
        """
        Get scores formatted for display.
        Returns a dict with mode-specific display data.
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset the game to initial state."""
        pass
    
    def next_turn(self):
        """Advance to the next player's turn."""
        self._turn_history.append(self.current_turn)
        self.current_player_index = (
            (self.current_player_index + 1) % self.num_players
        )
        self.current_turn = TurnState(player=self.current_player)
    
    def undo_last_dart(self) -> bool:
        """
        Undo the last dart in the current turn.
        Returns True if successful.
        """
        if self.current_turn.darts_thrown > 0 and self.current_turn.darts_scores:
            last_score = self.current_turn.darts_scores.pop()
            self.current_turn.darts_thrown -= 1
            self.current_turn.turn_total -= last_score.value
            return True
        return False
    
    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the name of the game mode."""
        pass
