"""
Premium dark theme for the OfflineDarts application.
Defines styles, colors, and the global stylesheet for PyQt6 widgets.
"""

from config import COLORS, FONT_FAMILY


def get_stylesheet() -> str:
    """Generate the global application stylesheet."""
    c = COLORS
    
    return f"""
    /* ── Global ─────────────────────────────────────────── */
    QMainWindow, QWidget {{
        background-color: {c["bg_primary"]};
        color: {c["text_primary"]};
        font-family: {FONT_FAMILY};
        font-size: 14px;
    }}
    
    /* ── Labels ─────────────────────────────────────────── */
    QLabel {{
        color: {c["text_primary"]};
        background: transparent;
    }}
    
    QLabel[class="heading"] {{
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -1px;
    }}
    
    QLabel[class="subheading"] {{
        font-size: 18px;
        font-weight: 500;
        color: {c["text_secondary"]};
    }}
    
    QLabel[class="score-big"] {{
        font-size: 72px;
        font-weight: 800;
        color: {c["accent"]};
    }}
    
    QLabel[class="score-medium"] {{
        font-size: 36px;
        font-weight: 700;
    }}
    
    QLabel[class="muted"] {{
        color: {c["text_muted"]};
        font-size: 12px;
    }}
    
    /* ── Buttons ────────────────────────────────────────── */
    QPushButton {{
        background-color: {c["bg_card"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 15px;
        font-weight: 600;
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background-color: {c["bg_elevated"]};
        border-color: {c["accent_dim"]};
    }}
    
    QPushButton:pressed {{
        background-color: {c["accent_dim"]};
        color: {c["bg_primary"]};
    }}
    
    QPushButton[class="primary"] {{
        background-color: {c["accent"]};
        color: {c["bg_primary"]};
        border: none;
        font-weight: 700;
    }}
    
    QPushButton[class="primary"]:hover {{
        background-color: {c["accent_dim"]};
    }}
    
    QPushButton[class="danger"] {{
        background-color: transparent;
        color: {c["danger"]};
        border-color: {c["danger"]};
    }}
    
    QPushButton[class="danger"]:hover {{
        background-color: {c["danger"]};
        color: white;
    }}
    
    QPushButton[class="ghost"] {{
        background: transparent;
        border: none;
        color: {c["text_secondary"]};
    }}
    
    QPushButton[class="ghost"]:hover {{
        color: {c["accent"]};
    }}
    
    /* ── Input Fields ──────────────────────────────────── */
    QLineEdit {{
        background-color: {c["bg_card"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 15px;
        selection-background-color: {c["accent_dim"]};
    }}
    
    QLineEdit:focus {{
        border-color: {c["accent"]};
    }}
    
    QLineEdit::placeholder {{
        color: {c["text_muted"]};
    }}
    
    /* ── Combo Box ─────────────────────────────────────── */
    QComboBox {{
        background-color: {c["bg_card"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 15px;
        min-width: 120px;
    }}
    
    QComboBox:hover {{
        border-color: {c["accent_dim"]};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {c["bg_card"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        selection-background-color: {c["bg_elevated"]};
    }}
    
    /* ── Spin Box ──────────────────────────────────────── */
    QSpinBox {{
        background-color: {c["bg_card"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 15px;
    }}
    
    /* ── Scroll Area ───────────────────────────────────── */
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    
    QScrollBar:vertical {{
        background-color: {c["bg_secondary"]};
        width: 8px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {c["border_light"]};
        border-radius: 4px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {c["accent_dim"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* ── Frame (Card) ──────────────────────────────────── */
    QFrame[class="card"] {{
        background-color: {c["bg_card"]};
        border: 1px solid {c["border"]};
        border-radius: 16px;
        padding: 20px;
    }}
    
    QFrame[class="card-glow"] {{
        background-color: {c["bg_card"]};
        border: 1px solid {c["accent_dim"]};
        border-radius: 16px;
        padding: 20px;
    }}
    
    /* ── Separator ─────────────────────────────────────── */
    QFrame[class="separator"] {{
        background-color: {c["border"]};
        max-height: 1px;
    }}
    
    /* ── Tab Widget ────────────────────────────────────── */
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    
    QTabBar::tab {{
        background: transparent;
        color: {c["text_muted"]};
        padding: 12px 20px;
        font-size: 14px;
        font-weight: 600;
        border-bottom: 2px solid transparent;
    }}
    
    QTabBar::tab:selected {{
        color: {c["accent"]};
        border-bottom: 2px solid {c["accent"]};
    }}
    
    QTabBar::tab:hover {{
        color: {c["text_primary"]};
    }}
    
    /* ── Group Box ─────────────────────────────────────── */
    QGroupBox {{
        background-color: {c["bg_card"]};
        border: 1px solid {c["border"]};
        border-radius: 12px;
        margin-top: 12px;
        padding-top: 24px;
        font-weight: 600;
    }}
    
    QGroupBox::title {{
        color: {c["text_secondary"]};
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
    """


def card_style(glow: bool = False) -> str:
    """Inline style for card-like containers."""
    c = COLORS
    border = c["accent_dim"] if glow else c["border"]
    return (
        f"background-color: {c['bg_card']}; "
        f"border: 1px solid {border}; "
        f"border-radius: 16px; "
        f"padding: 20px;"
    )


def accent_text_style(size: int = 14) -> str:
    """Inline style for accent-colored text."""
    return f"color: {COLORS['accent']}; font-size: {size}px; font-weight: 700;"


def danger_text_style(size: int = 14) -> str:
    """Inline style for danger/error text."""
    return f"color: {COLORS['danger']}; font-size: {size}px; font-weight: 700;"
