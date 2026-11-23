from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QTextEdit,
)
from PySide6.QtCore import Qt

from . import theme


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setMinimumWidth(440)
        self.setMinimumHeight(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(10)

        title = QLabel("提示词管理")
        title.setObjectName("brand")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel("版本 1.4.0")
        version.setObjectName("dim")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        desc = QTextEdit()
        desc.setReadOnly(True)
        desc.setStyleSheet(f"""
            QTextEdit {{
                background: {theme.INPUT_BG};
                border: 1px solid {theme.BORDER};
                border-radius: 12px;
                padding: 14px;
                color: {theme.TEXT_DIM};
                font-size: 13px;
            }}
        """)
        desc.setHtml(f"""
<h3 style="margin-top:0;color:{theme.TEXT};">功能概述</h3>
<p>一款桌面端提示词编辑管理工具，支持 AI 辅助整理与优化。</p>

<h3 style="color:{theme.TEXT};">使用方法</h3>
<ul>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">编辑区</b>：输入提示词内容，字数实时统计。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">整理格式</b>：调用 AI 修正错别字、标点、空格和换行。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">优化提示词</b>：调用 AI 增强提示词的清晰度与效果。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">深度思考</b>：勾选后 AI 先推理再输出，耗时较长。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">AI 结果区</b>：处理结果流式展示，可一键复制。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">保存</b>：将当前内容写入右侧历史记录。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">清除</b>：清空编辑区和结果区，开始新提示词。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">外观</b>：右上角按钮切换黑夜 / 白天，选择自动记住。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">收藏</b>：将当前提示词加入左侧「我的提示词」，自动生成标题和标签。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">历史记录</b>：右侧展示所有保存的提示词，点击加载到编辑区。<br>支持搜索、Delete 键删除、右键删除。</li>
<li style="color:{theme.TEXT_DIM};"><b style="color:{theme.CYAN};">我的提示词</b>：左侧展示收藏的提示词，标题在上、标签在下；标题旁的 <b style="color:{theme.CYAN};">+</b> 可直接把编辑区内容存进来。<br>双击加载到编辑区，右键可复制内容或取消收藏。<br>支持 Ctrl+C 复制、Delete 键删除。</li>
</ul>

<h3 style="color:{theme.TEXT};">环境要求</h3>
<ul>
<li style="color:{theme.TEXT_DIM};">DeepSeek API Key（在 文件 &gt; 设置 中配置）</li>
<li style="color:{theme.TEXT_DIM};">网络连接正常</li>
</ul>

<h3 style="color:{theme.TEXT};">关于作者</h3>
<p>
刘伟（紧张的卡米尔）<br>
1791723826@qq.com
</p>

<h3 style="color:{theme.TEXT};">许可</h3>
<p>仅供个人使用，请勿用于非法用途。</p>
""")
        layout.addWidget(desc)

        btn = QDialogButtonBox(QDialogButtonBox.Ok)
        btn.button(QDialogButtonBox.Ok).setText("知道了")
        theme.variant(btn.button(QDialogButtonBox.Ok), "primary")
        btn.accepted.connect(self.accept)
        layout.addWidget(btn)
