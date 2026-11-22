"""全局视觉主题：黑夜 / 白天两套配色 + 集中式样式表，改外观只改这个文件。

用法：`theme.apply(app, "dark" | "light")`，运行中可再次调用切换。
模块级颜色名（theme.CYAN 等）会随当前模式更新，各面板随时取用即可。
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QWidget

# 按平台给字体：列出本机不存在的字体族会让 Qt 每次启动多花 ~350ms 建别名
if sys.platform == "win32":
    UI_FAMILIES = ["Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", "Arial"]
    MONO_FAMILIES = ["Consolas", "Courier New"]
else:
    UI_FAMILIES = ["PingFang SC", "Helvetica Neue", "Arial"]
    MONO_FAMILIES = ["Menlo", "Monaco", "Courier New"]

DARK = {
    "BG": "#1a2236",
    "SURFACE": "#202a3e",
    "SURFACE_2": "#27324a",
    "SURFACE_3": "#2f3b56",
    "INPUT_BG": "#141c2c",
    "PRESSED": "#101828",
    "BORDER": "#2e3950",
    "BORDER_HI": "#43516e",
    "TEXT": "#E8EEF8",
    "TEXT_DIM": "#9AA9C0",
    "TEXT_FAINT": "#6D7C97",
    "CYAN": "#4FD6E8",
    "PURPLE": "#A99BFF",
    "CYAN_HI": "#6FE0EF",
    "PURPLE_HI": "#BCB0FF",
    "CYAN_LO": "#3FBECF",
    "PURPLE_LO": "#9384EE",
    "ACCENT_RGB": "79, 214, 232",
    "PRIMARY_TEXT": "#082028",
    "SEL_TEXT": "#082028",
    "SCROLL": "#2C3647",
    "SCROLL_HI": "#465469",
    "DANGER": "#FF6B81",
    "OK": "#4ADE80",
    "WARN": "#F5B942",
}

LIGHT = {
    "BG": "#EEF2F8",
    "SURFACE": "#FFFFFF",
    "SURFACE_2": "#F2F5FA",
    "SURFACE_3": "#E6ECF5",
    "INPUT_BG": "#FFFFFF",
    "PRESSED": "#DFE6F1",
    "BORDER": "#D8E0EC",
    "BORDER_HI": "#B9C5D6",
    "TEXT": "#16202F",
    "TEXT_DIM": "#4B5A72",
    "TEXT_FAINT": "#6C7C93",
    "CYAN": "#0B7A90",
    "PURPLE": "#5B4DD1",
    "CYAN_HI": "#0E8CA4",
    "PURPLE_HI": "#6C5CE7",
    "CYAN_LO": "#086A7D",
    "PURPLE_LO": "#4C3FBB",
    "ACCENT_RGB": "11, 122, 144",
    "PRIMARY_TEXT": "#FFFFFF",
    "SEL_TEXT": "#FFFFFF",
    "SCROLL": "#C8D2E0",
    "SCROLL_HI": "#A9B6C8",
    "DANGER": "#D93B52",
    "OK": "#1E9E5B",
    "WARN": "#B8791B",
}

MODE = "dark"
globals().update(DARK)


def _qss() -> str:
    t = globals()
    return f"""
QWidget {{
    color: {t['TEXT']};
    selection-background-color: {t['CYAN']};
    selection-color: {t['SEL_TEXT']};
}}
QMainWindow, QDialog, QMessageBox {{ background: {t['BG']}; }}

/* 面板卡片 */
QWidget#panel {{
    background: {t['SURFACE']};
    border: 1px solid {t['BORDER']};
    border-radius: 14px;
}}

/* 文字层级 */
QLabel {{ background: transparent; }}
QLabel#eyebrow {{ color: {t['TEXT_DIM']}; font-size: 11px; font-weight: 700; }}
QLabel#brand {{ font-size: 17px; font-weight: 700; }}
QLabel#brandSub {{ font-size: 10px; color: {t['TEXT_FAINT']}; }}
QLabel#dim {{ color: {t['TEXT_DIM']}; font-size: 11px; }}
QLabel#count {{
    color: {t['CYAN']};
    background: rgba({t['ACCENT_RGB']}, 12%);
    border: 1px solid rgba({t['ACCENT_RGB']}, 30%);
    border-radius: 9px;
    padding: 1px 8px;
    font-size: 10px;
}}

