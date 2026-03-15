"""
Core dart detection module.
Implements the image-differencing pipeline for detecting darts on the dartboard.

Pipeline:
1. Capture reference frame (empty board or board with previous darts)
2. Continuously compare current frame to reference
3. When enough pixels change → a dart has landed
4. Extract dart shape via corner detection + filtering
5. Find dart tip using skeletonization
6. Transform tip position to dartboard coordinates
7. Calculate score
"""

import cv2
import numpy as np
import time
import logging
from dataclasses import dataclass
from enum import Enum

from config import (
    NUM_CAMERAS,
    DIFF_THRESHOLD, GAUSSIAN_KERNEL, MORPH_KERNEL_SIZE,
    MIN_DART_PIXELS, MAX_DART_PIXELS,
    MIN_CORNERS, MIN_FILTERED_CORNERS,
    CORNER_MAX_CORNERS, CORNER_QUALITY, CORNER_MIN_DISTANCE,
    CORNER_BLOCK_SIZE, CORNER_K,
    CORNER_FILTER_X_RANGE, CORNER_FILTER_Y_RANGE,
    CORNER_LINE_DISTANCE,
    TAKEOUT_THRESHOLD, TAKEOUT_DELAY,
    DETECTION_SLEEP, DART_SETTLE_TIME,
)
from detection.kalman import KalmanFilter
from detection.calibration import Calibration
from detection.scorer import DartScorer, DartScore

logger = logging.getLogger(__name__)


class DetectionEvent(Enum):
    """Types of events the detector can emit."""
    DART_DETECTED = "dart_detected"
    TAKEOUT = "takeout"
    NO_DETECTION = "no_detection"
    ERROR = "error"


@dataclass
class DartDetection:
    """Result of a dart detection from a single camera."""
    camera_index: int
    tip_position: tuple[float, float]  # In camera pixel coordinates
    confidence: float
    diff_image: np.ndarray | None = None


@dataclass
class DetectionResult:
    """Combined detection result from all cameras."""
    event: DetectionEvent
    score: DartScore | None = None
    detections: list[DartDetection] | None = None
    board_position_mm: tuple[float, float] | None = None


