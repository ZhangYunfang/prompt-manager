"""从 icon-source.png 生成 macOS(.icns) 与 Windows(.ico) 图标。

源图会先合成到一层**白色圆角底**上（源图多为透明底，直接放深色 Dock/标题栏里看不清），
再导出各档尺寸。源图建议 ≥512×512；小于该尺寸会被平滑放大，细节会软。
用法：./.venv/bin/python make_icons.py
"""

import os
import subprocess
import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter

SRC = "icon-source.png"
ICONSET = "build/icon.iconset"
MASTER = 1024          # 主图边长，先合成到这个尺寸再缩各档
RADIUS_RATIO = 0.2237   # Big Sur 圆角比例（相对边长）
PADDING_RATIO = 0.12    # 图案四周留白，避免贴边

# macOS .iconset 要求的具体尺寸（像素, 文件名）
SIZES = [
    (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
]


def compose(src: QImage, size: int = MASTER) -> QImage:
    """白底圆角方块打底，源图居中叠在上面；圆角外保持透明。"""
    out = QImage(size, size, QImage.Format_ARGB32)
    out.fill(Qt.transparent)

    painter = QPainter(out)
    try:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        radius = size * RADIUS_RATIO
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

        pad = size * PADDING_RATIO
        inner = int(size - 2 * pad)
        art = src.scaled(inner, inner, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawImage(
            int((size - art.width()) / 2), int((size - art.height()) / 2), art
        )
    finally:
        painter.end()
    return out


def main() -> int:
    if not os.path.exists(SRC):
        print(f"缺少源图 {SRC}", file=sys.stderr)
        return 1
    src = QImage(SRC)
    if src.isNull():
        print(f"读不出源图 {SRC}", file=sys.stderr)
        return 1
    print(f"源图 {src.width()}x{src.height()}（透明底会补白底）")

    master = compose(src, MASTER)
    os.makedirs(ICONSET, exist_ok=True)
    for px, name in SIZES:
        img = master.scaled(px, px, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img.save(os.path.join(ICONSET, name), "PNG")

    subprocess.run(["iconutil", "-c", "icns", ICONSET, "-o", "icon-rounded.icns"], check=True)
    print("已生成 icon-rounded.icns")

    if sys.platform == "darwin":
        # Windows 用的 .ico 在 macOS 上由 Qt 写出（单张 256）
        master.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(
            "icon-rounded.ico", "ICO"
        )
        print("已生成 icon-rounded.ico")
    return 0


if __name__ == "__main__":
    sys.exit(main())
