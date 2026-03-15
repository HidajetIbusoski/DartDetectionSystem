"""
X01 game mode (501, 301, etc.) with double-out rules.
"""

from game.modes.base import GameMode, TurnState, TurnResult
from game.player import Player
from detection.scorer import DartScore
from config import DEFAULT_X01_START, DARTS_PER_TURN


# Common checkouts for suggestion display
CHECKOUT_MAP = {
    170: "T20 T20 BULL",
    167: "T20 T19 BULL",
    164: "T20 T18 BULL",
    161: "T20 T17 BULL",
    160: "T20 T20 D20",
    158: "T20 T20 D19",
    157: "T20 T19 D20",
    156: "T20 T20 D18",
    155: "T20 T19 D19",
    154: "T20 T18 D20",
    153: "T20 T19 D18",
    152: "T20 T20 D16",
    151: "T20 T17 D20",
    150: "T20 T18 D18",
    149: "T20 T19 D16",
    148: "T20 T16 D20",
    147: "T20 T17 D18",
    146: "T20 T18 D16",
    145: "T20 T15 D20",
    144: "T20 T20 D12",
    143: "T20 T17 D16",
    142: "T20 T14 D20",
    141: "T20 T19 D12",
    140: "T20 T20 D10",
    139: "T20 T13 D20",
    138: "T20 T18 D12",
    137: "T20 T19 D10",
    136: "T20 T20 D8",
    135: "T20 T17 D12",
    134: "T20 T14 D16",
    133: "T20 T19 D8",
    132: "T20 T16 D12",
    131: "T20 T13 D16",
    130: "T20 T18 D8",
    129: "T19 T16 D12",
    128: "T18 T14 D16",
    127: "T20 T17 D8",
    126: "T19 T19 D6",
    125: "T20 T19 D4",  # or 25 T20 D20
    124: "T20 T16 D8",
    123: "T19 T16 D9",
    122: "T18 T20 D4",
    121: "T20 T11 D14",
    120: "T20 S20 D20",
    119: "T19 T12 D13",
    118: "T20 S18 D20",
    117: "T20 S17 D20",
    116: "T20 S16 D20",
    115: "T20 S15 D20",
    114: "T20 S14 D20",
    113: "T20 S13 D20",
    112: "T20 T12 D8",
    111: "T20 S11 D20",
    110: "T20 BULL",
    107: "T19 BULL",
    104: "T18 BULL",
    101: "T17 BULL",
    100: "T20 D20",
    99: "T19 S10 D16",
    98: "T20 D19",
    97: "T19 D20",
    96: "T20 D18",
    95: "T19 D19",
    94: "T18 D20",
    93: "T19 D18",
    92: "T20 D16",
    91: "T17 D20",
    90: "T18 D18",
    89: "T19 D16",
    88: "T16 D20",
    87: "T17 D18",
    86: "T18 D16",
    85: "T15 D20",
    84: "T20 D12",
    83: "T17 D16",
    82: "T14 D20",
    81: "T19 D12",
    80: "T20 D10",
    79: "T13 D20",
    78: "T18 D12",
    77: "T19 D10",
    76: "T20 D8",
    75: "T17 D12",
    74: "T14 D16",
    73: "T19 D8",
    72: "T16 D12",
    71: "T13 D16",
    70: "T18 D8",
    69: "T19 D6",
    68: "T20 D4",
    67: "T17 D8",
    66: "T10 D18",
    65: "T19 D4",
    64: "T16 D8",
    63: "T13 D12",
    62: "T10 D16",
    61: "T15 D8",
    60: "S20 D20",
    59: "S19 D20",
    58: "S18 D20",
    57: "S17 D20",
    56: "S16 D20",
    55: "S15 D20",
    54: "S14 D20",
    53: "S13 D20",
    52: "S12 D20",
    51: "S11 D20",
    50: "BULL",
    49: "S9 D20",
    48: "S8 D20",
    47: "S7 D20",
    46: "S6 D20",
    45: "S13 D16",
    44: "S4 D20",
    43: "S3 D20",
    42: "S10 D16",
    41: "S9 D16",
    40: "D20",
    39: "S7 D16",
    38: "D19",
    36: "D18",
    34: "D17",
    32: "D16",
    30: "D15",
    28: "D14",
    26: "D13",
    24: "D12",
    22: "D11",
    20: "D10",
    18: "D9",
    16: "D8",
    14: "D7",
    12: "D6",
    10: "D5",
    8: "D4",
    6: "D3",
    4: "D2",
    2: "D1",
}


