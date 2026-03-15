"""
Main application window and page management.
"""

import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QShortcut, QKeySequence

from config import (
    WINDOW_TITLE, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    COLORS, NUM_CAMERAS
)
from ui.theme import get_stylesheet
from ui.widgets.dartboard import DartboardWidget
from ui.widgets.camera_feed import CameraFeedWidget
from ui.widgets.scoreboard import ScoreboardWidget
from ui.widgets.game_setup import GameSetupWidget
from ui.widgets.calibration_wizard import CalibrationWizard
from ui.pages.settings import SettingsWidget
from detection.camera import CameraManager
from detection.calibration import Calibration
from detection.detector import DartDetector, DetectionEvent
from game.manager import GameManager, GameState
from game.modes.base import TurnResult
from game.stats import Database
from audio.sounds import SoundManager, SoundType
from detection.scorer import DartScore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window with page stack navigation.
    
    Pages:
    - Home: Game setup / mode selector
    - Play: Main gameplay with dartboard, camera, and scoreboard
    - Calibrate: Camera calibration wizard
    - Settings: Configuration panel
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setStyleSheet(get_stylesheet())
        
        # ── Core systems ──
        self.camera_manager = CameraManager()
        self.calibration = Calibration()
        self.detector = DartDetector(self.calibration)
        self.game_manager = GameManager(self)
        self.sound_manager = SoundManager(self)
        self.database = Database()
        self._current_game_id: int | None = None
        self._turn_number = 0
        
        # Try loading existing calibration
        self.calibration.load()
        
        # ── Page stack ──
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        
        # Create pages
        self._home_page = self._create_home_page()
        self._play_page = self._create_play_page()
        self._calibrate_page = self._create_calibrate_page()
        self._settings_page = self._create_settings_page()
        
        self._stack.addWidget(self._home_page)       # Index 0
        self._stack.addWidget(self._play_page)        # Index 1
        self._stack.addWidget(self._calibrate_page)   # Index 2
        self._stack.addWidget(self._settings_page)    # Index 3
        
        # ── Connect signals ──
        self.game_manager.score_updated.connect(self._on_score_updated)
        self.game_manager.turn_completed.connect(self._on_turn_completed)
        self.game_manager.game_over_signal.connect(self._on_game_over)
        self.game_manager.bust_signal.connect(self._on_bust)
        
        # ── Detection loop ──
        self._detection_timer = QTimer(self)
        self._detection_timer.timeout.connect(self._run_detection)
        self._detection_active = False
        
        # ── Camera feed update ──
        self.camera_manager.on_frame(self._on_camera_frame)
        
        # ── Keyboard shortcuts ──
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self._show_home)
        
        # Show home
        self._stack.setCurrentIndex(0)
    
    # ──────────────────────────────────────────────────────
    # PAGE: Home
    # ──────────────────────────────────────────────────────
    
    def _create_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(24, 16, 24, 16)
        
        logo = QLabel("🎯 OfflineDarts")
        logo.setFont(QFont("Inter", 20, QFont.Weight.ExtraBold))
        logo.setStyleSheet(f"color: {COLORS['accent']};")
        top_bar.addWidget(logo)
        
        top_bar.addStretch()
        
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self._show_settings)
        top_bar.addWidget(settings_btn)
        
        calibrate_btn = QPushButton("📷 Calibrate")
        calibrate_btn.clicked.connect(self._show_calibrate)
        top_bar.addWidget(calibrate_btn)
        
        layout.addLayout(top_bar)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)
        
        # Game setup
        self._game_setup = GameSetupWidget()
        self._game_setup.start_game.connect(self._start_game)
        layout.addWidget(self._game_setup)
        
        return page
    
    # ──────────────────────────────────────────────────────
    # PAGE: Play
    # ──────────────────────────────────────────────────────
    
    def _create_play_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(16, 12, 16, 12)
        
        back_btn = QPushButton("← Back")
        back_btn.setProperty("class", "ghost")
        back_btn.clicked.connect(self._show_home)
        top_bar.addWidget(back_btn)
        
        self._play_title = QLabel("501")
        self._play_title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self._play_title.setStyleSheet(f"color: {COLORS['accent']};")
        top_bar.addWidget(self._play_title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        new_leg_btn = QPushButton("New Leg")
        new_leg_btn.clicked.connect(self._new_leg)
        top_bar.addWidget(new_leg_btn)
        
        layout.addLayout(top_bar)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)
        
        # Main content: Dartboard + Cameras | Scoreboard
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        
        # Left: Dartboard + Camera feeds
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(16, 16, 8, 16)
        left_layout.setSpacing(12)
        
        # Dartboard
        self._dartboard = DartboardWidget()
        self._dartboard.setMinimumSize(400, 400)
        self._dartboard.segment_clicked.connect(self._on_manual_score)
        left_layout.addWidget(self._dartboard, stretch=3)
        
        # Camera feeds row
        cam_row = QHBoxLayout()
        cam_row.setSpacing(8)
        self._camera_feeds: list[CameraFeedWidget] = []
        for i in range(NUM_CAMERAS):
            feed = CameraFeedWidget(camera_index=i, label=f"Cam {i+1}")
            feed.setMaximumHeight(180)
            cam_row.addWidget(feed)
            self._camera_feeds.append(feed)
        left_layout.addLayout(cam_row, stretch=1)
        
        splitter.addWidget(left_widget)
        
        # Right: Scoreboard
        self._scoreboard = ScoreboardWidget()
        self._scoreboard.next_turn_clicked.connect(self._next_turn)
        self._scoreboard.undo_clicked.connect(self._undo_dart)
        splitter.addWidget(self._scoreboard)
        
        splitter.setSizes([700, 350])
        layout.addWidget(splitter)
        
        return page
    
    # ──────────────────────────────────────────────────────
    # PAGE: Calibrate
    # ──────────────────────────────────────────────────────
    
    def _create_calibrate_page(self) -> QWidget:
        self._calibration_wizard = CalibrationWizard()
        self._calibration_wizard.calibration_complete.connect(
            self._on_calibration_complete
        )
        self._calibration_wizard.cancelled.connect(self._show_home)
        return self._calibration_wizard
    
    # ──────────────────────────────────────────────────────
    # PAGE: Settings
    # ──────────────────────────────────────────────────────
    
    def _create_settings_page(self) -> QWidget:
        self._settings_widget = SettingsWidget()
        self._settings_widget.settings_changed.connect(self._apply_settings)
        self._settings_widget.calibrate_requested.connect(self._show_calibrate)
        self._settings_widget.back_requested.connect(self._show_home)
        return self._settings_widget
    
    # ──────────────────────────────────────────────────────
    # Navigation
    # ──────────────────────────────────────────────────────
    
    def _show_home(self):
        self._stop_detection()
        self._stack.setCurrentIndex(0)
    
    def _show_play(self):
        self._stack.setCurrentIndex(1)
    
    def _show_calibrate(self):
        self._calibration_wizard.reset()
        self._start_cameras()
        self._stack.setCurrentIndex(2)
    
    def _show_settings(self):
        self._stack.setCurrentIndex(3)
    
    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()
    
    # ──────────────────────────────────────────────────────
    # Game Control
    # ──────────────────────────────────────────────────────
    
    @pyqtSlot(str, list, int)
    def _start_game(self, mode: str, player_names: list, starting_score: int):
        """Start a new game."""
        try:
            self.game_manager.create_game(mode, player_names, starting_score)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to start game: {e}")
            return
        
        # Record game start in database
        self._current_game_id = self.database.start_game(mode, player_names)
        self._turn_number = 0
        
        # Update UI
        display = self.game_manager.get_display_data()
        if display:
            self._play_title.setText(display.get("mode", mode))
            self._scoreboard.set_players(display.get("players", []))
            self._scoreboard.update_scores(display)
        
        self._dartboard.clear_hits()
        self._show_play()
        
        # Start cameras and detection
        self._start_cameras()
        self._start_detection()
        
        logger.info(f"Game started: {mode}")
    
    def _new_leg(self):
        """Start a new leg."""
        self.game_manager.new_leg()
        self._dartboard.clear_hits()
        self._scoreboard.clear_message()
        display = self.game_manager.get_display_data()
        if display:
            self._scoreboard.update_scores(display)
        self._start_detection()
    
    def _next_turn(self):
        """Advance to next player's turn."""
        self.game_manager.confirm_turn()
        self._dartboard.clear_hits()
        self._scoreboard.clear_message()
        display = self.game_manager.get_display_data()
        if display:
            self._scoreboard.update_scores(display)
        
        # Set new reference frames
        frames = self.camera_manager.get_all_frames()
        if frames:
            self.detector.set_all_reference_frames(frames)
    
    def _undo_dart(self):
        """Undo the last dart."""
        if self.game_manager.undo_last_dart():
            display = self.game_manager.get_display_data()
            if display:
                self._scoreboard.update_scores(display)
            if self._dartboard._hits:
                self._dartboard._hits.pop()
                self._dartboard.update()
    
    @pyqtSlot(object)
    def _on_manual_score(self, score: DartScore):
        """Handle manual score from clicking the dartboard."""
        if not self.game_manager.is_playing:
            return
        
        self.game_manager.process_dart(score)
        self._dartboard.add_hit(0, 0, score)  # Center marker for manual
        self._play_sound_for_score(score)
        self._record_throw(score)
        
        display = self.game_manager.get_display_data()
        if display:
            self._scoreboard.update_scores(display)
    
    # ──────────────────────────────────────────────────────
    # Detection
    # ──────────────────────────────────────────────────────
    
    def _start_cameras(self):
        """Start camera capture if not already running."""
        if not self.camera_manager.is_running:
            self.camera_manager.start()
            # Wait briefly for cameras to initialize, then set reference
            QTimer.singleShot(1000, self._set_initial_reference)
    
    def _set_initial_reference(self):
        """Set the initial reference frames from current camera feeds."""
        frames = self.camera_manager.get_all_frames()
        if frames:
            self.detector.set_all_reference_frames(frames)
            logger.info("Initial reference frames set")
    
    def _start_detection(self):
        """Start the detection loop."""
        if not self._detection_active:
            self._detection_active = True
            self._detection_timer.start(100)  # 10 Hz detection loop
    
    def _stop_detection(self):
        """Stop the detection loop."""
        self._detection_active = False
        self._detection_timer.stop()
    
    def _run_detection(self):
        """Single detection cycle — called by timer."""
        if not self.game_manager.is_playing:
            return
        
        frames = self.camera_manager.get_all_frames()
        if not frames:
            return
        
        result = self.detector.detect_from_frames(frames)
        
        if result.event == DetectionEvent.DART_DETECTED and result.score:
            # Process the detected dart
            turn_state = self.game_manager.process_dart(result.score)
            
            # Play sound effect
            self._play_sound_for_score(result.score)
            
            # Record throw in database
            self._record_throw(result.score)
            
            # Update dartboard visualization
            if result.board_position_mm:
                x, y = result.board_position_mm
                self._dartboard.add_hit(x, y, result.score)
            
            # Update scoreboard
            display = self.game_manager.get_display_data()
            if display:
                self._scoreboard.update_scores(display)
            
            # Update reference frames (board now has a new dart)
            self.detector.update_reference_after_hit(frames)
            
            logger.info(f"Dart detected: {result.score.label} ({result.score.value})")
        
        elif result.event == DetectionEvent.TAKEOUT:
            # Darts removed — set new reference after delay
            self._dartboard.clear_hits()
            QTimer.singleShot(3000, self._set_initial_reference)
            logger.info("Takeout detected")
    
    def _on_camera_frame(self, camera_index: int, frame):
        """Update camera feed widgets and calibration wizard."""
        if camera_index < len(self._camera_feeds):
            self._camera_feeds[camera_index].update_frame(frame)
        
        # Also feed to calibration wizard if active
        if self._stack.currentIndex() == 2:
            self._calibration_wizard.set_camera_frame(camera_index, frame)
    
    # ──────────────────────────────────────────────────────
    # Signal handlers
    # ──────────────────────────────────────────────────────
    
    @pyqtSlot(object)
    def _on_score_updated(self, turn_state):
        display = self.game_manager.get_display_data()
        if display:
            self._scoreboard.update_scores(display)
    
    @pyqtSlot(object)
    def _on_turn_completed(self, turn_state):
        self._turn_number += 1
        self.sound_manager.play(SoundType.TURN_COMPLETE)
        
        # Check for 180
        if turn_state.turn_total == 180:
            self.sound_manager.play(SoundType.ONE_EIGHTY)
        
        display = self.game_manager.get_display_data()
        if display:
            self._scoreboard.update_scores(display)
    
    @pyqtSlot(object)
    def _on_game_over(self, winner):
        self._stop_detection()
        self.sound_manager.play(SoundType.GAME_OVER)
        
        # Record in database
        if self._current_game_id and winner:
            self.database.end_game(
                self._current_game_id,
                winner=winner.name,
                game_data=self.game_manager.get_display_data()
            )
            # Update player stats
            for p in self.game_manager.players:
                self.database.update_player_stats(
                    player_name=p.name,
                    won=(p == winner),
                    darts=p.darts_thrown,
                    score=p.total_score,
                    checkout=p.highest_checkout,
                    num_180s=p.num_180s,
                    ton_plus=p.num_ton_plus,
                    doubles_att=p.doubles_attempted,
                    doubles_hit=p.doubles_hit,
                    three_dart_avg=p.three_dart_average,
                )
        
        display = self.game_manager.get_display_data()
        if display:
            self._scoreboard.update_scores(display)
    
    @pyqtSlot(object)
    def _on_bust(self, turn_state):
        self.sound_manager.play(SoundType.BUST)
        self._scoreboard.show_bust(turn_state.message)
        self._dartboard.clear_hits()
    
    @pyqtSlot(list)
    def _on_calibration_complete(self, calibrations):
        """Handle completed calibration."""
        for cal in calibrations:
            self.calibration.set_calibration_points(
                cal["camera_index"], cal["points"]
            )
        
        self.calibration.save()
        logger.info("Calibration complete and saved")
        
        QMessageBox.information(
            self, "Calibration Complete",
            "All cameras have been calibrated successfully!"
        )
        self._show_home()
    
    @pyqtSlot(dict)
    def _apply_settings(self, settings: dict):
        """Apply changed settings."""
        # Audio
        self.sound_manager.enabled = settings.get("sound_enabled", True)
        self.sound_manager.volume = settings.get("volume", 0.7)
        
        # Camera indices
        new_indices = settings.get("camera_indices")
        if new_indices and new_indices != self.camera_manager.camera_indices:
            self.camera_manager.stop()
            self.camera_manager = CameraManager(new_indices)
            self.camera_manager.on_frame(self._on_camera_frame)
        
        logger.info(f"Settings applied: {settings}")
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self._show_home()
    
    # ──────────────────────────────────────────────────────
    # Sound & Database helpers
    # ──────────────────────────────────────────────────────
    
    def _play_sound_for_score(self, score: DartScore):
        """Play the appropriate sound for a dart score."""
        self.sound_manager.play_for_score(
            value=score.value,
            multiplier=score.multiplier,
            is_bull=score.is_bull,
            is_miss=score.is_miss,
        )
    
    def _record_throw(self, score: DartScore):
        """Record a dart throw in the database."""
        if self._current_game_id and self.game_manager.current_player:
            turn = self.game_manager.game_mode.current_turn if self.game_manager.game_mode else None
            dart_num = turn.darts_thrown if turn else 0
            self.database.record_throw(
                game_id=self._current_game_id,
                player_name=self.game_manager.current_player.name,
                turn_number=self._turn_number,
                dart_number=dart_num,
                score_value=score.value,
                score_label=score.label,
                multiplier=score.multiplier,
                sector=score.base_sector,
            )
    
    # ──────────────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────────────
    
    def closeEvent(self, event):
        """Clean up on close."""
        self._stop_detection()
        self.camera_manager.stop()
        self.database.close()
        super().closeEvent(event)