class DartDetector:
    """
    Main dart detection engine.
    Uses image differencing across multiple cameras to detect dart hits.
    """
    
    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        self.scorer = DartScorer()
        
        # Kalman filters for each camera
        self.kalman_filters = [KalmanFilter() for _ in range(NUM_CAMERAS)]
        
        # Reference frames (the "before" images)
        self.reference_frames: dict[int, np.ndarray] = {}
        
        # Previous tip points for tracking
        self.prev_tips: dict[int, tuple[float, float] | None] = {
            i: None for i in range(NUM_CAMERAS)
        }
        
        # Morphological kernel
        self._morph_kernel = np.ones(
            (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE), np.uint8
        )
        
        # Callbacks
        self._callbacks = []
    
    def set_reference_frame(self, camera_index: int, frame: np.ndarray):
        """Set the reference frame for a camera (grayscale)."""
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.reference_frames[camera_index] = frame.copy()
    
    def set_all_reference_frames(self, frames: dict[int, np.ndarray]):
        """Set reference frames for all cameras."""
        for idx, frame in frames.items():
            self.set_reference_frame(idx, frame)
    
    def on_detection(self, callback):
        """Register callback for detection events: callback(DetectionResult)."""
        self._callbacks.append(callback)
    
    def _emit(self, result: DetectionResult):
        """Emit a detection result to all callbacks."""
        for cb in self._callbacks:
            cb(result)
    
    # ── Image Processing Pipeline ─────────────────────────────────────────
    
    @staticmethod
    def to_gray(frame: np.ndarray) -> np.ndarray:
        """Convert frame to grayscale if needed."""
        if len(frame.shape) == 3:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame
    
    def get_diff_threshold(self, current_gray: np.ndarray,
                           reference_gray: np.ndarray) -> np.ndarray:
        """
        Compute thresholded difference image between current and reference.
        Returns binary image showing changed pixels.
        """
        # Absolute difference
        diff = cv2.absdiff(reference_gray, current_gray)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(diff, GAUSSIAN_KERNEL, 0)
        
        # Binary threshold
        _, thresh = cv2.threshold(
            blurred, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY
        )
        
        # Morphological closing (fill small holes)
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, self._morph_kernel)
        
        # Morphological opening (remove noise)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, self._morph_kernel)
        
        return opened
    
    @staticmethod
    def get_diff_blur(current_gray: np.ndarray,
                      reference_gray: np.ndarray) -> np.ndarray:
        """
        Compute blurred difference image for corner detection.
        Returns the blurred diff image.
        """
        diff = cv2.absdiff(reference_gray, current_gray)
        kernel = np.ones((5, 5), np.float32) / 25
        return cv2.filter2D(diff, -1, kernel)
    
    @staticmethod
    def detect_corners(diff_blur: np.ndarray) -> np.ndarray:
        """
        Detect corners/features in the diff image using Harris detector.
        These corners represent the dart shape.
        """
        corners = cv2.goodFeaturesToTrack(
            diff_blur,
            maxCorners=CORNER_MAX_CORNERS,
            qualityLevel=CORNER_QUALITY,
            minDistance=CORNER_MIN_DISTANCE,
            mask=None,
            blockSize=CORNER_BLOCK_SIZE,
            useHarrisDetector=True,
            k=CORNER_K
        )
        if corners is None:
            return np.array([])
        return np.intp(corners)
    
    @staticmethod
    def filter_corners_by_distance(corners: np.ndarray) -> np.ndarray:
        """
        Filter corners by distance from mean position.
        Removes outlier points that aren't part of the dart.
        """
        if len(corners) == 0:
            return corners
        
        mean = np.mean(corners, axis=0)
        filtered = np.array([
            c for c in corners
            if abs(mean[0][0] - c[0][0]) <= CORNER_FILTER_X_RANGE
            and abs(mean[0][1] - c[0][1]) <= CORNER_FILTER_Y_RANGE
        ])
        return filtered if len(filtered) > 0 else corners
    
    @staticmethod
    def filter_corners_by_line(corners: np.ndarray,
                               rows: int, cols: int) -> np.ndarray:
        """
        Filter corners to keep only those near the fitted line.
        The dart is roughly linear, so points far from the line are noise.
        """
        if len(corners) < 5:
            return corners
        
        try:
            [vx, vy, x, y] = cv2.fitLine(
                corners, cv2.DIST_HUBER, 0, 0.1, 0.1
            )
            lefty = int((-x[0] * vy[0] / vx[0]) + y[0])
            righty = int(((cols - x[0]) * vy[0] / vx[0]) + y[0])
            
            filtered = np.array([
                c for c in corners
                if abs(
                    (righty - lefty) * c[0][0] - (cols - 1) * c[0][1]
                    + cols * lefty - righty
                ) / np.sqrt((righty - lefty) ** 2 + (cols - 1) ** 2)
                <= CORNER_LINE_DISTANCE
            ])
            return filtered if len(filtered) > 0 else corners
        except Exception:
            return corners
    
    def find_dart_tip(self, corners: np.ndarray,
                      diff_blur: np.ndarray,
                      camera_index: int) -> tuple[int, int] | None:
        """
        Find the dart tip from filtered corners.
        Uses skeletonization and the Kalman filter.
        
        Returns (x, y) tip position in pixels, or None if not found.
        """
        if len(corners) < 3:
            return None
        
        try:
            # Create contour from corners
            contour = corners.reshape((-1, 1, 2))
            
            # Draw filled contour on blank image
            mask = np.zeros_like(diff_blur)
            cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
            
            # Skeletonize using thinning
            try:
                skeleton = cv2.ximgproc.thinning(mask)
            except AttributeError:
                # ximgproc not available, fall back to lowest point method
                skeleton = mask
            
            # Find contours of skeleton
            skel_contours, _ = cv2.findContours(
                skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if len(skel_contours) > 0:
                # Use the largest contour
                largest = max(skel_contours, key=cv2.contourArea)
                points = largest.reshape(-1, 2)
                
                # Find the point closest to the board (lowest y for top-mounted,
                # or use the extreme point based on camera position)
                # Default: use the lowest point (highest y value)
                tip_idx = np.argmax(points[:, 1])
                tip = (int(points[tip_idx][0]), int(points[tip_idx][1]))
            else:
                # Fallback: use extreme corner point
                tip_idx = np.argmax(corners[:, 0, 1])
                tip = (int(corners[tip_idx][0][0]), int(corners[tip_idx][0][1]))
            
            # Update Kalman filter
            kf = self.kalman_filters[camera_index]
            kf.predict()
            kf.update(np.array([[tip[0]], [tip[1]]]))
            
            # Use filtered position
            filtered_x, filtered_y = kf.position
            tip = (int(filtered_x), int(filtered_y))
            
            self.prev_tips[camera_index] = tip
            return tip
            
        except Exception as e:
            logger.warning(f"Tip detection failed for camera {camera_index}: {e}")
            return None
    
    # ── Main Detection Method ─────────────────────────────────────────────
    
    def process_frame(self, camera_index: int,
                      current_frame: np.ndarray) -> DartDetection | None:
        """
        Process a single frame from one camera.
        Compares to reference and attempts dart detection.
        
        Returns DartDetection if a dart was found, None otherwise.
        """
        ref = self.reference_frames.get(camera_index)
        if ref is None:
            return None
        
        current_gray = self.to_gray(current_frame)
        
        # Step 1: Get threshold image
        thresh = self.get_diff_threshold(current_gray, ref)
        pixel_count = cv2.countNonZero(thresh)
        
        # Check if it's a takeout (hand removing darts)
        if pixel_count > TAKEOUT_THRESHOLD:
            return None  # Signal takeout externally
        
        # Check if enough pixels changed for a dart
        if pixel_count < MIN_DART_PIXELS or pixel_count > MAX_DART_PIXELS:
            return None
        
        # Step 2: Get blurred diff for corner detection
        diff_blur = self.get_diff_blur(current_gray, ref)
        
        # Step 3: Detect corners
        corners = self.detect_corners(diff_blur)
        if len(corners) < MIN_CORNERS:
            return None
        
        # Step 4: Filter corners
        corners = self.filter_corners_by_distance(corners)
        if len(corners) < MIN_FILTERED_CORNERS:
            return None
        
        rows, cols = diff_blur.shape[:2]
        corners = self.filter_corners_by_line(corners, rows, cols)
        
        # Re-check threshold on blurred diff
        _, blur_thresh = cv2.threshold(diff_blur, DIFF_THRESHOLD, 255, 0)
        if cv2.countNonZero(blur_thresh) > 15000:
            return None
        
        # Step 5: Find dart tip
        tip = self.find_dart_tip(corners, diff_blur, camera_index)
        if tip is None:
            return None
        
        # Calculate confidence based on corner quality
        confidence = min(len(corners) / 100.0, 1.0)
        
        return DartDetection(
            camera_index=camera_index,
            tip_position=tip,
            confidence=confidence,
            diff_image=diff_blur,
        )
    
    def detect_from_frames(self,
                           frames: dict[int, np.ndarray]) -> DetectionResult:
        """
        Run detection across all camera frames.
        Combines results from multiple cameras for the final score.
        """
        detections = []
        is_takeout = False
        
        for cam_idx, frame in frames.items():
            ref = self.reference_frames.get(cam_idx)
            if ref is None:
                continue
            
            current_gray = self.to_gray(frame)
            thresh = self.get_diff_threshold(current_gray, ref)
            pixel_count = cv2.countNonZero(thresh)
            
            # Check takeout on any camera
            if pixel_count > TAKEOUT_THRESHOLD:
                is_takeout = True
                break
            
            detection = self.process_frame(cam_idx, frame)
            if detection is not None:
                detections.append(detection)
        
        if is_takeout:
            self._handle_takeout()
            return DetectionResult(event=DetectionEvent.TAKEOUT)
        
        if not detections:
            return DetectionResult(event=DetectionEvent.NO_DETECTION)
        
        # Use the detection with highest confidence
        best = max(detections, key=lambda d: d.confidence)
        
        # Transform to dartboard coordinates
        try:
            if self.calibration.is_calibrated(best.camera_index):
                mm_x, mm_y = self.calibration.transform_to_mm(
                    best.camera_index,
                    best.tip_position[0],
                    best.tip_position[1]
                )
                score = self.scorer.calculate(mm_x, mm_y)
                
                return DetectionResult(
                    event=DetectionEvent.DART_DETECTED,
                    score=score,
                    detections=detections,
                    board_position_mm=(mm_x, mm_y),
                )
            else:
                logger.warning("Camera not calibrated, returning raw detection")
                return DetectionResult(
                    event=DetectionEvent.DART_DETECTED,
                    detections=detections,
                )
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return DetectionResult(
                event=DetectionEvent.ERROR,
                detections=detections,
            )
    
    def _handle_takeout(self):
        """Handle dart takeout — reset tracking state."""
        logger.info("Takeout detected — resetting tracking")
        for i in range(NUM_CAMERAS):
            self.prev_tips[i] = None
            self.kalman_filters[i].reset()
    
    def update_reference_after_hit(self, frames: dict[int, np.ndarray]):
        """
        Update reference frames after a dart hit.
        The new reference should include the dart that just landed.
        """
        for cam_idx, frame in frames.items():
            self.set_reference_frame(cam_idx, frame)
    
    def reset(self):
        """Full reset — clear all state."""
        self.reference_frames.clear()
        self._handle_takeout()
