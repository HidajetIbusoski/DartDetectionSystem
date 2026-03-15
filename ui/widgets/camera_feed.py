"""
Live camera feed widget.
Displays processed frames from cameras with detection overlays.
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QFont

from config import COLORS


class CameraFeedWidget(QWidget):
    """
    Widget that displays a live camera feed.
    Converts OpenCV frames (numpy arrays) to QPixmap for display.
    """
    
    def __init__(self, camera_index: int = 0, label: str = "Camera",
                 parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Camera label
        self._label = QLabel(label)
        self._label.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
        
        # Video display
        self._display = QLabel()
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 8px;"
        )
        self._display.setMinimumSize(200, 150)
        self._display.setScaledContents(True)
        layout.addWidget(self._display)
        
        # FPS indicator
        self._fps_label = QLabel("-- FPS")
        self._fps_label.setFont(QFont("Inter", 9))
        self._fps_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._fps_label)
        
        # FPS tracking
        self._frame_count = 0
        self._fps_timer = QTimer(self)
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(1000)
    
    def update_frame(self, frame: np.ndarray):
        """Update the display with a new frame."""
        if frame is None:
            return
        
        self._frame_count += 1
        
        # Convert numpy array to QImage
        if len(frame.shape) == 2:
            # Grayscale
            h, w = frame.shape
            qimg = QImage(frame.data, w, h, w, QImage.Format.Format_Grayscale8)
        else:
            # BGR → RGB
            h, w, ch = frame.shape
            rgb = frame[:, :, ::-1].copy()
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qimg)
        self._display.setPixmap(pixmap)
    
    def set_placeholder(self, text: str = "No Camera"):
        """Show placeholder text instead of video."""
        self._display.setText(text)
        self._display.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 8px; "
            f"color: {COLORS['text_muted']}; "
            f"font-size: 14px;"
        )
    
    def _update_fps(self):
        """Update FPS display."""
        self._fps_label.setText(f"{self._frame_count} FPS")
        self._frame_count = 0
