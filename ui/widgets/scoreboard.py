"""
Scoreboard panel widget.
Displays scores, turn info, player stats, and checkout suggestions.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config import COLORS, DARTS_PER_TURN


class ScoreboardWidget(QWidget):
    """
    Score display panel for the game.
    Shows current scores, turn breakdown, averages, and checkout hints.
    """
    
    next_turn_clicked = pyqtSignal()
    undo_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # ── Mode / Title ──
        self._title = QLabel("501")
        self._title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title)
        
        # ── Player Scores ──
        self._players_container = QVBoxLayout()
        self._players_container.setSpacing(12)
        layout.addLayout(self._players_container)
        
        self._player_widgets: list[dict] = []
        
        # ── Current Turn ──
        turn_frame = QFrame()
        turn_frame.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 12px; padding: 16px;"
        )
        turn_layout = QVBoxLayout(turn_frame)
        turn_layout.setSpacing(8)
        
        turn_header = QLabel("CURRENT TURN")
        turn_header.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        turn_header.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        turn_layout.addWidget(turn_header)
        
        # Dart slots (3 slots)
        darts_row = QHBoxLayout()
        darts_row.setSpacing(8)
        self._dart_slots = []
        for i in range(DARTS_PER_TURN):
            slot = QLabel("—")
            slot.setFont(QFont("Inter", 22, QFont.Weight.Bold))
            slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slot.setStyleSheet(
                f"color: {COLORS['text_muted']}; "
                f"background-color: {COLORS['bg_secondary']}; "
                f"border: 1px solid {COLORS['border']}; "
                f"border-radius: 8px; padding: 12px; min-width: 60px;"
            )
            darts_row.addWidget(slot)
            self._dart_slots.append(slot)
        turn_layout.addLayout(darts_row)
        
        # Turn total
        self._turn_total = QLabel("0")
        self._turn_total.setFont(QFont("Inter", 36, QFont.Weight.ExtraBold))
        self._turn_total.setStyleSheet(f"color: {COLORS['accent']}; border: none;")
        self._turn_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        turn_layout.addWidget(self._turn_total)
        
        layout.addWidget(turn_frame)
        
        # ── Checkout Hint ──
        self._checkout_hint = QLabel("")
        self._checkout_hint.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self._checkout_hint.setStyleSheet(
            f"color: {COLORS['warning']}; "
            f"background-color: rgba(255, 165, 2, 0.08); "
            f"border: 1px solid rgba(255, 165, 2, 0.2); "
            f"border-radius: 8px; padding: 10px;"
        )
        self._checkout_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._checkout_hint.hide()
        layout.addWidget(self._checkout_hint)
        
        # ── Message ──
        self._message = QLabel("")
        self._message.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setWordWrap(True)
        self._message.setStyleSheet("border: none;")
        self._message.hide()
        layout.addWidget(self._message)
        
        # ── Buttons ──
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        
        self._undo_btn = QPushButton("↩ Undo")
        self._undo_btn.setProperty("class", "ghost")
        self._undo_btn.clicked.connect(self.undo_clicked.emit)
        buttons_row.addWidget(self._undo_btn)
        
        self._next_btn = QPushButton("Next Player →")
        self._next_btn.setProperty("class", "primary")
        self._next_btn.clicked.connect(self.next_turn_clicked.emit)
        self._next_btn.hide()
        buttons_row.addWidget(self._next_btn)
        
        layout.addLayout(buttons_row)
        
        layout.addStretch()
    
    def set_players(self, player_data: list[dict]):
        """Initialize player score cards."""
        # Clear existing
        for pw in self._player_widgets:
            pw["frame"].deleteLater()
        self._player_widgets.clear()
        
        for i, p in enumerate(player_data):
            frame = QFrame()
            frame.setStyleSheet(
                f"background-color: {COLORS['bg_card']}; "
                f"border: 1px solid {COLORS['border']}; "
                f"border-radius: 12px; padding: 12px;"
            )
            
            fl = QVBoxLayout(frame)
            fl.setSpacing(4)
            
            # Name row
            name_row = QHBoxLayout()
            name_lbl = QLabel(p.get("name", f"Player {i+1}"))
            name_lbl.setFont(QFont("Inter", 13, QFont.Weight.Bold))
            name_lbl.setStyleSheet("border: none;")
            name_row.addWidget(name_lbl)
            
            avg_lbl = QLabel(f"Avg: {p.get('average', 0)}")
            avg_lbl.setFont(QFont("Inter", 11))
            avg_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
            name_row.addWidget(avg_lbl, alignment=Qt.AlignmentFlag.AlignRight)
            fl.addLayout(name_row)
            
            # Score
            score_lbl = QLabel(str(p.get("score", 0)))
            score_lbl.setFont(QFont("Inter", 48, QFont.Weight.ExtraBold))
            score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            score_lbl.setStyleSheet(f"color: {COLORS['accent']}; border: none;")
            fl.addWidget(score_lbl)
            
            self._players_container.addWidget(frame)
            self._player_widgets.append({
                "frame": frame,
                "name": name_lbl,
                "score": score_lbl,
                "average": avg_lbl,
            })
    
    def update_scores(self, data: dict):
        """Update the scoreboard from game display data."""
        if not data:
            return
        
        self._title.setText(data.get("mode", ""))
        
        # Update player scores
        players = data.get("players", [])
        current_idx = data.get("current_player", 0)
        
        for i, p in enumerate(players):
            if i >= len(self._player_widgets):
                break
            
            pw = self._player_widgets[i]
            pw["score"].setText(str(p.get("score", p.get("total_score", 0))))
            pw["average"].setText(f"Avg: {p.get('average', 0)}")
            
            # Highlight active player
            is_active = (i == current_idx)
            border_color = COLORS["accent"] if is_active else COLORS["border"]
            pw["frame"].setStyleSheet(
                f"background-color: {COLORS['bg_card']}; "
                f"border: 1px solid {border_color}; "
                f"border-radius: 12px; padding: 12px;"
            )
        
        # Update turn info
        turn = data.get("current_turn", {})
        darts = turn.get("darts", [])
        
        for i, slot in enumerate(self._dart_slots):
            if i < len(darts):
                d = darts[i]
                slot.setText(d.get("label", ""))
                slot.setStyleSheet(
                    f"color: {COLORS['text_primary']}; "
                    f"background-color: {COLORS['bg_elevated']}; "
                    f"border: 1px solid {COLORS['accent_dim']}; "
                    f"border-radius: 8px; padding: 12px; min-width: 60px;"
                )
            else:
                slot.setText("—")
                slot.setStyleSheet(
                    f"color: {COLORS['text_muted']}; "
                    f"background-color: {COLORS['bg_secondary']}; "
                    f"border: 1px solid {COLORS['border']}; "
                    f"border-radius: 8px; padding: 12px; min-width: 60px;"
                )
        
        self._turn_total.setText(str(turn.get("total", 0)))
        
        # Checkout hint
        hint = data.get("checkout_hint")
        if hint:
            self._checkout_hint.setText(f"🎯 Checkout: {hint}")
            self._checkout_hint.show()
        else:
            self._checkout_hint.hide()
        
        # Next turn button
        has_3_darts = len(darts) >= DARTS_PER_TURN
        self._next_btn.setVisible(has_3_darts and not data.get("game_over", False))
        
        # Game over message
        winner = data.get("winner")
        if winner:
            self._show_message(f"🏆 {winner} wins!", COLORS["accent"])
        
    def show_bust(self, message: str):
        """Show bust notification."""
        self._show_message(f"💥 {message}", COLORS["danger"])
    
    def _show_message(self, text: str, color: str):
        """Show a temporary message."""
        self._message.setText(text)
        self._message.setStyleSheet(f"color: {color}; border: none;")
        self._message.show()
    
    def clear_message(self):
        """Hide the message."""
        self._message.hide()
