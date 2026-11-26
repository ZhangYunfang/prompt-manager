# 提示词管理（PromptManager）

桌面端提示词编辑器：左边写提示词，右边让 AI 帮你**整理**（修错别字、补标点）或**优化**（改得更清晰具体），
收藏自己的常用提示词、按标签和关键词找回来，历史自动留档。支持 Windows / macOS / Linux。

## 下载与启动

到 [Releases](https://github.com/ZhangYunfang/prompt-manager/releases/latest) 下对应平台的包：

| 平台 | 产物 | 怎么启动 |
|---|---|---|
| Windows x64 | `PromptManager-<版本>-windows-x64.zip` | 解压后进 `PromptManager` 文件夹，双击 `PromptManager.exe`。**整个文件夹要一起留着**，只把 exe 拷走会起不来 |
| macOS arm64 | `PromptManager-<版本>-macos-arm64.zip` | 解压得到 `PromptManager.app`，拖进「应用程序」；首次打开若被拦，右键 →「打开」 |
| Linux x64 | `PromptManager-<版本>-linux-x64.tar.gz` | `tar -xzf` 解压，运行里面的 `PromptManager` |

macOS 是 Apple 芯片（arm64）版本；Intel 机型暂未提供。

## 首次使用：配置 AI

打开「设置」，填 API Key（默认走 DeepSeek：`https://api.deepseek.com` / `deepseek-v4-flash`），
点「测试连接」通过即可。也支持任何 OpenAI 兼容的 `/chat/completions` 端点，把服务地址和模型名换成自己的。

## 主要功能

- **整理 / 优化**：AI 结果在右侧实时流式显示，完成后按 Markdown 渲染并可一键复制（提示词统一要求 Markdown 输出并用四个反引号包裹，防止长文本截断）
- **联网搜索**：「深度思考」旁边的「联网搜索」勾上后，AI 先联网搜索再作答；结果框按 Markdown 渲染，末尾自动附「参考来源」（标题 + 链接，复制时一并带走），也可点右上角「参考来源 N」在独立窗口里逐条打开原文
- **阅读链接**：编辑区里贴了网址（`https://…`）时会自动让 AI 读取网页再回答，不需要额外开关
- **优化时是否思考**：勾选「思考」会用支持思考的模型先推理再给结果，响应更慢但通常更准
- **我的提示词**：收藏、标题与标签管理（右键可「修改标题和标签」「复制内容」「移除」）、搜索、单击加载到编辑区
- **历史记录**：每次编辑自动留档，可一键清空
- **外观**：黑夜 / 白天两套主题、12 种主体风格色、整体字号 80%~140% 调节

## 数据放在哪

都在用户目录下的 `prompt-manager/`：

- `settings.json`：API Key、服务地址、主题与字号（权限 600，只给自己读写）
- `prompts_history.json`：历史记录
- `prompts_bookmarks.json`：我的提示词

换机器时把这三个文件拷过去即可。

## 常见问题

- **Windows 双击没反应/报缺 DLL**：确认是整个 `PromptManager` 文件夹解压出来的，而不是单独把 exe 拖出来；杀软把它拦进了隔离区的话，先加白名单再解压一次
- **换图标后还显示旧图标**：系统图标缓存，删掉旧文件夹重新解压，或重启资源管理器 / `killall Dock`（macOS）
- **勾了联网搜索但没搜**：搜不搜由模型判断（提示词类需求常常不需要联网），要它查最新事实就把问题写成"查一下…并给出处"
- **AI 报「API Key 无效」**：设置里重新填，注意别带多余空格
- **AI 结果为空或超时**：换网络重试；自建端点请确认支持流式（`stream: true`）的 `text/event-stream`

## 开发与打包

```bash
cd prompt-manager
python -m pip install -r requirements.txt
python main.py                                  # 直接运行
./.venv/bin/python make_icons.py                # 从 icon-source.png 重新生成 .icns/.ico
python -m PyInstaller --noconfirm build.spec     # 本机构建
```

打标签（`v*`）会自动触发 GitHub Actions 构建三平台产物并挂到对应 Release。
界面记录见 [`docs/CHANGELOG.md`](docs/CHANGELOG.md)。
