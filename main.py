"""
OfflineDarts — Offline Automatic Dart Scoring Desktop Application

Usage:
    python main.py

Requires:
    - Python 3.11+
    - 3 USB webcams (OV9732 recommended)
    - LED ring light around dartboard
    - Install dependencies: pip install -r requirements.txt
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from ui.app import MainWindow


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("OfflineDarts")
    app.setApplicationVersion("1.0.0")
    
    # Set default font
    font = QFont("Inter", 13)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.showMaximized()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
