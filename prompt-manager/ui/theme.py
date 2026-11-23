"""全局视觉主题：黑夜 / 白天两套配色 + 集中式样式表，改外观只改这个文件。

用法：`theme.apply(app, "dark" | "light")`，运行中可再次调用切换。
模块级颜色名（theme.CYAN 等）会随当前模式更新，各面板随时取用即可。
整体字号由 FONT_SCALE 统一放大缩小（设置页可调），所有字号都写在一个单位里。
"""

import sys
import weakref

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
    "PRIMARY_TEXT": "#FFFFFF",
    "SEL_TEXT": "#FFFFFF",
    "SCROLL": "#C8D2E0",
    "SCROLL_HI": "#A9B6C8",
    "DANGER": "#D93B52",
    "OK": "#1E9E5B",
    "WARN": "#B8791B",
}

# 主体风格配色：名称 → (显示名, 主色, 副色)，主副两色组成按钮渐变
ACCENTS = {
    "cyan":   ("青紫", "#4FD6E8", "#A99BFF"),
    "blue":   ("蓝",   "#3B82F6", "#22D3EE"),
    "indigo": ("靛蓝", "#6366F1", "#818CF8"),
    "purple": ("紫",   "#A78BFA", "#7C3AED"),
    "pink":   ("粉",   "#F472B6", "#FB7185"),
    "red":    ("红",   "#EF4444", "#F87171"),
    "orange": ("橙",   "#FB923C", "#F97316"),
    "yellow": ("黄",   "#FBBF24", "#F59E0B"),
    "lime":   ("黄绿", "#A3E635", "#84CC16"),
    "green":  ("绿",   "#34D399", "#22C55E"),
    "teal":   ("青绿", "#2DD4BF", "#14B8A6"),
    "gray":   ("灰",   "#94A3B8", "#64748B"),
}

MODE = "dark"
ACCENT = "cyan"

# 整体字号倍率：设置页 ±10% 调整，范围 80%~140%
MIN_SCALE = 0.8
MAX_SCALE = 1.4
SCALE_STEP = 0.1
FONT_SCALE = 1.0

globals().update(DARK)


def _f(px: float, cap: float = 0) -> str:
    """把一个基准像素值按当前倍率换算成 QSS 字号；cap 防止图标按钮里的字撑破方块。"""
    v = px * FONT_SCALE
    if cap:
        v = min(v, cap)
    return f"{max(9, round(v))}px"


def px(n: float) -> int:
    """同理换算固定几何（方形小按钮边长等），避免放大字号后被裁掉。"""
    return max(1, round(n * FONT_SCALE))


def _contrast(a: QColor, b: QColor) -> float:
    def lum(c):
        def f(v):
            v /= 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c.red()) + 0.7152 * f(c.green()) + 0.0722 * f(c.blue())
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _readable_on_white(color: QColor) -> QColor:
    """浅色模式下把强调色压暗到与白底对比 ≥4.5:1，保证文字可读。"""
    out = QColor(color)
    for _ in range(24):
        if _contrast(out, QColor("#FFFFFF")) >= 4.5:
            break
        out = out.darker(112)
    return out


def _hsl(hue: int, sat: float, light: float) -> str:
    return QColor.fromHslF((hue % 360) / 360.0, max(0.0, min(1.0, sat)),
                           max(0.0, min(1.0, light))).name()


