"""线性图标：全部用 QPainter 现画，不依赖图标文件或第三方库。

风格统一为 1.6px 圆头描边、几何对称、无多余细节。
主题切换后调用 recolor_all() 重新着色（QIcon 是静态位图，不会跟着 QSS 变）。
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QPushButton

from . import theme

BOX = 16.0          # 绘制坐标盒
STROKE = 1.6

ROLES = {
    "accent": lambda: theme.CYAN,
    "text": lambda: theme.TEXT,
    "dim": lambda: theme.TEXT_DIM,
    "primary": lambda: theme.PRIMARY_TEXT,
}


def _pen(color: QColor, width: float = STROKE) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _draw(kind: str, p: QPainter, color: QColor) -> None:
    p.setPen(_pen(color))
    p.setBrush(Qt.NoBrush)
    c = BOX / 2.0

    if kind == "plus":
        p.drawLine(QPointF(c - 4.4, c), QPointF(c + 4.4, c))
        p.drawLine(QPointF(c, c - 4.4), QPointF(c, c + 4.4))

    elif kind == "sun":
        p.drawEllipse(QPointF(c, c), 3.1, 3.1)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0),
                       (-0.71, -0.71), (0.71, -0.71), (-0.71, 0.71), (0.71, 0.71)):
            p.drawLine(QPointF(c + dx * 5.4, c + dy * 5.4),
                       QPointF(c + dx * 7.0, c + dy * 7.0))

    elif kind == "moon":
        path = QPainterPath()
        path.addEllipse(QRectF(c - 4.6, c - 5.6, 10.2, 11.2))
        cut = QPainterPath()
        cut.addEllipse(QRectF(c - 1.4, c - 6.2, 9.2, 11.2))
        p.drawPath(path.subtracted(cut))

    elif kind == "star":                       # 保存到我的提示词
        pts = []
        for i in range(10):
            ang = -3.14159 / 2 + i * 3.14159 / 5
            r = 6.2 if i % 2 == 0 else 2.9
            pts.append(QPointF(c + r * __import__("math").cos(ang),
                               c + r * __import__("math").sin(ang)))
        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        p.drawPath(path)

    elif kind == "sparkle":                    # 优化提示词
        for cx, cy, r in ((c - 0.6, c - 0.8, 5.6), (c + 4.2, c + 4.0, 2.4)):
            p.drawLine(QPointF(cx, cy - r), QPointF(cx + r * 0.42, cy - r * 0.42))
            p.drawLine(QPointF(cx + r * 0.42, cy - r * 0.42), QPointF(cx + r, cy))
            p.drawLine(QPointF(cx + r, cy), QPointF(cx + r * 0.42, cy + r * 0.42))
            p.drawLine(QPointF(cx + r * 0.42, cy + r * 0.42), QPointF(cx, cy + r))
            p.drawLine(QPointF(cx, cy + r), QPointF(cx - r * 0.42, cy + r * 0.42))
            p.drawLine(QPointF(cx - r * 0.42, cy + r * 0.42), QPointF(cx - r, cy))
            p.drawLine(QPointF(cx - r, cy), QPointF(cx - r * 0.42, cy - r * 0.42))
            p.drawLine(QPointF(cx - r * 0.42, cy - r * 0.42), QPointF(cx, cy - r))

    elif kind == "align":                      # 整理格式
        for i, w in enumerate((9.6, 6.4, 8.4, 5.0)):
            y = c - 4.6 + i * 3.05
            p.drawLine(QPointF(c - 4.8, y), QPointF(c - 4.8 + w, y))

    elif kind == "chip":                       # 深度思考
        p.drawRoundedRect(QRectF(c - 4.4, c - 4.4, 8.8, 8.8), 1.6, 1.6)
        p.drawEllipse(QPointF(c, c), 1.5, 1.5)
        for a in (-3.2, 0.0, 3.2):
            p.drawLine(QPointF(c + a, c - 5.9), QPointF(c + a, c - 4.4))
            p.drawLine(QPointF(c + a, c + 4.4), QPointF(c + a, c + 5.9))
            p.drawLine(QPointF(c - 5.9, c + a), QPointF(c - 4.4, c + a))
            p.drawLine(QPointF(c + 4.4, c + a), QPointF(c + 5.9, c + a))

    elif kind == "brush":                      # 清空历史
        handle = QPen(color)
        handle.setWidthF(1.5)
        handle.setCapStyle(Qt.RoundCap)
        p.setPen(handle)
        p.drawLine(QPointF(c + 3.4, c - 3.4), QPointF(c + 0.3, c + 0.3))
        head = QPen(color)
        head.setWidthF(3.6)
        head.setCapStyle(Qt.FlatCap)
        p.setPen(head)
        p.drawLine(QPointF(c - 0.2, c + 0.8), QPointF(c - 3.4, c + 4.0))
        tip = QPen(color)
        tip.setWidthF(1.1)
        tip.setCapStyle(Qt.RoundCap)
        p.setPen(tip)
        p.drawLine(QPointF(c - 3.9, c + 4.2), QPointF(c - 4.6, c + 5.8))
        p.drawLine(QPointF(c - 2.3, c + 4.2), QPointF(c - 3.0, c + 5.8))

    elif kind == "palette":                    # 打开主体色板
        p.drawEllipse(QPointF(c, c), 5.8, 5.4)
        p.save()
        p.setBrush(color)
        p.setPen(Qt.NoPen)
        for dx, dy in ((-1.9, -2.3), (2.1, -1.6), (2.4, 2.0), (-2.2, 2.2)):
            p.drawEllipse(QPointF(c + dx, c + dy), 1.15, 1.15)
        p.restore()

    elif kind == "copy":
        back = QPainterPath()
        back.addRoundedRect(QRectF(c - 5.6, c - 5.6, 7.4, 7.4), 1.8, 1.8)
        front = QPainterPath()
        front.addRoundedRect(QRectF(c - 1.2, c - 1.2, 7.4, 7.4), 1.8, 1.8)
        p.drawPath(back)
        p.setBrush(QColor(theme.SURFACE))          # 让前件压掉后件的线
        p.drawPath(front)

    elif kind == "check":                          # 复制成功后的对勾
        p.drawLine(QPointF(c - 4.6, c + 0.2), QPointF(c - 1.4, c + 3.4))
        p.drawLine(QPointF(c - 1.4, c + 3.4), QPointF(c + 4.8, c - 3.4))


def make(kind: str, role: str = "text", px: int = 16) -> QIcon:
    color = QColor(ROLES.get(role, ROLES["text"])())
    pix = QPixmap(px, px)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    try:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.scale(px / BOX, px / BOX)
        _draw(kind, painter, color)
    finally:
        painter.end()
    return QIcon(pix)


class IconButton(QPushButton):
    """带线性图标的按钮；主题切换后由 recolor_all() 统一换色。"""

    def __init__(self, text: str, kind: str, role: str = "text", icon_px: int = 16, parent=None):
        super().__init__(text, parent)
        self._kind = kind
        self._role = role
        self._icon_px = icon_px
        self.setIcon(make(kind, role, icon_px))
        self.setIconSize(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(icon_px, icon_px))

    def refresh_icon(self) -> None:
        self.setIcon(make(self._kind, self._role, self._icon_px))

    def set_kind(self, kind: str) -> None:
        self._kind = kind
        self.refresh_icon()


def recolor_all() -> None:
    """主题/主体色切换后调用：把所有 IconButton 的图标按当前配色重画。"""
    app = QApplication.instance()
    if app is None:
        return
    for w in app.allWidgets():
        if isinstance(w, IconButton):
            w.refresh_icon()
