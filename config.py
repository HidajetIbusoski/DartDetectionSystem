"""
OfflineDarts - Application Configuration & Constants
All dartboard dimensions follow WDF/BDO official specifications.
"""

import numpy as np
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets"
CALIBRATION_DIR = DATA_DIR / "calibration"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CALIBRATION_DIR.mkdir(exist_ok=True)

# ─── Camera Settings ─────────────────────────────────────────────────────────
NUM_CAMERAS = 3
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# Default camera indices (user can override in settings)
DEFAULT_CAMERA_INDICES = [0, 1, 2]

# ─── Dartboard Dimensions (mm) ───────────────────────────────────────────────
# Official WDF/BDO dartboard dimensions
DARTBOARD_DIAMETER_MM = 451.0

BULLSEYE_RADIUS_MM = 6.35
OUTER_BULL_RADIUS_MM = 15.9
TRIPLE_RING_INNER_RADIUS_MM = 99.0
TRIPLE_RING_OUTER_RADIUS_MM = 107.0
DOUBLE_RING_INNER_RADIUS_MM = 162.0
DOUBLE_RING_OUTER_RADIUS_MM = 170.0

# Dart tip physical radius
TIP_RADIUS_MM = 1.15

# ─── Dartboard Sector Layout ─────────────────────────────────────────────────
# Sectors in clockwise order starting from the top (12 o'clock position)
# Each sector spans 18 degrees
SECTOR_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
NUM_SECTORS = 20
SECTOR_ANGLE = 360.0 / NUM_SECTORS  # 18 degrees per sector

# ─── Detection Parameters ────────────────────────────────────────────────────
# Image differencing
DIFF_THRESHOLD = 60          # Pixel intensity threshold for diff image
GAUSSIAN_KERNEL = (5, 5)     # Gaussian blur kernel size
MORPH_KERNEL_SIZE = 5        # Morphological operation kernel size

# Dart detection pixel thresholds
MIN_DART_PIXELS = 1000       # Minimum changed pixels to consider a dart hit
MAX_DART_PIXELS = 7500       # Maximum changed pixels (above = noise/movement)
MIN_CORNERS = 40             # Minimum corners to detect a dart shape
MIN_FILTERED_CORNERS = 30    # Minimum corners after filtering

# Corner detection
CORNER_MAX_CORNERS = 640
CORNER_QUALITY = 0.0008
CORNER_MIN_DISTANCE = 1
CORNER_BLOCK_SIZE = 3
CORNER_K = 0.06

# Corner filtering
CORNER_FILTER_X_RANGE = 180  # Max X distance from mean corner
CORNER_FILTER_Y_RANGE = 120  # Max Y distance from mean corner
CORNER_LINE_DISTANCE = 40    # Max distance from fitted line

# Takeout detection
TAKEOUT_THRESHOLD = 18000    # Pixel change threshold for hand/takeout
TAKEOUT_DELAY = 3.0          # Seconds to wait after takeout

# Detection loop timing
DETECTION_SLEEP = 0.1        # Seconds between detection cycles
DART_SETTLE_TIME = 0.2       # Seconds to wait after initial detection

# ─── Kalman Filter Parameters ────────────────────────────────────────────────
KALMAN_DT = 1.0 / CAMERA_FPS
KALMAN_U_X = 0
KALMAN_U_Y = 0
KALMAN_STD_ACC = 1.0
KALMAN_X_STD_MEAS = 0.1
KALMAN_Y_STD_MEAS = 0.1

# ─── Calibration ─────────────────────────────────────────────────────────────
# Reference points on the dartboard for perspective calibration
# These are the outer double ring intersections:
# Point 1: 20/1 boundary (top-right area)
# Point 2: 6/10 boundary (bottom-right area)
# Point 3: 19/3 boundary (bottom-left area)
# Point 4: 11/14 boundary (top-left area)
NUM_CALIBRATION_POINTS = 4

# Target calibration points in normalized dartboard space
# Computed from sector angles and double ring radius
def _compute_calibration_targets():
    """Compute target calibration point positions on a normalized dartboard."""
    radius = DOUBLE_RING_OUTER_RADIUS_MM
    center = np.array([0.0, 0.0])
    
    # Boundary angles for calibration points (in degrees from top, clockwise)
    # 20/1: between sector 0 (20) and sector 1 (1) = 9 degrees from top
    # 6/10: between sector 5 (6) and sector 6 (10) = 99 degrees
    # 19/3: between sector 11 (19) and sector 12 (3) = 189 degrees  
    # 11/14: between sector 15 (11) and sector 16 (14) = 279 degrees
    boundary_angles_deg = [9, 99, 189, 279]
    
    targets = []
    for angle_deg in boundary_angles_deg:
        angle_rad = np.radians(angle_deg - 90)  # Convert to math convention
        x = center[0] + radius * np.cos(angle_rad)
        y = center[1] + radius * np.sin(angle_rad)
        targets.append([x, y])
    
    return np.float32(targets)

CALIBRATION_TARGETS = _compute_calibration_targets()

# ─── Game Defaults ────────────────────────────────────────────────────────────
DEFAULT_X01_START = 501
DARTS_PER_TURN = 3
MAX_PLAYERS = 4

# ─── UI Settings ──────────────────────────────────────────────────────────────
WINDOW_TITLE = "OfflineDarts"
MIN_WINDOW_WIDTH = 1280
MIN_WINDOW_HEIGHT = 800

# Color palette
COLORS = {
    "bg_primary": "#0A0A0F",
    "bg_secondary": "#14141F",
    "bg_card": "#1A1A2E",
    "bg_elevated": "#22223A",
    "accent": "#00FF88",
    "accent_dim": "#00CC6A",
    "accent_glow": "rgba(0, 255, 136, 0.15)",
    "text_primary": "#FFFFFF",
    "text_secondary": "#A0A0B8",
    "text_muted": "#6B6B80",
    "danger": "#FF4757",
    "warning": "#FFA502",
    "success": "#00FF88",
    "border": "#2A2A3E",
    "border_light": "#3A3A50",
    "triple": "#FF3366",
    "double": "#3366FF",
    "bullseye": "#FF0044",
    "outer_bull": "#00CC44",
}

# Fonts
FONT_FAMILY = "Inter, Segoe UI, sans-serif"
FONT_SIZE_XL = 48
FONT_SIZE_LG = 28
FONT_SIZE_MD = 18
FONT_SIZE_SM = 14
FONT_SIZE_XS = 11
