"""
Camera capture and management module.
Handles multi-camera capture in separate threads for low-latency frame delivery.
"""

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
import time
import logging

from config import (
    NUM_CAMERAS, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS,
    DEFAULT_CAMERA_INDICES
)

logger = logging.getLogger(__name__)


class CameraThread(QThread):
    """Thread that continuously captures frames from a single camera."""
    
    frame_ready = pyqtSignal(int, np.ndarray)  # camera_index, frame
    error = pyqtSignal(int, str)  # camera_index, error_message
    
    def __init__(self, camera_index: int, device_index: int, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self.device_index = device_index
        self._running = False
        self._mutex = QMutex()
        self._cap = None
    
    def run(self):
        """Main capture loop."""
        self._cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        
        if not self._cap.isOpened():
            self.error.emit(self.camera_index, f"Failed to open camera {self.device_index}")
            return
        
        # Configure camera
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        
        self._running = True
        logger.info(f"Camera {self.camera_index} (device {self.device_index}) started")
        
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                self.frame_ready.emit(self.camera_index, frame)
            else:
                self.error.emit(self.camera_index, "Failed to read frame")
                time.sleep(0.1)
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.001)
        
        self._cap.release()
        logger.info(f"Camera {self.camera_index} stopped")
    
    def stop(self):
        """Stop the capture loop."""
        self._running = False
        self.wait(2000)


class CameraManager:
    """
    Manages multiple cameras for the dart detection system.
    Provides thread-safe access to the latest frames from each camera.
    """
    
    def __init__(self, camera_indices=None):
        self.camera_indices = camera_indices or DEFAULT_CAMERA_INDICES
        self.threads: list[CameraThread] = []
        self._frames: dict[int, np.ndarray] = {}
        self._mutex = QMutex()
        self._frame_callbacks = []
        self._error_callbacks = []
    
    def start(self):
        """Start all camera capture threads."""
        for i, device_idx in enumerate(self.camera_indices):
            thread = CameraThread(i, device_idx)
            thread.frame_ready.connect(self._on_frame)
            thread.error.connect(self._on_error)
            self.threads.append(thread)
            thread.start()
            logger.info(f"Starting camera thread {i} on device {device_idx}")
    
    def stop(self):
        """Stop all camera capture threads."""
        for thread in self.threads:
            thread.stop()
        self.threads.clear()
        self._frames.clear()
    
    def _on_frame(self, camera_index: int, frame: np.ndarray):
        """Handle incoming frame from a camera thread."""
        with QMutexLocker(self._mutex):
            self._frames[camera_index] = frame.copy()
        
        for callback in self._frame_callbacks:
            callback(camera_index, frame)
    
    def _on_error(self, camera_index: int, message: str):
        """Handle camera error."""
        logger.error(f"Camera {camera_index} error: {message}")
        for callback in self._error_callbacks:
            callback(camera_index, message)
    
    def get_frame(self, camera_index: int) -> np.ndarray | None:
        """Get the latest frame from a camera (thread-safe)."""
        with QMutexLocker(self._mutex):
            return self._frames.get(camera_index, None)
    
    def get_gray_frame(self, camera_index: int) -> np.ndarray | None:
        """Get the latest frame as grayscale."""
        frame = self.get_frame(camera_index)
        if frame is not None:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return None
    
    def get_all_frames(self) -> dict[int, np.ndarray]:
        """Get the latest frames from all cameras."""
        with QMutexLocker(self._mutex):
            return {k: v.copy() for k, v in self._frames.items()}
    
    def on_frame(self, callback):
        """Register a callback for new frames: callback(camera_index, frame)."""
        self._frame_callbacks.append(callback)
    
    def on_error(self, callback):
        """Register a callback for errors: callback(camera_index, message)."""
        self._error_callbacks.append(callback)
    
    @staticmethod
    def detect_cameras(max_index: int = 10) -> list[int]:
        """Detect available cameras by trying to open each index."""
        available = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
                cap.release()
        return available
    
    @property
    def is_running(self) -> bool:
        return len(self.threads) > 0 and any(t.isRunning() for t in self.threads)
    
    @property
    def num_cameras(self) -> int:
        return len(self.camera_indices)