def _surfaces(mode: str, accent: str) -> dict:
    """非默认风格时，把底色板按强调色色相重新着色（明度层次保持不变）。

    默认的青紫风格保留原先手调的 #1a2236 系列，不做推导。
    """
    main = QColor(ACCENTS[accent][1])
    hue = int(main.hueF() * 360) if main.hueF() >= 0 else 220
    if mode == "light":
        return {
            "BG": _hsl(hue, 0.16, 0.952),
            "SURFACE": "#FFFFFF",
            "SURFACE_2": _hsl(hue, 0.18, 0.945),
            "SURFACE_3": _hsl(hue, 0.20, 0.900),
            "INPUT_BG": _hsl(hue, 0.12, 0.985),
            "PRESSED": _hsl(hue, 0.20, 0.880),
            "BORDER": _hsl(hue, 0.18, 0.870),
            "BORDER_HI": _hsl(hue, 0.16, 0.760),
            "SCROLL": _hsl(hue, 0.16, 0.820),
            "SCROLL_HI": _hsl(hue, 0.16, 0.680),
        }
    sat = min(max(main.saturationF() * 0.45, 0.10), 0.26)
    return {
        "BG": _hsl(hue, sat, 0.157),
        "SURFACE": _hsl(hue, sat, 0.184),
        "SURFACE_2": _hsl(hue, sat, 0.221),
        "SURFACE_3": _hsl(hue, sat, 0.261),
        "INPUT_BG": _hsl(hue, sat * 0.85, 0.126),
        "PRESSED": _hsl(hue, sat * 0.9, 0.110),
        "BORDER": _hsl(hue, sat * 0.8, 0.247),
        "BORDER_HI": _hsl(hue, sat * 0.9, 0.347),
        "SCROLL": _hsl(hue, sat * 0.7, 0.226),
        "SCROLL_HI": _hsl(hue, sat * 0.8, 0.343),
    }


def _accent_tokens(mode: str, accent: str) -> dict:
    _, main, second = ACCENTS.get(accent, ACCENTS["cyan"])
    c1, c2 = QColor(main), QColor(second)
    if mode == "light":
        c1, c2 = _readable_on_white(c1), _readable_on_white(c2)
    return {
        "CYAN": c1.name(),
        "PURPLE": c2.name(),
        "CYAN_HI": c1.lighter(112).name(),
        "PURPLE_HI": c2.lighter(112).name(),
        "CYAN_LO": c1.darker(112).name(),
        "PURPLE_LO": c2.darker(112).name(),
        "ACCENT_RGB": f"{c1.red()}, {c1.green()}, {c1.blue()}",
    }


globals().update(_accent_tokens(MODE, ACCENT))


def swatch_color(key: str) -> str:
    """色盘里该风格在当前模式下应显示的颜色。"""
    return _accent_tokens(MODE, key)["CYAN"]


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
QLabel#eyebrow {{ color: {t['TEXT_DIM']}; font-size: {_f(12)}; font-weight: 700; }}
QLabel#brand {{ font-size: {_f(18)}; font-weight: 700; }}
QLabel#brandSub {{ font-size: {_f(11)}; color: {t['TEXT_FAINT']}; }}
QLabel#dim {{ color: {t['TEXT_DIM']}; font-size: {_f(12)}; }}
QLabel#count {{
    color: {t['CYAN']};
    background: rgba({t['ACCENT_RGB']}, 12%);
    border: 1px solid rgba({t['ACCENT_RGB']}, 30%);
    border-radius: 9px;
    padding: 1px 8px;
    font-size: {_f(11)};
}}

