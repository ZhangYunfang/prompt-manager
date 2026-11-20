"""从 icon-source.png 生成 macOS(.icns) 与 Windows(.ico) 图标。

源图建议 ≥512×512；小于该尺寸会被平滑放大，细节会软。
用法：./.venv/bin/python make_icons.py
"""

import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

SRC = "icon-source.png"
ICONSET = "build/icon.iconset"

# macOS .iconset 要求的具体尺寸（像素, 文件名）
SIZES = [
    (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
]


def main() -> int:
    if not os.path.exists(SRC):
        print(f"缺少源图 {SRC}", file=sys.stderr)
        return 1
    src = QImage(SRC)
    if src.isNull():
        print(f"读不出源图 {SRC}", file=sys.stderr)
        return 1
    print(f"源图 {src.width()}x{src.height()}")

    os.makedirs(ICONSET, exist_ok=True)
    for px, name in SIZES:
        img = src.scaled(px, px, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img.save(os.path.join(ICONSET, name), "PNG")

    subprocess.run(["iconutil", "-c", "icns", ICONSET, "-o", "icon-rounded.icns"], check=True)
    print("已生成 icon-rounded.icns")

    if sys.platform == "darwin":
        # Windows 用的 .ico 在 macOS 上由 Qt 写出（单张 256）
        src.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(
            "icon-rounded.ico", "ICO"
        )
        print("已生成 icon-rounded.ico")
    return 0


if __name__ == "__main__":
    sys.exit(main())
