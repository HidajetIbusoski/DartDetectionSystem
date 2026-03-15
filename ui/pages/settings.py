"""
Settings page widget.
Configuration panel for cameras, detection, audio, and display settings.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpinBox, QSlider, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config import (
    COLORS, NUM_CAMERAS, DEFAULT_CAMERA_INDICES,
    CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS,
    DIFF_THRESHOLD, MIN_DART_PIXELS, MAX_DART_PIXELS,
    TAKEOUT_THRESHOLD, TAKEOUT_DELAY,
)


class SettingsWidget(QWidget):
    """
    Settings / configuration panel.
    Allows users to configure cameras, detection thresholds,
    audio, and display preferences.
    """

    settings_changed = pyqtSignal(dict)  # emits updated settings
    calibrate_requested = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Scrollable settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: transparent; }}"
        )

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setProperty("class", "ghost")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)

        title = QLabel("Settings")
        title.setFont(QFont("Inter", 28, QFont.Weight.ExtraBold))
        header.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addStretch()
        layout.addLayout(header)

        # ── Camera Settings ──
        cam_group = self._create_group("📷  Camera Configuration")
        cam_form = QFormLayout()
        cam_form.setSpacing(12)

        # Camera indices
        self._cam_spins = []
        for i in range(NUM_CAMERAS):
            spin = QSpinBox()
            spin.setRange(0, 10)
            spin.setValue(DEFAULT_CAMERA_INDICES[i] if i < len(DEFAULT_CAMERA_INDICES) else i)
            spin.setMinimumWidth(80)
            self._cam_spins.append(spin)
            cam_form.addRow(f"Camera {i+1} Index:", spin)

        # Resolution
        self._res_combo = QComboBox()
        self._res_combo.addItems(["1280×720", "640×480", "1920×1080"])
        cam_form.addRow("Resolution:", self._res_combo)

        # FPS
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(15, 60)
        self._fps_spin.setValue(CAMERA_FPS)
        cam_form.addRow("Frame Rate:", self._fps_spin)

        # Detect cameras button
        detect_btn = QPushButton("🔍  Detect Available Cameras")
        detect_btn.clicked.connect(self._detect_cameras)
        cam_form.addRow("", detect_btn)

        # Calibrate button
        cal_btn = QPushButton("🎯  Calibrate Cameras")
        cal_btn.setProperty("class", "primary")
        cal_btn.clicked.connect(self.calibrate_requested.emit)
        cam_form.addRow("", cal_btn)

        cam_group.layout().addLayout(cam_form)
        layout.addWidget(cam_group)

        # ── Detection Settings ──
        det_group = self._create_group("🔬  Detection Tuning")
        det_form = QFormLayout()
        det_form.setSpacing(12)

        # Diff threshold
        self._diff_thresh = self._create_slider(20, 150, DIFF_THRESHOLD)
        det_form.addRow("Diff Threshold:", self._diff_thresh["layout"])

        # Min dart pixels
        self._min_px = self._create_slider(200, 5000, MIN_DART_PIXELS, step=100)
        det_form.addRow("Min Dart Pixels:", self._min_px["layout"])

        # Max dart pixels
        self._max_px = self._create_slider(2000, 20000, MAX_DART_PIXELS, step=500)
        det_form.addRow("Max Dart Pixels:", self._max_px["layout"])

        # Takeout threshold
        self._takeout_thresh = self._create_slider(5000, 50000, TAKEOUT_THRESHOLD, step=1000)
        det_form.addRow("Takeout Threshold:", self._takeout_thresh["layout"])

        # Takeout delay
        self._takeout_delay = QSpinBox()
        self._takeout_delay.setRange(1, 10)
        self._takeout_delay.setValue(int(TAKEOUT_DELAY))
        self._takeout_delay.setSuffix(" sec")
        det_form.addRow("Takeout Delay:", self._takeout_delay)

        det_group.layout().addLayout(det_form)
        layout.addWidget(det_group)

        # ── Audio Settings ──
        audio_group = self._create_group("🔊  Audio")
        audio_form = QFormLayout()
        audio_form.setSpacing(12)

        self._sound_enabled = QCheckBox("Enable Sound Effects")
        self._sound_enabled.setChecked(True)
        self._sound_enabled.setStyleSheet(f"color: {COLORS['text_primary']};")
        audio_form.addRow(self._sound_enabled)

        self._volume_slider = self._create_slider(0, 100, 70)
        audio_form.addRow("Volume:", self._volume_slider["layout"])

        # Test sound
        test_btn = QPushButton("🔔  Test Sound")
        test_btn.clicked.connect(self._test_sound)
        audio_form.addRow("", test_btn)

        audio_group.layout().addLayout(audio_form)
        layout.addWidget(audio_group)

        # ── Display Settings ──
        disp_group = self._create_group("🖥  Display")
        disp_form = QFormLayout()
        disp_form.setSpacing(12)

        self._show_cameras = QCheckBox("Show Camera Feeds During Game")
        self._show_cameras.setChecked(True)
        self._show_cameras.setStyleSheet(f"color: {COLORS['text_primary']};")
        disp_form.addRow(self._show_cameras)

        self._show_debug = QCheckBox("Show Detection Debug Overlay")
        self._show_debug.setChecked(False)
        self._show_debug.setStyleSheet(f"color: {COLORS['text_primary']};")
        disp_form.addRow(self._show_debug)

        self._fullscreen = QCheckBox("Start in Fullscreen")
        self._fullscreen.setChecked(False)
        self._fullscreen.setStyleSheet(f"color: {COLORS['text_primary']};")
        disp_form.addRow(self._fullscreen)

        disp_group.layout().addLayout(disp_form)
        layout.addWidget(disp_group)

        # ── Data Management ──
        data_group = self._create_group("💾  Data")
        data_form = QFormLayout()
        data_form.setSpacing(12)

        self._clear_stats_btn = QPushButton("🗑  Clear All Statistics")
        self._clear_stats_btn.setProperty("class", "danger")
        self._clear_stats_btn.clicked.connect(self._confirm_clear_stats)
        data_form.addRow("", self._clear_stats_btn)

        self._clear_cal_btn = QPushButton("🗑  Reset Calibration")
        self._clear_cal_btn.setProperty("class", "danger")
        self._clear_cal_btn.clicked.connect(self._confirm_clear_calibration)
        data_form.addRow("", self._clear_cal_btn)

        data_group.layout().addLayout(data_form)
        layout.addWidget(data_group)

        # ── Save Button ──
        save_btn = QPushButton("💾  Save Settings")
        save_btn.setProperty("class", "primary")
        save_btn.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        save_btn.setMinimumHeight(56)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['accent']}; "
            f"color: {COLORS['bg_primary']}; border: none; border-radius: 14px; "
            f"font-size: 16px; font-weight: 700; padding: 14px; }}"
            f"QPushButton:hover {{ background-color: {COLORS['accent_dim']}; }}"
        )
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

        scroll.setWidget(content)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_group(self, title: str) -> QGroupBox:
        """Create a styled group box."""
        group = QGroupBox(title)
        group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        group.setStyleSheet(
            f"QGroupBox {{ "
            f"  background-color: {COLORS['bg_card']}; "
            f"  border: 1px solid {COLORS['border']}; "
            f"  border-radius: 14px; "
            f"  margin-top: 16px; padding: 20px; padding-top: 32px; "
            f"}} "
            f"QGroupBox::title {{ "
            f"  color: {COLORS['text_primary']}; "
            f"  subcontrol-origin: margin; left: 20px; padding: 0 8px; "
            f"}}"
        )
        vl = QVBoxLayout()
        group.setLayout(vl)
        return group

    def _create_slider(self, min_val: int, max_val: int, default: int,
                        step: int = 1) -> dict:
        """Create a slider with value label."""
        wrapper = QHBoxLayout()
        wrapper.setSpacing(12)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.setSingleStep(step)
        slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ "
            f"  background: {COLORS['bg_secondary']}; height: 6px; border-radius: 3px; "
            f"}} "
            f"QSlider::handle:horizontal {{ "
            f"  background: {COLORS['accent']}; width: 18px; height: 18px; "
            f"  margin: -6px 0; border-radius: 9px; "
            f"}} "
            f"QSlider::sub-page:horizontal {{ "
            f"  background: {COLORS['accent_dim']}; border-radius: 3px; "
            f"}}"
        )
        wrapper.addWidget(slider, stretch=1)

        val_label = QLabel(str(default))
        val_label.setMinimumWidth(60)
        val_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        val_label.setStyleSheet(f"color: {COLORS['accent']};")
        val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        wrapper.addWidget(val_label)

        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))

        return {"layout": wrapper, "slider": slider, "label": val_label}

    def _detect_cameras(self):
        """Detect available cameras and show result."""
        from detection.camera import CameraManager
        cameras = CameraManager.detect_cameras()
        if cameras:
            QMessageBox.information(
                self, "Cameras Detected",
                f"Found {len(cameras)} camera(s) at indices: {cameras}"
            )
            # Auto-fill camera indices
            for i, cam_idx in enumerate(cameras[:NUM_CAMERAS]):
                if i < len(self._cam_spins):
                    self._cam_spins[i].setValue(cam_idx)
        else:
            QMessageBox.warning(
                self, "No Cameras",
                "No cameras were detected. Check your USB connections."
            )

    def _test_sound(self):
        """Play a test sound."""
        try:
            from audio.sounds import SoundManager, SoundType
            sm = SoundManager(self)
            sm.volume = self._volume_slider["slider"].value() / 100.0
            sm.play(SoundType.DART_BULL)
        except Exception as e:
            QMessageBox.warning(self, "Audio Error", str(e))

    def _confirm_clear_stats(self):
        """Confirm clearing all statistics."""
        reply = QMessageBox.question(
            self, "Clear Statistics",
            "Are you sure you want to delete all game history and player statistics?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from game.stats import Database
                db = Database()
                db.clear_all()
                db.close()
                QMessageBox.information(self, "Done", "All statistics cleared.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _confirm_clear_calibration(self):
        """Confirm resetting calibration."""
        reply = QMessageBox.question(
            self, "Reset Calibration",
            "Are you sure you want to reset all camera calibrations?\n\nYou will need to recalibrate before playing.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import shutil
            from config import CALIBRATION_DIR
            try:
                if CALIBRATION_DIR.exists():
                    shutil.rmtree(CALIBRATION_DIR)
                    CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
                QMessageBox.information(self, "Done", "Calibration reset.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _save_settings(self):
        """Emit settings changed signal with current values."""
        settings = {
            "camera_indices": [s.value() for s in self._cam_spins],
            "resolution": self._res_combo.currentText(),
            "fps": self._fps_spin.value(),
            "diff_threshold": self._diff_thresh["slider"].value(),
            "min_dart_pixels": self._min_px["slider"].value(),
            "max_dart_pixels": self._max_px["slider"].value(),
            "takeout_threshold": self._takeout_thresh["slider"].value(),
            "takeout_delay": self._takeout_delay.value(),
            "sound_enabled": self._sound_enabled.isChecked(),
            "volume": self._volume_slider["slider"].value() / 100.0,
            "show_cameras": self._show_cameras.isChecked(),
            "show_debug": self._show_debug.isChecked(),
            "fullscreen": self._fullscreen.isChecked(),
        }
        self.settings_changed.emit(settings)

    def get_settings(self) -> dict:
        """Get current settings values."""
        return {
            "camera_indices": [s.value() for s in self._cam_spins],
            "resolution": self._res_combo.currentText(),
            "fps": self._fps_spin.value(),
            "diff_threshold": self._diff_thresh["slider"].value(),
            "min_dart_pixels": self._min_px["slider"].value(),
            "max_dart_pixels": self._max_px["slider"].value(),
            "takeout_threshold": self._takeout_thresh["slider"].value(),
            "takeout_delay": self._takeout_delay.value(),
            "sound_enabled": self._sound_enabled.isChecked(),
            "volume": self._volume_slider["slider"].value() / 100.0,
            "show_cameras": self._show_cameras.isChecked(),
            "show_debug": self._show_debug.isChecked(),
            "fullscreen": self._fullscreen.isChecked(),
        }
