"""
Free play / practice mode.
No rules — just throw and track your scores.
"""

from game.modes.base import GameMode, TurnState, TurnResult
from game.player import Player
from detection.scorer import DartScore
from config import DARTS_PER_TURN


class FreePlayGame(GameMode):
    """
    Free play / practice mode.
    
    No game rules — just records every throw, tracks totals,
    averages, and grouping data. Good for practice sessions.
    """
    
    def __init__(self, players: list[Player]):
        super().__init__(players)
        
        # Hit history for heatmap
        self.all_throws: list[dict] = []
        self.turn_count = 0
        
        for player in self.players:
            player.reset_game(0)
    
    @property
    def mode_name(self) -> str:
        return "Free Play"
    
    def process_dart(self, score: DartScore) -> TurnState:
        """Process a dart throw in free play."""
        turn = self.current_turn
        
        turn.darts_scores.append(score)
        turn.darts_thrown += 1
        turn.turn_total += score.value
        
        # Update stats
        player = self.current_player
        player.darts_thrown += 1
        player.total_darts += 1
        player.total_score += score.value
        player.score += score.value  # Cumulative total
        
        # Record throw
        self.all_throws.append({
            "player": player.name,
            "score": score.value,
            "label": score.label,
            "sector": score.base_sector,
            "multiplier": score.multiplier,
        })
        
        # Check turn complete
        if turn.darts_thrown >= DARTS_PER_TURN:
            self.turn_count += 1
            
            if turn.turn_total == 180:
                player.num_180s += 1
            elif turn.turn_total >= 100:
                player.num_ton_plus += 1
            
            turn.result = TurnResult.TURN_COMPLETE
            turn.message = f"{turn.turn_total} scored"
            return turn
        
        turn.result = TurnResult.SCORED
        turn.message = f"{score.label} ({score.value})"
        return turn
    
    def get_display_scores(self) -> dict:
        """Get scores for display."""
        return {
            "mode": self.mode_name,
            "players": [
                {
                    "name": p.name,
                    "total_score": p.score,
                    "average": round(p.three_dart_average, 1),
                    "darts": p.darts_thrown,
                    "180s": p.num_180s,
                    "ton_plus": p.num_ton_plus,
                }
                for p in self.players
            ],
            "current_player": self.current_player_index,
            "current_turn": {
                "darts": [
                    {"label": s.label, "value": s.value}
                    for s in self.current_turn.darts_scores
                ],
                "total": self.current_turn.turn_total,
            },
            "total_turns": self.turn_count,
            "total_throws": len(self.all_throws),
        }
    
    def reset(self):
        """Reset free play."""
        self.game_over = False
        self.winner = None
        self.current_player_index = 0
        self.all_throws.clear()
        self.turn_count = 0
        for player in self.players:
            player.reset_game(0)
        self.current_turn = TurnState(player=self.current_player)
