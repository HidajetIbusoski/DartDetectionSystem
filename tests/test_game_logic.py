"""
Tests for game logic — X01, Cricket, and Free Play modes.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.player import Player
from game.modes.x01 import X01Game
from game.modes.cricket import CricketGame
from game.modes.freeplay import FreePlayGame
from game.modes.base import TurnResult
from detection.scorer import DartScore


def make_score(value, multiplier=1, sector=None, label="", is_bull=False):
    """Helper to create DartScore objects for testing."""
    sector = sector or (value // multiplier if multiplier > 0 else 0)
    return DartScore(
        value=value,
        multiplier=multiplier,
        base_sector=sector,
        label=label or f"S{sector}",
        is_bull=is_bull,
    )


# ─── X01 Tests ────────────────────────────────────────────────────────────


class TestX01Basic:
    def test_initial_score(self):
        players = [Player(name="Alice"), Player(name="Bob")]
        game = X01Game(players, starting_score=501)
        assert players[0].score == 501
        assert players[1].score == 501
    
    def test_score_subtraction(self):
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=501)
        
        result = game.process_dart(make_score(20))
        assert players[0].score == 481
        assert result.result == TurnResult.SCORED
    
    def test_three_darts_complete_turn(self):
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=501)
        
        game.process_dart(make_score(20))
        game.process_dart(make_score(20))
        result = game.process_dart(make_score(20))
        
        assert result.result == TurnResult.TURN_COMPLETE
        assert players[0].score == 441
    
    def test_180(self):
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=501)
        
        game.process_dart(make_score(60, multiplier=3, sector=20, label="T20"))
        game.process_dart(make_score(60, multiplier=3, sector=20, label="T20"))
        game.process_dart(make_score(60, multiplier=3, sector=20, label="T20"))
        
        assert players[0].num_180s == 1
        assert players[0].score == 321


class TestX01Bust:
    def test_bust_below_zero(self):
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=10)
        
        result = game.process_dart(make_score(20))
        assert result.result == TurnResult.BUST
        assert players[0].score == 10  # Reverted
    
    def test_bust_leaves_one(self):
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=11)
        
        # Score 10 → leaves 1, which is a bust (can't checkout on 1)
        result = game.process_dart(make_score(10))
        assert result.result == TurnResult.BUST
        assert players[0].score == 11  # Reverted
    
    def test_bust_no_double_finish(self):
        """Reaching 0 without a double = bust."""
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=20)
        
        # Hit single 20 (not double) → reaches 0 but not on a double
        result = game.process_dart(make_score(20, multiplier=1, sector=20))
        assert result.result == TurnResult.BUST


class TestX01Checkout:
    def test_double_checkout(self):
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=40)
        
        result = game.process_dart(
            DartScore(value=40, multiplier=2, base_sector=20, label="D20")
        )
        assert result.result == TurnResult.CHECKOUT
        assert players[0].score == 0
        assert game.game_over is True
        assert game.winner == players[0]
    
    def test_bullseye_checkout(self):
        players = [Player(name="Alice")]
        game = X01Game(players, starting_score=50)
        
        result = game.process_dart(
            DartScore(value=50, multiplier=2, base_sector=25,
                      label="BULL", is_bull=True)
        )
        assert result.result == TurnResult.CHECKOUT
        assert game.game_over is True
    
    def test_checkout_suggestion(self):
        assert X01Game.get_checkout_suggestion(170) == "T20 T20 BULL"
        assert X01Game.get_checkout_suggestion(40) == "D20"
        assert X01Game.get_checkout_suggestion(999) is None


class TestX01MultiPlayer:
    def test_turn_rotation(self):
        players = [Player(name="Alice"), Player(name="Bob")]
        game = X01Game(players, starting_score=501)
        
        # Alice's turn
        game.process_dart(make_score(20))
        game.process_dart(make_score(20))
        game.process_dart(make_score(20))
        
        game.next_turn()
        
        # Now it should be Bob's turn
        assert game.current_player.name == "Bob"


# ─── Cricket Tests ────────────────────────────────────────────────────────


class TestCricket:
    def test_marking_number(self):
        players = [Player(name="Alice"), Player(name="Bob")]
        game = CricketGame(players)
        
        # Hit single 20
        game.process_dart(make_score(20, multiplier=1, sector=20))
        assert game.marks[0][20] == 1
    
    def test_closing_number(self):
        players = [Player(name="Alice"), Player(name="Bob")]
        game = CricketGame(players)
        
        game.process_dart(make_score(20, multiplier=1, sector=20))
        game.process_dart(make_score(20, multiplier=1, sector=20))
        game.process_dart(make_score(20, multiplier=1, sector=20))
        
        assert game.marks[0][20] == 3  # Closed
    
    def test_triple_closes_immediately(self):
        players = [Player(name="Alice"), Player(name="Bob")]
        game = CricketGame(players)
        
        game.process_dart(make_score(60, multiplier=3, sector=20))
        assert game.marks[0][20] == 3


# ─── Free Play Tests ─────────────────────────────────────────────────────


class TestFreePlay:
    def test_cumulative_scoring(self):
        players = [Player(name="Alice")]
        game = FreePlayGame(players)
        
        game.process_dart(make_score(20))
        game.process_dart(make_score(20))
        game.process_dart(make_score(20))
        
        assert players[0].score == 60
        assert len(game.all_throws) == 3
    
    def test_never_game_over(self):
        players = [Player(name="Alice")]
        game = FreePlayGame(players)
        
        for _ in range(30):
            game.process_dart(make_score(20))
            if game.current_turn.darts_thrown == 0:
                pass  # Turn completed auto
        
        assert game.game_over is False


# ─── Player Tests ─────────────────────────────────────────────────────────


class TestPlayer:
    def test_three_dart_average(self):
        p = Player(name="Test")
        p.total_score = 300
        p.total_darts = 10
        assert p.three_dart_average == 90.0
    
    def test_checkout_percentage(self):
        p = Player(name="Test")
        p.doubles_attempted = 10
        p.doubles_hit = 3
        assert p.checkout_percentage == 30.0
    
    def test_reset(self):
        p = Player(name="Test")
        p.score = 100
        p.darts_thrown = 50
        p.reset_game(501)
        assert p.score == 501
        assert p.darts_thrown == 0
