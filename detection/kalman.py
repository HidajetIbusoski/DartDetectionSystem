"""
Kalman Filter for dart tip position stabilization.
Smooths jittery tip detections across frames using a linear Kalman filter.
"""

import numpy as np

from config import (
    KALMAN_DT, KALMAN_U_X, KALMAN_U_Y,
    KALMAN_STD_ACC, KALMAN_X_STD_MEAS, KALMAN_Y_STD_MEAS
)


class KalmanFilter:
    """
    2D Kalman filter for tracking dart tip position.
    
    State vector: [x, y, vx, vy]
    Measurement vector: [x, y]
    
    Uses a constant-velocity motion model with acceleration noise.
    """
    
    def __init__(self, dt=None, u_x=None, u_y=None,
                 std_acc=None, x_std_meas=None, y_std_meas=None):
        self.dt = dt or KALMAN_DT
        self.u_x = u_x if u_x is not None else KALMAN_U_X
        self.u_y = u_y if u_y is not None else KALMAN_U_Y
        self.std_acc = std_acc or KALMAN_STD_ACC
        
        x_std = x_std_meas or KALMAN_X_STD_MEAS
        y_std = y_std_meas or KALMAN_Y_STD_MEAS
        
        # State transition matrix
        self.A = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float64)
        
        # Control input matrix
        self.B = np.array([
            [(self.dt ** 2) / 2, 0],
            [0, (self.dt ** 2) / 2],
            [self.dt, 0],
            [0, self.dt]
        ], dtype=np.float64)
        
        # Measurement matrix
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float64)
        
        # Process noise covariance
        self.Q = np.array([
            [(self.dt ** 4) / 4, 0, (self.dt ** 3) / 2, 0],
            [0, (self.dt ** 4) / 4, 0, (self.dt ** 3) / 2],
            [(self.dt ** 3) / 2, 0, self.dt ** 2, 0],
            [0, (self.dt ** 3) / 2, 0, self.dt ** 2]
        ], dtype=np.float64) * self.std_acc ** 2
        
        # Measurement noise covariance
        self.R = np.array([
            [x_std ** 2, 0],
            [0, y_std ** 2]
        ], dtype=np.float64)
        
        # State covariance matrix
        self.P = np.eye(4, dtype=np.float64)
        
        # State vector
        self.x = np.zeros((4, 1), dtype=np.float64)
    
    def predict(self) -> np.ndarray:
        """
        Predict the next state.
        Returns the predicted state vector.
        """
        u = np.array([[self.u_x], [self.u_y]], dtype=np.float64)
        self.x = self.A @ self.x + self.B @ u
        self.P = self.A @ self.P @ self.A.T + self.Q
        return self.x
    
    def update(self, z: np.ndarray):
        """
        Update the state with a measurement.
        z: measurement vector [x, y] as shape (2, 1)
        """
        z = np.array(z, dtype=np.float64).reshape(2, 1)
        
        # Innovation
        y = z - self.H @ self.x
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.x = self.x + K @ y
        
        # Update covariance
        I = np.eye(4, dtype=np.float64)
        IKH = I - K @ self.H
        self.P = IKH @ self.P @ IKH.T + K @ self.R @ K.T
    
    def reset(self, x: float = 0, y: float = 0):
        """Reset the filter state."""
        self.x = np.array([[x], [y], [0], [0]], dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64)
    
    @property
    def position(self) -> tuple[float, float]:
        """Get the current estimated position."""
        return float(self.x[0, 0]), float(self.x[1, 0])