/* 按钮 */
QPushButton {{
    background: {t['SURFACE_2']};
    color: {t['TEXT']};
    border: 1px solid {t['BORDER']};
    border-radius: 9px;
    padding: 7px 16px;
}}
QPushButton:hover {{ background: {t['SURFACE_3']}; border-color: {t['BORDER_HI']}; }}
QPushButton:pressed {{ background: {t['PRESSED']}; }}
QPushButton:focus {{ border-color: {t['CYAN']}; }}
QPushButton:disabled {{ color: {t['TEXT_FAINT']}; background: {t['SURFACE']}; border-color: {t['BORDER']}; }}

QPushButton[variant="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t['CYAN']}, stop:1 {t['PURPLE']});
    color: {t['PRIMARY_TEXT']};
    border: 1px solid transparent;
    font-weight: 700;
}}
QPushButton[variant="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t['CYAN_HI']}, stop:1 {t['PURPLE_HI']});
}}
QPushButton[variant="primary"]:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t['CYAN_LO']}, stop:1 {t['PURPLE_LO']});
}}
QPushButton[variant="primary"]:disabled {{
    background: {t['SURFACE_2']};
    color: {t['TEXT_FAINT']};
    border: 1px solid {t['BORDER']};
}}

QPushButton#plus {{
    padding: 0;
    font-size: 15px;
    font-weight: 700;
    border-radius: 7px;
}}

QPushButton[variant="accent"] {{
    background: transparent;
    color: {t['CYAN']};
    border: 1px solid rgba({t['ACCENT_RGB']}, 50%);
}}
QPushButton[variant="accent"]:hover {{
    background: rgba({t['ACCENT_RGB']}, 12%);
    border-color: {t['CYAN']};
}}

QPushButton[variant="ghost"] {{
    background: transparent;
    color: {t['TEXT_DIM']};
    border: 1px solid transparent;
}}
QPushButton[variant="ghost"]:hover {{
    background: {t['SURFACE_2']};
    color: {t['TEXT']};
    border-color: {t['BORDER']};
}}
QPushButton[variant="ghost"]:disabled {{ color: {t['TEXT_FAINT']}; background: transparent; }}

/* 输入 */
QLineEdit {{
    background: {t['INPUT_BG']};
    border: 1px solid {t['BORDER']};
    border-radius: 9px;
    padding: 7px 11px;
    color: {t['TEXT']};
}}
QLineEdit:hover {{ border-color: {t['BORDER_HI']}; }}
QLineEdit:focus {{ border-color: {t['CYAN']}; }}
QLineEdit:read-only {{ color: {t['TEXT_DIM']}; }}

QPlainTextEdit {{
    background: {t['INPUT_BG']};
    border: 1px solid {t['BORDER']};
    border-radius: 12px;
    padding: 12px;
    color: {t['TEXT']};
}}
QPlainTextEdit:hover {{ border-color: {t['BORDER_HI']}; }}
QPlainTextEdit:focus {{ border-color: rgba({t['ACCENT_RGB']}, 62%); }}

/* 列表 */
QListWidget {{
    background: transparent;
    border: none;
    outline: 0;
    padding: 2px;
}}
QListWidget::item {{
    color: {t['TEXT_DIM']};
    padding: 9px 11px;
    border: 1px solid transparent;
    border-radius: 10px;
}}
QListWidget::item:hover {{ background: {t['SURFACE_2']}; color: {t['TEXT']}; }}
QListWidget::item:selected {{
    background: rgba({t['ACCENT_RGB']}, 10%);
    border: 1px solid rgba({t['ACCENT_RGB']}, 45%);
    color: {t['TEXT']};
}}

/* 滚动条 */
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t['SCROLL']}; border-radius: 4px; min-height: 32px; }}
QScrollBar::handle:vertical:hover {{ background: {t['SCROLL_HI']}; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {t['SCROLL']}; border-radius: 4px; min-width: 32px; }}
QScrollBar::handle:horizontal:hover {{ background: {t['SCROLL_HI']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* 分隔条 */
QSplitter::handle {{ background: transparent; }}
QSplitter::handle:horizontal {{ width: 10px; }}
QSplitter::handle:hover {{ background: rgba({t['ACCENT_RGB']}, 14%); border-radius: 5px; }}

/* 勾选框 */
QCheckBox {{ color: {t['TEXT_DIM']}; spacing: 8px; }}
QCheckBox:hover {{ color: {t['TEXT']}; }}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 5px;
    border: 1px solid {t['BORDER_HI']};
    background: {t['INPUT_BG']};
}}
QCheckBox::indicator:hover {{ border-color: {t['CYAN']}; }}
QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t['CYAN']}, stop:1 {t['PURPLE']});
    border: 1px solid transparent;
}}

