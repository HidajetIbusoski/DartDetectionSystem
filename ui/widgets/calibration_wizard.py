"""
Calibration wizard widget.
Guides the user through the 4-point calibration process for each camera.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QFont, QImage, QPixmap, QPainter, QPen, QColor

from config import COLORS, NUM_CAMERAS, NUM_CALIBRATION_POINTS


class CalibrationClickLabel(QLabel):
    """QLabel that captures click positions for calibration."""
    
    point_clicked = pyqtSignal(float, float)  # x, y in image coordinates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._points: list[tuple[float, float]] = []
        self._scale_x = 1.0
        self._scale_y = 1.0
    
    def set_frame(self, frame: np.ndarray):
        """Display a camera frame and enable clicking."""
        if frame is None:
            return
        
        if len(frame.shape) == 2:
            h, w = frame.shape
            qimg = QImage(frame.data, w, h, w, QImage.Format.Format_Grayscale8)
        else:
            h, w, ch = frame.shape
            rgb = frame[:, :, ::-1].copy()
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qimg)
        
        # Calculate scale factors
        self._scale_x = w / self.width() if self.width() > 0 else 1
        self._scale_y = h / self.height() if self.height() > 0 else 1
        
        # Draw existing points
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for i, (px, py) in enumerate(self._points):
            # Crosshair
            pen = QPen(QColor(COLORS["accent"]), 2)
            painter.setPen(pen)
            painter.drawLine(QPointF(px - 15, py), QPointF(px + 15, py))
            painter.drawLine(QPointF(px, py - 15), QPointF(px, py + 15))
            
            # Circle
            painter.drawEllipse(QPointF(px, py), 8, 8)
            
            # Label
            font = QFont("Inter", 12, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(QPointF(px + 12, py - 12), str(i + 1))
        
        painter.end()
        self.setPixmap(pixmap.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert widget coordinates to image coordinates
            x = event.position().x() * self._scale_x
            y = event.position().y() * self._scale_y
            self._points.append((x, y))
            self.point_clicked.emit(x, y)
        super().mousePressEvent(event)
    
    def clear_points(self):
        self._points.clear()
    
    @property
    def points(self) -> list[tuple[float, float]]:
        return self._points.copy()


class CalibrationWizard(QWidget):
    """
    Step-by-step calibration wizard.
    Guides the user to click 4 reference points on each camera.
    """
    
    calibration_complete = pyqtSignal(list)  # list of [camera_idx, points]
    cancelled = pyqtSignal()
    
    POINT_DESCRIPTIONS = [
        "Click the outer double ring where 20 meets 1 (top-right area)",
        "Click the outer double ring where 6 meets 10 (bottom-right area)",
        "Click the outer double ring where 19 meets 3 (bottom-left area)",
        "Click the outer double ring where 11 meets 14 (top-left area)",
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_camera = 0
        self._all_calibrations: list = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        
        # Title
        self._title = QLabel("Camera Calibration")
        self._title.setFont(QFont("Inter", 28, QFont.Weight.ExtraBold))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title)
        
        # Progress
        self._progress = QLabel(f"Camera 1 of {NUM_CAMERAS}")
        self._progress.setFont(QFont("Inter", 14))
        self._progress.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._progress)
        
        # Instruction
        self._instruction = QLabel(self.POINT_DESCRIPTIONS[0])
        self._instruction.setFont(QFont("Inter", 14))
        self._instruction.setStyleSheet(
            f"color: {COLORS['warning']}; "
            f"background-color: rgba(255, 165, 2, 0.08); "
            f"border: 1px solid rgba(255, 165, 2, 0.2); "
            f"border-radius: 8px; padding: 12px;"
        )
        self._instruction.setWordWrap(True)
        self._instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._instruction)
        
        # Camera view (clickable)
        self._camera_view = CalibrationClickLabel()
        self._camera_view.setMinimumSize(640, 480)
        self._camera_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._camera_view.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 12px;"
        )
        self._camera_view.point_clicked.connect(self._on_point_clicked)
        layout.addWidget(self._camera_view)
        
        # Point counter
        self._point_counter = QLabel("Points: 0 / 4")
        self._point_counter.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self._point_counter.setStyleSheet(f"color: {COLORS['accent']};")
        self._point_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._point_counter)
        
        # Buttons
        btn_row = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "ghost")
        cancel_btn.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(cancel_btn)
        
        btn_row.addStretch()
        
        self._redo_btn = QPushButton("↩ Redo Points")
        self._redo_btn.clicked.connect(self._redo_points)
        btn_row.addWidget(self._redo_btn)
        
        self._next_btn = QPushButton("Next Camera →")
        self._next_btn.setProperty("class", "primary")
        self._next_btn.clicked.connect(self._next_camera)
        self._next_btn.setEnabled(False)
        btn_row.addWidget(self._next_btn)
        
        layout.addLayout(btn_row)
    
    def set_camera_frame(self, camera_index: int, frame: np.ndarray):
        """Update the displayed camera frame."""
        if camera_index == self._current_camera:
            self._camera_view.set_frame(frame)
    
    def _on_point_clicked(self, x: float, y: float):
        """Handle a calibration point click."""
        num_points = len(self._camera_view.points)
        self._point_counter.setText(
            f"Points: {num_points} / {NUM_CALIBRATION_POINTS}"
        )
        
        if num_points < NUM_CALIBRATION_POINTS:
            self._instruction.setText(self.POINT_DESCRIPTIONS[num_points])
        
        if num_points >= NUM_CALIBRATION_POINTS:
            self._next_btn.setEnabled(True)
            self._instruction.setText("✅ All points set! Click 'Next Camera' to continue.")
            self._instruction.setStyleSheet(
                f"color: {COLORS['accent']}; "
                f"background-color: rgba(0, 255, 136, 0.08); "
                f"border: 1px solid rgba(0, 255, 136, 0.2); "
                f"border-radius: 8px; padding: 12px;"
            )
    
    def _redo_points(self):
        """Clear points and start over for current camera."""
        self._camera_view.clear_points()
        self._point_counter.setText(f"Points: 0 / {NUM_CALIBRATION_POINTS}")
        self._instruction.setText(self.POINT_DESCRIPTIONS[0])
        self._instruction.setStyleSheet(
            f"color: {COLORS['warning']}; "
            f"background-color: rgba(255, 165, 2, 0.08); "
            f"border: 1px solid rgba(255, 165, 2, 0.2); "
            f"border-radius: 8px; padding: 12px;"
        )
        self._next_btn.setEnabled(False)
    
    def _next_camera(self):
        """Save current camera calibration and move to next."""
        points = self._camera_view.points
        self._all_calibrations.append({
            "camera_index": self._current_camera,
            "points": [[p[0], p[1]] for p in points],
        })
        
        self._current_camera += 1
        
        if self._current_camera >= NUM_CAMERAS:
            # All cameras calibrated
            self.calibration_complete.emit(self._all_calibrations)
            return
        
        # Reset for next camera
        self._camera_view.clear_points()
        self._progress.setText(
            f"Camera {self._current_camera + 1} of {NUM_CAMERAS}"
        )
        self._point_counter.setText(f"Points: 0 / {NUM_CALIBRATION_POINTS}")
        self._instruction.setText(self.POINT_DESCRIPTIONS[0])
        self._instruction.setStyleSheet(
            f"color: {COLORS['warning']}; "
            f"background-color: rgba(255, 165, 2, 0.08); "
            f"border: 1px solid rgba(255, 165, 2, 0.2); "
            f"border-radius: 8px; padding: 12px;"
        )
        self._next_btn.setEnabled(False)
    
    def reset(self):
        """Reset the wizard."""
        self._current_camera = 0
        self._all_calibrations.clear()
        self._camera_view.clear_points()
        self._progress.setText(f"Camera 1 of {NUM_CAMERAS}")
        self._point_counter.setText(f"Points: 0 / {NUM_CALIBRATION_POINTS}")
        self._next_btn.setEnabled(False)
