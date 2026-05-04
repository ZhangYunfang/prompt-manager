from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QTextEdit,
)
from PySide6.QtCore import Qt


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setMinimumWidth(440)
        self.setMinimumHeight(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("提示词管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #222;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel("版本 1.0.0")
        version.setStyleSheet("font-size: 11px; color: #888;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        desc = QTextEdit()
        desc.setReadOnly(True)
        desc.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 12px;
                color: #333;
                font-size: 13px;
            }
        """)
        desc.setHtml("""
<h3 style="margin-top:0;">功能概述</h3>
<p>一款桌面端提示词编辑管理工具，支持 AI 辅助整理与优化。</p>

<h3>使用方法</h3>
<ul>
<li><b>编辑区</b>：输入提示词内容，字数实时统计。</li>
<li><b>整理格式</b>：调用 AI 修正错别字、标点、空格和换行。</li>
<li><b>优化提示词</b>：调用 AI 增强提示词的清晰度与效果。</li>
<li><b>深度思考</b>：勾选后 AI 先推理再输出，耗时较长。</li>
<li><b>AI 结果区</b>：处理结果流式展示，可一键复制。</li>
<li><b>保存</b>：将当前内容写入左侧历史记录。</li>
<li><b>清除</b>：清空编辑区和结果区，开始新提示词。</li>
<li><b>收藏</b>：将当前提示词加入右侧收藏夹，自动生成标题和标签。</li>
<li><b>历史记录</b>：左侧展示所有保存的提示词，点击加载到编辑区。<br>支持搜索、Delete 键删除、右键删除。</li>
<li><b>收藏夹</b>：右侧展示收藏的提示词，标题在上、标签在下。<br>双击加载到编辑区，右键可复制内容或取消收藏。<br>支持 Ctrl+C 复制、Delete 键删除。</li>
</ul>

<h3>环境要求</h3>
<ul>
<li>DeepSeek API Key（在 文件 &gt; 设置 中配置）</li>
<li>网络连接正常</li>
</ul>

<h3>关于作者</h3>
<p>
刘伟（紧张的卡米尔）<br>
1791723826@qq.com
</p>

<h3>许可</h3>
<p>仅供个人使用，请勿用于非法用途。</p>
""")
        layout.addWidget(desc)

        btn = QDialogButtonBox(QDialogButtonBox.Ok)
        btn.accepted.connect(self.accept)
        layout.addWidget(btn)