class X01Game(GameMode):
    """
    X01 game mode (501, 301, 701, etc.)
    
    Rules:
    - Each player starts at X01 points
    - Subtract each dart's score from the total
    - Must finish on a double (or bullseye)
    - Going below 0 or to exactly 1 = Bust (turn scores reversed)
    """
    
    def __init__(self, players: list[Player], starting_score: int = None):
        super().__init__(players)
        self.starting_score = starting_score or DEFAULT_X01_START
        
        # Initialize all players
        for player in self.players:
            player.reset_game(self.starting_score)
            player.score = self.starting_score
        
        # Score before current turn (for bust reversal)
        self._score_before_turn: dict[int, int] = {
            i: self.starting_score for i in range(len(players))
        }
    
    @property
    def mode_name(self) -> str:
        return f"{self.starting_score}"
    
    def process_dart(self, score: DartScore) -> TurnState:
        """Process a dart throw in X01 mode."""
        player = self.current_player
        turn = self.current_turn
        
        if self.game_over:
            turn.result = TurnResult.INVALID
            turn.message = "Game is over"
            return turn
        
        # Record the dart
        turn.darts_scores.append(score)
        turn.darts_thrown += 1
        turn.turn_total += score.value
        
        # Update player stats
        player.darts_thrown += 1
        player.total_darts += 1
        player.total_score += score.value
        
        # Calculate remaining score
        remaining = player.score - score.value
        
        # Check for bust
        if remaining < 0 or remaining == 1:
            # Bust! Revert turn scores
            self._bust(turn, player)
            return turn
        
        # Check for checkout (must be on a double or bullseye)
        if remaining == 0:
            if score.is_double or (score.is_bull and score.value == 50):
                # Checkout!
                player.score = 0
                player.doubles_attempted += 1
                player.doubles_hit += 1
                
                if turn.turn_total > player.highest_checkout:
                    player.highest_checkout = turn.turn_total
                
                self.game_over = True
                self.winner = player
                player.legs_won += 1
                
                turn.result = TurnResult.CHECKOUT
                turn.message = f"{player.name} checks out with {turn.turn_total}!"
                return turn
            else:
                # Must finish on a double — bust!
                self._bust(turn, player)
                return turn
        
        # Normal score
        player.score = remaining
        
        # Track doubles attempted (when remaining is <= 170 and on a double segment)
        if score.is_double:
            player.doubles_attempted += 1
            # They didn't check out, so they missed the checkout
        
        # Check for turn complete
        if turn.darts_thrown >= DARTS_PER_TURN:
            # Check for 180
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
    
    def _bust(self, turn: TurnState, player: Player):
        """Handle a bust — revert the turn's scores."""
        player.score = self._score_before_turn[self.current_player_index]
        turn.result = TurnResult.BUST
        turn.message = f"BUST! Score remains at {player.score}"
        
        # Revert statistics for this turn
        for s in turn.darts_scores:
            player.total_score -= s.value
    
    def next_turn(self):
        """Advance to next turn, saving pre-turn score."""
        super().next_turn()
        self._score_before_turn[self.current_player_index] = (
            self.current_player.score
        )
    
    def get_display_scores(self) -> dict:
        """Get scores for UI display."""
        checkout_hint = self.get_checkout_suggestion(self.current_player.score)
        
        return {
            "mode": self.mode_name,
            "players": [
                {
                    "name": p.name,
                    "score": p.score,
                    "average": round(p.three_dart_average, 1),
                    "darts": p.darts_thrown,
                    "legs": p.legs_won,
                    "checkout_pct": round(p.checkout_percentage, 1),
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
            "checkout_hint": checkout_hint,
            "game_over": self.game_over,
            "winner": self.winner.name if self.winner else None,
        }
    
    @staticmethod
    def get_checkout_suggestion(remaining: int) -> str | None:
        """Get checkout suggestion for the remaining score."""
        return CHECKOUT_MAP.get(remaining)
    
    def reset(self):
        """Reset the game."""
        self.game_over = False
        self.winner = None
        self.current_player_index = 0
        for i, player in enumerate(self.players):
            player.reset_game(self.starting_score)
            player.score = self.starting_score
            self._score_before_turn[i] = self.starting_score
        self.current_turn = TurnState(player=self.current_player)
