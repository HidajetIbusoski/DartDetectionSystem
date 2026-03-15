"""
Camera calibration module.
Manages 4-point perspective calibration for each camera to map
camera coordinates to dartboard coordinates.
"""

import cv2
import numpy as np
import json
import logging
from pathlib import Path

from config import (
    NUM_CAMERAS, NUM_CALIBRATION_POINTS,
    CALIBRATION_DIR, DOUBLE_RING_OUTER_RADIUS_MM,
    CAMERA_WIDTH, CAMERA_HEIGHT
)

logger = logging.getLogger(__name__)


class Calibration:
    """
    Handles perspective calibration for dart cameras.
    
    The user selects 4 reference points on the dartboard in each camera view.
    These correspond to the outer double ring intersection points:
      1. 20/1 boundary (top-right)
      2. 6/10 boundary (bottom-right)
      3. 19/3 boundary (bottom-left)
      4. 11/14 boundary (top-left)
    
    A perspective transform matrix is computed to map camera pixels
    to a normalized dartboard coordinate space.
    """
    
    def __init__(self):
        self.perspective_matrices: list[np.ndarray | None] = [None] * NUM_CAMERAS
        self.inverse_matrices: list[np.ndarray | None] = [None] * NUM_CAMERAS
        self.source_points: list[np.ndarray | None] = [None] * NUM_CAMERAS
        self._board_center_px = (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2)
        self._pixels_per_mm = 1.0
    
    def set_calibration_points(self, camera_index: int, points: list[list[float]]):
        """
        Set the 4 calibration points for a camera and compute the transform.
        
        Args:
            camera_index: Index of the camera (0, 1, or 2)
            points: List of 4 [x, y] points clicked by the user
        """
        if len(points) != NUM_CALIBRATION_POINTS:
            raise ValueError(f"Expected {NUM_CALIBRATION_POINTS} points, got {len(points)}")
        
        src_points = np.float32(points)
        self.source_points[camera_index] = src_points
        
        # Destination points: map to a normalized square view centered on the board
        # We use a virtual board image of the same size as camera resolution
        # with the board center at the image center
        board_radius_px = min(CAMERA_WIDTH, CAMERA_HEIGHT) * 0.4
        self._pixels_per_mm = board_radius_px / DOUBLE_RING_OUTER_RADIUS_MM
        
        cx, cy = CAMERA_WIDTH / 2, CAMERA_HEIGHT / 2
        self._board_center_px = (cx, cy)
        
        # Compute destination points matching the 4 calibration positions
        # These are at the outer double ring at specific angles
        # 20/1: ~9° from top → angle from right = 81°
        # 6/10: ~99° from top → angle from right = -9°
        # 19/3: ~189° from top → angle from right = -99°
        # 11/14: ~279° from top → angle from right = -189° = 171°
        angles_deg = [81, -9, -99, 171]
        
        dst_points = []
        for angle_deg in angles_deg:
            angle_rad = np.radians(angle_deg)
            px = cx + board_radius_px * np.cos(angle_rad)
            py = cy - board_radius_px * np.sin(angle_rad)
            dst_points.append([px, py])
        
        dst_points = np.float32(dst_points)
        
        # Compute perspective transform
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        self.perspective_matrices[camera_index] = matrix
        
        # Compute inverse for reverse mapping
        _, inv_matrix = cv2.invert(matrix)
        self.inverse_matrices[camera_index] = inv_matrix
        
        logger.info(f"Calibration set for camera {camera_index}")
    
    def transform_point(self, camera_index: int, x: float, y: float) -> tuple[float, float]:
        """
        Transform a point from camera space to calibrated dartboard space.
        Returns (x, y) in the calibrated coordinate system.
        """
        matrix = self.perspective_matrices[camera_index]
        if matrix is None:
            raise ValueError(f"Camera {camera_index} is not calibrated")
        
        point = np.array([[[x, y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, matrix)
        return float(transformed[0][0][0]), float(transformed[0][0][1])
    
    def transform_to_mm(self, camera_index: int, x: float, y: float) -> tuple[float, float]:
        """
        Transform a point from camera space to dartboard millimeter coordinates.
        Origin (0, 0) = board center. Suitable for passing to the scorer.
        """
        tx, ty = self.transform_point(camera_index, x, y)
        cx, cy = self._board_center_px
        mm_x = (tx - cx) / self._pixels_per_mm
        mm_y = (ty - cy) / self._pixels_per_mm
        return mm_x, mm_y
    
    def is_calibrated(self, camera_index: int) -> bool:
        """Check if a specific camera is calibrated."""
        return self.perspective_matrices[camera_index] is not None
    
    def all_calibrated(self) -> bool:
        """Check if all cameras are calibrated."""
        return all(m is not None for m in self.perspective_matrices)
    
    def save(self, directory: Path | str | None = None):
        """Save calibration data to disk."""
        save_dir = Path(directory) if directory else CALIBRATION_DIR
        save_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(NUM_CAMERAS):
            if self.perspective_matrices[i] is not None:
                filepath = save_dir / f"camera_{i}_calibration.npz"
                np.savez(
                    filepath,
                    matrix=self.perspective_matrices[i],
                    source_points=self.source_points[i],
                    pixels_per_mm=self._pixels_per_mm,
                    board_center=np.array(self._board_center_px),
                )
                logger.info(f"Saved calibration for camera {i} to {filepath}")
    
    def load(self, directory: Path | str | None = None) -> bool:
        """
        Load calibration data from disk.
        Returns True if at least one calibration was loaded.
        """
        load_dir = Path(directory) if directory else CALIBRATION_DIR
        loaded_any = False
        
        for i in range(NUM_CAMERAS):
            filepath = load_dir / f"camera_{i}_calibration.npz"
            if filepath.exists():
                try:
                    data = np.load(filepath)
                    self.perspective_matrices[i] = data["matrix"]
                    self.source_points[i] = data["source_points"]
                    self._pixels_per_mm = float(data["pixels_per_mm"])
                    center = data["board_center"]
                    self._board_center_px = (float(center[0]), float(center[1]))
                    
                    _, inv = cv2.invert(self.perspective_matrices[i])
                    self.inverse_matrices[i] = inv
                    
                    loaded_any = True
                    logger.info(f"Loaded calibration for camera {i}")
                except Exception as e:
                    logger.error(f"Failed to load calibration for camera {i}: {e}")
        
        return loaded_any
    
    @property
    def pixels_per_mm(self) -> float:
        return self._pixels_per_mm
    
    @property
    def board_center_px(self) -> tuple[float, float]:
        return self._board_center_px