/* 菜单与提示 */
QMenu {{
    background: {t['SURFACE']};
    border: 1px solid {t['BORDER_HI']};
    border-radius: 10px;
    padding: 6px;
    color: {t['TEXT']};
}}
QMenu::item {{ padding: 7px 18px; border-radius: 7px; }}
QMenu::item:selected {{ background: rgba({t['ACCENT_RGB']}, 16%); color: {t['TEXT']}; }}
QMenu::separator {{ height: 1px; background: {t['BORDER']}; margin: 5px 8px; }}
QMenuBar {{ background: {t['BG']}; color: {t['TEXT_DIM']}; }}
QMenuBar::item {{ padding: 4px 10px; background: transparent; border-radius: 6px; }}
QMenuBar::item:selected {{ background: {t['SURFACE_2']}; color: {t['TEXT']}; }}
QToolTip {{
    background: {t['SURFACE_3']};
    color: {t['TEXT']};
    border: 1px solid {t['BORDER_HI']};
    border-radius: 8px;
    padding: 6px 9px;
}}

/* 分组框 */
QGroupBox {{
    border: 1px solid {t['BORDER']};
    border-radius: 12px;
    margin-top: 14px;
    padding: 12px 12px 10px 12px;
    color: {t['TEXT_DIM']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {t['TEXT_FAINT']};
}}
"""


def as_panel(widget: QWidget) -> QWidget:
    """普通 QWidget 要被 QSS 画上卡片底色，必须显式开启 styled background。"""
    widget.setObjectName("panel")
    widget.setAttribute(Qt.WA_StyledBackground, True)
    return widget


def variant(widget: QWidget, name: str) -> QWidget:
    """给 QPushButton 之类的控件打上 variant 属性，驱动上面的样式分支。"""
    widget.setProperty("variant", name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    return widget


def mono_font(size: int = 13, weight: QFont.Weight = QFont.Normal) -> QFont:
    """等宽字体：提示词正文用，读代码块更整齐。"""
    font = QFont()
    font.setFamilies(MONO_FAMILIES)
    font.setPointSize(size)
    font.setWeight(weight)
    return font


def accent_pair():
    """当前模式的强调色（青, 紫），给自绘控件用。"""
    return QColor(CYAN), QColor(PURPLE)


def _palette() -> QPalette:
    t = globals()
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(t['BG']))
    pal.setColor(QPalette.WindowText, QColor(t['TEXT']))
    pal.setColor(QPalette.Base, QColor(t['INPUT_BG']))
    pal.setColor(QPalette.AlternateBase, QColor(t['SURFACE']))
    pal.setColor(QPalette.Text, QColor(t['TEXT']))
    pal.setColor(QPalette.Button, QColor(t['SURFACE_2']))
    pal.setColor(QPalette.ButtonText, QColor(t['TEXT']))
    pal.setColor(QPalette.Highlight, QColor(t['CYAN']))
    pal.setColor(QPalette.HighlightedText, QColor(t['SEL_TEXT']))
    pal.setColor(QPalette.ToolTipBase, QColor(t['SURFACE_3']))
    pal.setColor(QPalette.ToolTipText, QColor(t['TEXT']))
    pal.setColor(QPalette.PlaceholderText, QColor(t['TEXT_FAINT']))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor(t['TEXT_FAINT']))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(t['TEXT_FAINT']))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor(t['TEXT_FAINT']))
    return pal


def apply(app: QApplication, mode: str = "dark") -> None:
    """应用配色；运行中再次调用即切换模式。"""
    global MODE
    MODE = "light" if mode == "light" else "dark"
    globals().update(LIGHT if MODE == "light" else DARK)

    # 声明配色，macOS 原生标题栏才会跟着变（否则黑身白头）
    app.styleHints().setColorScheme(Qt.ColorScheme.Light if MODE == "light" else Qt.ColorScheme.Dark)
    app.setStyle("Fusion")

    font = QFont()
    font.setFamilies(UI_FAMILIES)
    font.setPointSize(13)
    app.setFont(font)

    app.setPalette(_palette())
    app.setStyleSheet(_qss())