/* 按钮 */
QPushButton {{
    background: {t['SURFACE_2']};
    color: {t['TEXT']};
    border: 1px solid {t['BORDER']};
    border-radius: 9px;
    font-size: {_f(13)};
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
    font-size: {_f(16, cap=19)};
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
QPushButton[variant="accent"]:pressed,
QPushButton[variant="accent"]:checked {{
    background: rgba({t['ACCENT_RGB']}, 22%);
    border-color: {t['CYAN']};
    color: {t['CYAN_HI']};
}}
QPushButton[variant="accent"]:disabled {{
    color: {t['TEXT_FAINT']};
    border-color: {t['BORDER']};
    background: transparent;
}}

QPushButton[variant="outline"] {{
    background: transparent;
    color: {t['TEXT']};
    border: 1px solid {t['BORDER_HI']};
}}
QPushButton[variant="outline"]:hover {{
    background: rgba({t['ACCENT_RGB']}, 10%);
    border-color: {t['CYAN']};
    color: {t['CYAN']};
}}
QPushButton[variant="outline"]:pressed {{ background: rgba({t['ACCENT_RGB']}, 20%); }}
QPushButton[variant="outline"]:disabled {{
    color: {t['TEXT_FAINT']};
    background: transparent;
    border-color: {t['BORDER']};
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
    font-size: {_f(14)};
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
    font-size: {_f(14)};
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
QCheckBox {{ color: {t['TEXT_DIM']}; font-size: {_f(13)}; spacing: 8px; }}
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
    font-size: {_f(13)};
    padding: 6px;
    color: {t['TEXT']};
}}
QMenu::item {{ padding: 7px 18px; border-radius: 7px; }}
QMenu::item:selected {{ background: rgba({t['ACCENT_RGB']}, 16%); color: {t['TEXT']}; }}
QMenu::separator {{ height: 1px; background: {t['BORDER']}; margin: 5px 8px; }}
QMenuBar {{ background: {t['BG']}; color: {t['TEXT_DIM']}; font-size: {_f(13)}; }}
QMenuBar::item {{ padding: 4px 10px; background: transparent; border-radius: 6px; }}
QMenuBar::item:selected {{ background: {t['SURFACE_2']}; color: {t['TEXT']}; }}
QToolTip {{
    background: {t['SURFACE_3']};
    color: {t['TEXT']};
    border: 1px solid {t['BORDER_HI']};
    border-radius: 8px;
    font-size: {_f(13)};
    padding: 6px 9px;
}}

/* 分组框 */
QGroupBox {{
    border: 1px solid {t['BORDER']};
    border-radius: 12px;
    margin-top: 14px;
    font-size: {_f(13)};
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
    """等宽字体：提示词正文用，读代码块更整齐。字号跟随整体倍率。"""
    font = QFont()
    font.setFamilies(MONO_FAMILIES)
    font.setPointSizeF(size * FONT_SCALE)
    font.setWeight(weight)
    return font


# 自己设过 QFont 的控件（编辑器正文）不会被 QSS 覆盖，切倍率时需要重设一次
_MONO_WIDGETS = []


def apply_mono(widget: QWidget, size: int = 13) -> QWidget:
    """给正文编辑框套等宽字体，并登记以便整体字号变化时同步。"""
    widget.setFont(mono_font(size))
    _MONO_WIDGETS.append((weakref.ref(widget), size))
    return widget


def _refresh_mono():
    alive = []
    for ref, size in _MONO_WIDGETS:
        widget = ref()
        if widget is not None:
            widget.setFont(mono_font(size))
            alive.append((ref, size))
    _MONO_WIDGETS[:] = alive


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


def apply(app: QApplication, mode: str = "dark", accent: str = "cyan",
          scale: float = None) -> None:
    """应用配色与字号；运行中再次调用即切换模式、主体风格色或整体字号。

    scale 省略时沿用当前倍率，所以只切配色/风格的调用点不用改。
    """
    global MODE, ACCENT, FONT_SCALE
    MODE = "light" if mode == "light" else "dark"
    ACCENT = accent if accent in ACCENTS else "cyan"
    if scale is not None:
        FONT_SCALE = max(MIN_SCALE, min(MAX_SCALE, round(float(scale), 2)))
    globals().update(LIGHT if MODE == "light" else DARK)
    globals().update(_accent_tokens(MODE, ACCENT))
    if ACCENT != "cyan":
        globals().update(_surfaces(MODE, ACCENT))

    # 声明配色，macOS 原生标题栏才会跟着变（否则黑身白头）
    app.styleHints().setColorScheme(Qt.ColorScheme.Light if MODE == "light" else Qt.ColorScheme.Dark)
    app.setStyle("Fusion")

    font = QFont()
    font.setFamilies(UI_FAMILIES)
    font.setPointSizeF(13 * FONT_SCALE)
    app.setFont(font)

    app.setPalette(_palette())
    app.setStyleSheet(_qss())
    _refresh_mono()
