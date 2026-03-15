"""
Interactive dartboard visualization widget.
Draws a vector dartboard with accurate proportions and animated hit markers.
"""

import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QRadialGradient,
    QLinearGradient, QFont, QPainterPath
)

from config import (
    SECTOR_ORDER,
    BULLSEYE_RADIUS_MM, OUTER_BULL_RADIUS_MM,
    TRIPLE_RING_INNER_RADIUS_MM, TRIPLE_RING_OUTER_RADIUS_MM,
    DOUBLE_RING_INNER_RADIUS_MM, DOUBLE_RING_OUTER_RADIUS_MM,
    COLORS,
)
from detection.scorer import DartScore


class DartboardWidget(QWidget):
    """
    Vector-drawn dartboard widget with dart hit visualization.
    
    Features:
    - Accurately proportioned dartboard segments
    - Animated dart hit markers with glow effects
    - Click-to-correct score (click a segment to get its score)
    - Responsive sizing
    """
    
    # Signal emitted when user clicks a segment (for score correction)
    segment_clicked = pyqtSignal(object)  # DartScore
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        
        # Dart hits to display
        self._hits: list[dict] = []  # [{x_mm, y_mm, score, glow}]
        self._max_hits = 3  # Show last 3 hits
        
        # Animation
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._update_glow)
        self._glow_timer.start(50)
        self._glow_phase = 0.0
        
        # Colors
        self._black_segment = QColor(30, 30, 35)
        self._white_segment = QColor(230, 225, 210)
        self._red_ring = QColor(220, 50, 50)
        self._green_ring = QColor(40, 160, 60)
        self._bull_red = QColor(200, 40, 40)
        self._bull_green = QColor(50, 150, 60)
        self._wire_color = QColor(180, 180, 180, 100)
        self._number_color = QColor(200, 200, 200)
        self._bg_color = QColor(10, 10, 15)
        self._hit_color = QColor(COLORS["accent"])
        
        self.setMouseTracking(True)
    
    def add_hit(self, x_mm: float, y_mm: float, score: DartScore):
        """Add a dart hit marker to the board."""
        self._hits.append({
            "x_mm": x_mm,
            "y_mm": y_mm,
            "score": score,
            "glow": 1.0,
        })
        
        # Keep only recent hits
        if len(self._hits) > self._max_hits:
            self._hits.pop(0)
        
        self.update()
    
    def clear_hits(self):
        """Clear all hit markers."""
        self._hits.clear()
        self.update()
    
    def _update_glow(self):
        """Animate the glow effect on hit markers."""
        self._glow_phase += 0.1
        if self._glow_phase > 2 * math.pi:
            self._glow_phase -= 2 * math.pi
        self.update()
    
    def _mm_to_px(self, mm: float) -> float:
        """Convert mm to pixels based on current widget size."""
        size = min(self.width(), self.height())
        # Leave margin for numbers
        board_size = size * 0.82
        return mm * (board_size / 2) / DOUBLE_RING_OUTER_RADIUS_MM
    
    def _board_center(self) -> QPointF:
        """Get the center of the board in widget coordinates."""
        return QPointF(self.width() / 2, self.height() / 2)
    
    def paintEvent(self, event):
        """Draw the dartboard."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self._board_center()
        
        # Background
        painter.fillRect(self.rect(), self._bg_color)
        
        # Draw board shadow
        shadow_r = self._mm_to_px(DOUBLE_RING_OUTER_RADIUS_MM + 15)
        shadow_grad = QRadialGradient(center, shadow_r)
        shadow_grad.setColorAt(0.7, QColor(0, 0, 0, 60))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, shadow_r, shadow_r)
        
        # Draw segments from outside in
        self._draw_segments(painter, center)
        
        # Draw wires
        self._draw_wires(painter, center)
        
        # Draw bulls
        self._draw_bulls(painter, center)
        
        # Draw numbers
        self._draw_numbers(painter, center)
        
        # Draw hit markers
        self._draw_hits(painter, center)
        
        painter.end()
    
    def _draw_segments(self, painter: QPainter, center: QPointF):
        """Draw the 20 dartboard segments with correct colors."""
        sector_angle = 360.0 / 20
        start_offset = -90 - sector_angle / 2  # So "20" is at the top
        
        for i, sector_num in enumerate(SECTOR_ORDER):
            start_angle = start_offset + i * sector_angle
            
            # Determine colors for this sector
            if i % 2 == 0:
                segment_color = self._black_segment
                ring_color = self._red_ring
            else:
                segment_color = self._white_segment
                ring_color = self._green_ring
            
            # Double ring (outermost scoring area)
            self._draw_ring_segment(
                painter, center, start_angle, sector_angle,
                self._mm_to_px(DOUBLE_RING_INNER_RADIUS_MM),
                self._mm_to_px(DOUBLE_RING_OUTER_RADIUS_MM),
                ring_color
            )
            
            # Outer single
            self._draw_ring_segment(
                painter, center, start_angle, sector_angle,
                self._mm_to_px(TRIPLE_RING_OUTER_RADIUS_MM),
                self._mm_to_px(DOUBLE_RING_INNER_RADIUS_MM),
                segment_color
            )
            
            # Triple ring
            self._draw_ring_segment(
                painter, center, start_angle, sector_angle,
                self._mm_to_px(TRIPLE_RING_INNER_RADIUS_MM),
                self._mm_to_px(TRIPLE_RING_OUTER_RADIUS_MM),
                ring_color
            )
            
            # Inner single
            self._draw_ring_segment(
                painter, center, start_angle, sector_angle,
                self._mm_to_px(OUTER_BULL_RADIUS_MM),
                self._mm_to_px(TRIPLE_RING_INNER_RADIUS_MM),
                segment_color
            )
    
    def _draw_ring_segment(self, painter: QPainter, center: QPointF,
                           start_angle: float, span_angle: float,
                           inner_r: float, outer_r: float,
                           color: QColor):
        """Draw a ring segment (pie slice between two radii)."""
        path = QPainterPath()
        
        # Outer arc
        outer_rect = QRectF(
            center.x() - outer_r, center.y() - outer_r,
            outer_r * 2, outer_r * 2
        )
        inner_rect = QRectF(
            center.x() - inner_r, center.y() - inner_r,
            inner_r * 2, inner_r * 2
        )
        
        # Qt uses 1/16th of a degree for angles
        start_16 = int(start_angle * 16)
        span_16 = int(span_angle * 16)
        
        path.arcMoveTo(outer_rect, start_angle)
        path.arcTo(outer_rect, start_angle, span_angle)
        path.arcTo(inner_rect, start_angle + span_angle, -span_angle)
        path.closeSubpath()
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
    
    def _draw_wires(self, painter: QPainter, center: QPointF):
        """Draw the wire grid on the board."""
        pen = QPen(self._wire_color, 0.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Ring wires
        for r_mm in [BULLSEYE_RADIUS_MM, OUTER_BULL_RADIUS_MM,
                     TRIPLE_RING_INNER_RADIUS_MM, TRIPLE_RING_OUTER_RADIUS_MM,
                     DOUBLE_RING_INNER_RADIUS_MM, DOUBLE_RING_OUTER_RADIUS_MM]:
            r = self._mm_to_px(r_mm)
            painter.drawEllipse(center, r, r)
        
        # Sector wires
        sector_angle = 360.0 / 20
        start_offset = -90 - sector_angle / 2
        inner_r = self._mm_to_px(BULLSEYE_RADIUS_MM)
        outer_r = self._mm_to_px(DOUBLE_RING_OUTER_RADIUS_MM)
        
        for i in range(20):
            angle = math.radians(start_offset + i * sector_angle)
            x1 = center.x() + inner_r * math.cos(angle)
            y1 = center.y() - inner_r * math.sin(angle)
            x2 = center.x() + outer_r * math.cos(angle)
            y2 = center.y() - outer_r * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def _draw_bulls(self, painter: QPainter, center: QPointF):
        """Draw the bullseye and outer bull."""
        # Outer bull (green)
        r_outer = self._mm_to_px(OUTER_BULL_RADIUS_MM)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._bull_green))
        painter.drawEllipse(center, r_outer, r_outer)
        
        # Inner bull (red)
        r_inner = self._mm_to_px(BULLSEYE_RADIUS_MM)
        painter.setBrush(QBrush(self._bull_red))
        painter.drawEllipse(center, r_inner, r_inner)
    
    def _draw_numbers(self, painter: QPainter, center: QPointF):
        """Draw sector numbers around the board."""
        font = QFont("Inter", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(self._number_color))
        
        radius = self._mm_to_px(DOUBLE_RING_OUTER_RADIUS_MM + 14)
        sector_angle = 360.0 / 20
        
        for i, num in enumerate(SECTOR_ORDER):
            angle = math.radians(-90 + i * sector_angle)
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)
            
            text = str(num)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            
            painter.drawText(
                QPointF(x - tw / 2, y + th / 4), text
            )
    
    def _draw_hits(self, painter: QPainter, center: QPointF):
        """Draw dart hit markers with glow animation."""
        for i, hit in enumerate(self._hits):
            x_px = center.x() + self._mm_to_px(hit["x_mm"])
            y_px = center.y() + self._mm_to_px(hit["y_mm"])
            pos = QPointF(x_px, y_px)
            
            # Pulsing glow
            glow_intensity = 0.5 + 0.5 * math.sin(self._glow_phase + i)
            is_latest = (i == len(self._hits) - 1)
            
            if is_latest:
                # Larger glow for latest hit
                glow_r = 18 + 4 * glow_intensity
                glow_color = QColor(self._hit_color)
                glow_color.setAlphaF(0.3 * glow_intensity)
                
                glow_grad = QRadialGradient(pos, glow_r)
                glow_grad.setColorAt(0, glow_color)
                glow_grad.setColorAt(1, QColor(0, 0, 0, 0))
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(glow_grad))
                painter.drawEllipse(pos, glow_r, glow_r)
            
            # Dart marker
            marker_r = 5 if is_latest else 3
            painter.setPen(QPen(QColor(255, 255, 255), 1.5))
            painter.setBrush(QBrush(self._hit_color))
            painter.drawEllipse(pos, marker_r, marker_r)
            
            # Score label for latest hit
            if is_latest and hit["score"]:
                font = QFont("Inter", 10, QFont.Weight.Bold)
                painter.setFont(font)
                painter.setPen(QPen(QColor(COLORS["accent"])))
                painter.drawText(
                    QPointF(x_px + 10, y_px - 10),
                    hit["score"].label
                )
    
    def mousePressEvent(self, event):
        """Handle click on dartboard for manual score correction."""
        if event.button() == Qt.MouseButton.LeftButton:
            center = self._board_center()
            dx_px = event.position().x() - center.x()
            dy_px = event.position().y() - center.y()
            
            # Convert pixel offset to mm
            px_per_mm = self._mm_to_px(1.0)
            if px_per_mm > 0:
                x_mm = dx_px / px_per_mm
                y_mm = dy_px / px_per_mm
                
                from detection.scorer import DartScorer
                scorer = DartScorer()
                score = scorer.calculate(x_mm, y_mm)
                self.segment_clicked.emit(score)
        
        super().mousePressEvent(event)
