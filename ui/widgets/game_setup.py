"""
Game setup widget — lets users choose game mode, players, and settings.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QSpinBox, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config import COLORS, MAX_PLAYERS


class GameSetupWidget(QWidget):
    """
    Game setup screen for choosing mode, players, and settings.
    """
    
    start_game = pyqtSignal(str, list, int)  # mode, player_names, starting_score
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        layout.setContentsMargins(60, 40, 60, 40)
        
        # ── Title ──
        title = QLabel("New Game")
        title.setFont(QFont("Inter", 36, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        subtitle = QLabel("Choose your game mode and add players")
        subtitle.setFont(QFont("Inter", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(subtitle)
        
        layout.addSpacing(16)
        
        # ── Game Mode ──
        mode_frame = QFrame()
        mode_frame.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 16px; padding: 24px;"
        )
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(12)
        
        mode_label = QLabel("GAME MODE")
        mode_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        mode_label.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        mode_layout.addWidget(mode_label)
        
        # Mode buttons
        mode_btn_row = QHBoxLayout()
        mode_btn_row.setSpacing(8)
        self._mode_buttons = {}
        
        for mode in ["501", "301", "Cricket", "Free Play"]:
            btn = QPushButton(mode)
            btn.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            btn.setMinimumHeight(56)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, m=mode: self._select_mode(m))
            mode_btn_row.addWidget(btn)
            self._mode_buttons[mode] = btn
        
        self._mode_buttons["501"].setChecked(True)
        self._mode_buttons["501"].setProperty("class", "primary")
        self._selected_mode = "501"
        
        mode_layout.addLayout(mode_btn_row)
        
        # Starting score (for x01)
        self._score_row = QHBoxLayout()
        score_label = QLabel("Starting Score:")
        score_label.setStyleSheet(f"border: none; color: {COLORS['text_secondary']};")
        self._score_row.addWidget(score_label)
        
        self._score_spin = QSpinBox()
        self._score_spin.setRange(101, 1001)
        self._score_spin.setValue(501)
        self._score_spin.setSingleStep(100)
        self._score_spin.setMinimumWidth(100)
        self._score_row.addWidget(self._score_spin)
        self._score_row.addStretch()
        
        mode_layout.addLayout(self._score_row)
        layout.addWidget(mode_frame)
        
        # ── Players ──
        players_frame = QFrame()
        players_frame.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 16px; padding: 24px;"
        )
        players_layout = QVBoxLayout(players_frame)
        players_layout.setSpacing(12)
        
        players_label = QLabel("PLAYERS")
        players_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        players_label.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        players_layout.addWidget(players_label)
        
        self._player_inputs: list[QLineEdit] = []
        for i in range(MAX_PLAYERS):
            row = QHBoxLayout()
            row.setSpacing(8)
            
            num_label = QLabel(f"{i+1}")
            num_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            num_label.setStyleSheet(
                f"color: {COLORS['accent']}; border: none; min-width: 24px;"
            )
            row.addWidget(num_label)
            
            inp = QLineEdit()
            inp.setPlaceholderText(f"Player {i+1}")
            if i == 0:
                inp.setText("Player 1")
            row.addWidget(inp)
            
            self._player_inputs.append(inp)
            players_layout.addLayout(row)
            
            # Hide extra player slots initially
            if i >= 2:
                inp.hide()
                num_label.hide()
                inp._num_label = num_label
            else:
                inp._num_label = num_label
        
        # Add/remove player buttons
        pr = QHBoxLayout()
        self._add_player_btn = QPushButton("+ Add Player")
        self._add_player_btn.setProperty("class", "ghost")
        self._add_player_btn.clicked.connect(self._add_player)
        pr.addWidget(self._add_player_btn)
        pr.addStretch()
        players_layout.addLayout(pr)
        
        self._visible_players = 2
        
        layout.addWidget(players_frame)
        
        # ── Start Button ──
        self._start_btn = QPushButton("🎯  Start Game")
        self._start_btn.setProperty("class", "primary")
        self._start_btn.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self._start_btn.setMinimumHeight(64)
        self._start_btn.clicked.connect(self._on_start)
        self._start_btn.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['accent']}; "
            f"color: {COLORS['bg_primary']}; border: none; border-radius: 16px; "
            f"font-size: 18px; font-weight: 700; padding: 16px; }}"
            f"QPushButton:hover {{ background-color: {COLORS['accent_dim']}; }}"
        )
        layout.addWidget(self._start_btn)
        
        layout.addStretch()
    
    def _select_mode(self, mode: str):
        """Handle mode selection."""
        self._selected_mode = mode
        for m, btn in self._mode_buttons.items():
            if m == mode:
                btn.setChecked(True)
                btn.setProperty("class", "primary")
            else:
                btn.setChecked(False)
                btn.setProperty("class", "")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # Show/hide starting score for x01 modes
        is_x01 = mode in ("501", "301")
        self._score_spin.setVisible(is_x01)
        
        if mode == "501":
            self._score_spin.setValue(501)
        elif mode == "301":
            self._score_spin.setValue(301)
    
    def _add_player(self):
        """Show the next player input."""
        if self._visible_players < MAX_PLAYERS:
            inp = self._player_inputs[self._visible_players]
            inp.show()
            inp._num_label.show()
            self._visible_players += 1
        
        if self._visible_players >= MAX_PLAYERS:
            self._add_player_btn.hide()
    
    def _on_start(self):
        """Emit start game signal."""
        names = []
        for i in range(self._visible_players):
            name = self._player_inputs[i].text().strip()
            if not name:
                name = f"Player {i+1}"
            names.append(name)
        
        mode = self._selected_mode.lower()
        if mode == "free play":
            mode = "freeplay"
        
        score = self._score_spin.value()
        self.start_game.emit(mode, names, score)
