"""
Tests for the SQLite database layer.
"""

import sys
import os
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.stats import Database


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    database = Database(db_path=db_path)
    yield database
    
    database.close()
    os.unlink(db_path)


class TestGameRecording:
    def test_start_game(self, db):
        game_id = db.start_game("501", ["Alice", "Bob"])
        assert game_id is not None
        assert game_id > 0
    
    def test_end_game(self, db):
        game_id = db.start_game("501", ["Alice", "Bob"])
        db.end_game(game_id, winner="Alice", game_data={"mode": "501"})
        
        games = db.get_recent_games()
        assert len(games) == 1
        assert games[0]["winner"] == "Alice"
    
    def test_record_throw(self, db):
        game_id = db.start_game("501", ["Alice"])
        db.record_throw(
            game_id=game_id,
            player_name="Alice",
            turn_number=1,
            dart_number=1,
            score_value=60,
            score_label="T20",
            multiplier=3,
            sector=20,
        )
        
        throws = db.get_game_throws(game_id)
        assert len(throws) == 1
        assert throws[0]["score_value"] == 60
        assert throws[0]["score_label"] == "T20"
    
    def test_multiple_games(self, db):
        g1 = db.start_game("501", ["Alice"])
        g2 = db.start_game("cricket", ["Bob"])
        db.end_game(g1, winner="Alice")
        db.end_game(g2, winner="Bob")
        
        games = db.get_recent_games()
        assert len(games) == 2


class TestPlayerStats:
    def test_update_stats(self, db):
        db.update_player_stats(
            "Alice", won=True, darts=9, score=501,
            checkout=120, num_180s=1
        )
        
        stats = db.get_player_stats("Alice")
        assert stats is not None
        assert stats["games_played"] == 1
        assert stats["games_won"] == 1
        assert stats["num_180s"] == 1
    
    def test_accumulate_stats(self, db):
        db.update_player_stats("Alice", won=True, darts=9, score=300)
        db.update_player_stats("Alice", won=False, darts=12, score=400)
        
        stats = db.get_player_stats("Alice")
        assert stats["games_played"] == 2
        assert stats["games_won"] == 1
        assert stats["total_darts"] == 21
        assert stats["total_score"] == 700
    
    def test_all_player_stats(self, db):
        db.update_player_stats("Alice", won=True, darts=9, score=300)
        db.update_player_stats("Bob", won=False, darts=12, score=200)
        
        all_stats = db.get_all_player_stats()
        assert len(all_stats) == 2


class TestQueries:
    def test_hit_distribution(self, db):
        game_id = db.start_game("freeplay", ["Alice"])
        
        for _ in range(5):
            db.record_throw(game_id, "Alice", 1, 1, 20, "S20", 1, 20)
        for _ in range(3):
            db.record_throw(game_id, "Alice", 1, 2, 60, "T20", 3, 20)
        db.record_throw(game_id, "Alice", 1, 3, 19, "S19", 1, 19)
        
        dist = db.get_player_hit_distribution("Alice")
        assert dist[20] == 8  # 5 + 3 throws at sector 20
        assert dist[19] == 1
    
    def test_clear_all(self, db):
        db.start_game("501", ["Alice"])
        db.update_player_stats("Alice", won=True, darts=9, score=300)
        
        db.clear_all()
        
        assert len(db.get_recent_games()) == 0
        assert len(db.get_all_player_stats()) == 0
