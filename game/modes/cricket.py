"""
Cricket game mode.
"""

from game.modes.base import GameMode, TurnState, TurnResult
from game.player import Player
from detection.scorer import DartScore
from config import DARTS_PER_TURN


# Cricket targets
CRICKET_NUMBERS = [20, 19, 18, 17, 16, 15, 25]  # 25 = Bullseye


class CricketGame(GameMode):
    """
    Cricket game mode.
    
    Rules:
    - Targets: 15, 16, 17, 18, 19, 20, and Bullseye
    - Hit each target 3 times to "close" it
    - Once closed by you but not opponent, you score points
    - Game ends when one player closes all targets and has equal or more points
    """
    
    def __init__(self, players: list[Player]):
        super().__init__(players)
        
        # Track marks per player per number
        # marks[player_index][number] = count (0, 1, 2, 3+)
        self.marks: dict[int, dict[int, int]] = {
            i: {n: 0 for n in CRICKET_NUMBERS}
            for i in range(len(players))
        }
        
        # Points scored
        self.points: dict[int, int] = {i: 0 for i in range(len(players))}
        
        for player in self.players:
            player.reset_game(0)
    
    @property
    def mode_name(self) -> str:
        return "Cricket"
    
    def process_dart(self, score: DartScore) -> TurnState:
        """Process a dart throw in Cricket mode."""
        turn = self.current_turn
        player_idx = self.current_player_index
        
        if self.game_over:
            turn.result = TurnResult.INVALID
            turn.message = "Game is over"
            return turn
        
        turn.darts_scores.append(score)
        turn.darts_thrown += 1
        
        # Update player stats
        self.current_player.darts_thrown += 1
        self.current_player.total_darts += 1
        
        # Check if the dart hits a cricket number
        target = score.base_sector
        if target in CRICKET_NUMBERS:
            hits = score.multiplier
            
            # Bull special: single bull = 1 mark, double bull = 2 marks
            if target == 25:
                hits = 1 if score.value == 25 else 2
            
            current_marks = self.marks[player_idx][target]
            
            if current_marks < 3:
                # Still opening this number
                marks_to_close = 3 - current_marks
                marks_applied = min(hits, marks_to_close)
                extra_marks = hits - marks_applied
                
                self.marks[player_idx][target] = current_marks + marks_applied
                
                # If we've closed it and have extra marks, check for points
                if extra_marks > 0 and not self._is_closed_by_all(target):
                    point_value = target if target != 25 else 25
                    points_earned = point_value * extra_marks
                    self.points[player_idx] += points_earned
                    self.current_player.score = self.points[player_idx]
            
            elif current_marks >= 3 and not self._is_closed_by_all(target):
                # Already closed by us, score points if opponent hasn't closed
                point_value = target if target != 25 else 25
                points_earned = point_value * hits
                self.points[player_idx] += points_earned
                self.current_player.score = self.points[player_idx]
        
        # Check for game over
        if self._check_winner(player_idx):
            self.game_over = True
            self.winner = self.current_player
            self.current_player.legs_won += 1
            turn.result = TurnResult.CHECKOUT
            turn.message = f"{self.current_player.name} wins!"
            return turn
        
        # Check turn complete
        if turn.darts_thrown >= DARTS_PER_TURN:
            turn.result = TurnResult.TURN_COMPLETE
            return turn
        
        turn.result = TurnResult.SCORED
        turn.message = f"{score.label}"
        return turn
    
    def _is_closed_by_all(self, number: int) -> bool:
        """Check if a number is closed by all players."""
        return all(
            self.marks[i][number] >= 3
            for i in range(len(self.players))
        )
    
    def _check_winner(self, player_idx: int) -> bool:
        """Check if a player has won."""
        # Must have all numbers closed
        all_closed = all(
            self.marks[player_idx][n] >= 3
            for n in CRICKET_NUMBERS
        )
        
        if not all_closed:
            return False
        
        # Must have equal or more points than all opponents
        my_points = self.points[player_idx]
        return all(
            my_points >= self.points[i]
            for i in range(len(self.players))
            if i != player_idx
        )
    
    def get_display_scores(self) -> dict:
        """Get scores for Cricket display."""
        return {
            "mode": self.mode_name,
            "numbers": CRICKET_NUMBERS,
            "players": [
                {
                    "name": p.name,
                    "points": self.points[i],
                    "marks": {
                        n: self.marks[i][n]
                        for n in CRICKET_NUMBERS
                    },
                    "darts": p.darts_thrown,
                    "legs": p.legs_won,
                }
                for i, p in enumerate(self.players)
            ],
            "current_player": self.current_player_index,
            "current_turn": {
                "darts": [
                    {"label": s.label, "value": s.value}
                    for s in self.current_turn.darts_scores
                ],
            },
            "game_over": self.game_over,
            "winner": self.winner.name if self.winner else None,
        }
    
    def reset(self):
        """Reset the Cricket game."""
        self.game_over = False
        self.winner = None
        self.current_player_index = 0
        self.marks = {
            i: {n: 0 for n in CRICKET_NUMBERS}
            for i in range(len(self.players))
        }
        self.points = {i: 0 for i in range(len(self.players))}
        for player in self.players:
            player.reset_game(0)
        self.current_turn = TurnState(player=self.current_player)
