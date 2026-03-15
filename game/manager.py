"""
Game Manager — central controller for dart game sessions.
Bridges the detection engine with game logic and the UI.
"""

import logging
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal

from game.player import Player
from game.modes.base import GameMode, TurnState, TurnResult
from game.modes.x01 import X01Game
from game.modes.cricket import CricketGame
from game.modes.freeplay import FreePlayGame
from detection.scorer import DartScore

logger = logging.getLogger(__name__)


class GameState(Enum):
    """Top-level game states."""
    IDLE = "idle"             # No game in progress
    SETUP = "setup"           # Setting up a new game
    PLAYING = "playing"       # Game in progress, waiting for darts
    TURN_REVIEW = "turn_review"  # Reviewing turn scores before next player
    GAME_OVER = "game_over"   # Game finished


class GameManager(QObject):
    """
    Central game state machine.
    
    Signals:
        score_updated: Emitted when a dart is scored
        turn_completed: Emitted when a turn of 3 darts is done
        game_over: Emitted when the game ends
        state_changed: Emitted when game state changes
        bust: Emitted on a bust in X01
    """
    
    score_updated = pyqtSignal(object)      # TurnState
    turn_completed = pyqtSignal(object)     # TurnState
    game_over_signal = pyqtSignal(object)   # Player (winner)
    state_changed = pyqtSignal(str)         # GameState name
    bust_signal = pyqtSignal(object)        # TurnState
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = GameState.IDLE
        self.game_mode: GameMode | None = None
        self.players: list[Player] = []
    
    def create_game(self, mode: str, player_names: list[str],
                    starting_score: int = None):
        """
        Create and start a new game.
        
        Args:
            mode: "501", "301", "701", "cricket", or "freeplay"
            player_names: List of player names
            starting_score: Starting score for X01 modes
        """
        self.players = [
            Player(name=name, id=i)
            for i, name in enumerate(player_names)
        ]
        
        mode_lower = mode.lower().strip()
        
        if mode_lower in ("501", "301", "701", "x01"):
            score = starting_score or int(mode_lower) if mode_lower.isdigit() else 501
            self.game_mode = X01Game(self.players, starting_score=score)
        elif mode_lower == "cricket":
            self.game_mode = CricketGame(self.players)
        elif mode_lower == "freeplay":
            self.game_mode = FreePlayGame(self.players)
        else:
            raise ValueError(f"Unknown game mode: {mode}")
        
        self.state = GameState.PLAYING
        self.state_changed.emit(self.state.value)
        logger.info(f"Game started: {mode} with {len(self.players)} players")
    
    def process_dart(self, score: DartScore) -> TurnState | None:
        """
        Process an incoming dart score from the detection engine.
        Returns the turn state after processing.
        """
        if self.state != GameState.PLAYING or self.game_mode is None:
            return None
        
        turn_state = self.game_mode.process_dart(score)
        
        # Emit appropriate signals
        if turn_state.result == TurnResult.CHECKOUT:
            self.state = GameState.GAME_OVER
            self.game_over_signal.emit(self.game_mode.winner)
            self.state_changed.emit(self.state.value)
            
        elif turn_state.result == TurnResult.BUST:
            self.bust_signal.emit(turn_state)
            # Auto advance turn on bust
            self.game_mode.next_turn()
            
        elif turn_state.result == TurnResult.TURN_COMPLETE:
            self.state = GameState.TURN_REVIEW
            self.turn_completed.emit(turn_state)
            self.state_changed.emit(self.state.value)
        
        self.score_updated.emit(turn_state)
        return turn_state
    
    def confirm_turn(self):
        """
        Confirm the current turn and move to the next player.
        Called after the user reviews their 3-dart turn.
        """
        if self.game_mode is None:
            return
        
        self.game_mode.next_turn()
        self.state = GameState.PLAYING
        self.state_changed.emit(self.state.value)
    
    def undo_last_dart(self) -> bool:
        """Undo the last dart thrown."""
        if self.game_mode is None:
            return False
        return self.game_mode.undo_last_dart()
    
    def manual_score(self, value: int, multiplier: int, sector: int):
        """
        Manually enter a score (for corrections).
        Creates a DartScore and processes it.
        """
        labels = {1: f"S{sector}", 2: f"D{sector}", 3: f"T{sector}"}
        if sector == 25:
            labels = {1: "25", 2: "BULL"}
        
        score = DartScore(
            value=value,
            multiplier=multiplier,
            base_sector=sector,
            label=labels.get(multiplier, str(value)),
            is_bull=(sector == 25),
        )
        return self.process_dart(score)
    
    def get_display_data(self) -> dict | None:
        """Get current game display data."""
        if self.game_mode is None:
            return None
        return self.game_mode.get_display_scores()
    
    def new_leg(self):
        """Start a new leg with the same settings."""
        if self.game_mode is not None:
            self.game_mode.reset()
            self.state = GameState.PLAYING
            self.state_changed.emit(self.state.value)
    
    def end_game(self):
        """End the current game."""
        self.game_mode = None
        self.state = GameState.IDLE
        self.state_changed.emit(self.state.value)
    
    @property
    def current_player(self) -> Player | None:
        if self.game_mode:
            return self.game_mode.current_player
        return None
    
    @property
    def is_playing(self) -> bool:
        return self.state == GameState.PLAYING
