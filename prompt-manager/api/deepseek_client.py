import json
import re
from typing import Tuple
from urllib.parse import urlparse
import requests


FORMAT_SYSTEM_PROMPT = (
    "You are a text formatter. Fix the following prompt text: "
    "correct typos, add missing punctuation and brackets, "
    "remove extra spaces and line breaks. "
    "Output ONLY the corrected text, no explanations."
)

OPTIMIZE_SYSTEM_PROMPT = (
    "You are a prompt engineering expert. Improve the following prompt "
    "to make it clearer, more specific, and more effective. "
    "Output ONLY the improved prompt, no explanations."
)

TITLE_SYSTEM_PROMPT = (
    "Generate a very short title (2-8 Chinese characters) that summarizes "
    "the topic of this prompt text. Output ONLY the title, no explanations."
)

TAG_SUGGEST_SYSTEM_PROMPT = (
    "Analyze the following prompt text. Return a JSON object with two fields: "
    '"title" (a short 2-8 Chinese character summary) and '
    '"tags" (3-5 relevant single-word or two-word Chinese tags as an array). '
    'Output ONLY the JSON, no explanations. Example: {"title": "翻译助手", "tags": ["翻译", "英语", "商务"]}'
)

TIMEOUT = 30
FAST_TIMEOUT = 10

# 用户内容里出现链接时，声明 deepseek_read_url 让服务端抓取网页（只在最后一条用户消息里识别 URL）
URL_PATTERN = re.compile(r"https?://[^\s，。、）)]+")

WEB_SEARCH_TOOL = {"type": "deepseek_web_search", "name": "deepseek_web_search"}
READ_URL_TOOL = {"type": "deepseek_read_url", "name": "deepseek_read_url"}

# 模型调用服务端工具时的 kind（search/image_search 是联网搜索，deep_ 开头是深度思考搜索）
_SEARCH_KINDS = ("search", "image_search", "deep_search", "deep_image_search")


def site_of(url: str) -> str:
    """从 url 取站点名：去掉协议、路径与开头的 www.。"""
    host = urlparse(url).netloc or url
    return host[4:] if host.startswith("www.") else host


class StreamResult:
    def __init__(self):
        self.text = ""
        self.sources = []        # [{"title", "url", "site"}]，按出现顺序去重
        self.search_count = 0
        self.done = False
        self.error = ""
        import threading
        self._lock = threading.Lock()

    def update(self, text: str):
        with self._lock:
            self.text = text

    def add_annotations(self, annotations):
        """收集引用（url_citation），同一 url 只留一条。"""
        with self._lock:
            seen = {s["url"] for s in self.sources}
            for item in annotations or []:
                loc = (item or {}).get("url_citation") or {}
                url = (loc.get("url") or "").strip()
                if not url or url in seen:
                    continue
                seen.add(url)
                self.sources.append(
                    {"title": (loc.get("title") or "").strip() or url, "url": url, "site": site_of(url)}
                )

    def count_tool_calls(self, calls):
        """累加联网工具调用次数（含图片搜索与深度思考搜索）。"""
        with self._lock:
            for step in calls or []:
                for call in (step or {}).get("calls") or []:
                    if (call or {}).get("kind") in _SEARCH_KINDS:
                        self.search_count += 1

    def finish(self, error: str = ""):
        with self._lock:
            self.done = True
            self.error = error

    def get(self):
        with self._lock:
            return self.text, self.done, self.error

    def snapshot(self):
        with self._lock:
            return self.text, self.done, self.error, list(self.sources), self.search_count


def _parse_sse_delta(line: str):
    """解析一行 SSE，返回 choices[0].delta；不是数据行/解析失败/[DONE] 返回 None。"""
    if not line.startswith("data:"):
        return None
    data_str = line[5:].strip()
    if not data_str or data_str == "[DONE]":
        return None
    try:
        data = json.loads(data_str)
        choices = data.get("choices") or []
        if not choices:
            return None
        return choices[0].get("delta") or {}
    except (json.JSONDecodeError, AttributeError):
        return None


def _parse_sse_line(line: str):
    delta = _parse_sse_delta(line)
    return "" if delta is None else (delta.get("content") or "")


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-v4-flash"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def _call(self, system_prompt: str, user_content: str) -> Tuple[bool, str]:
        if not self._api_key:
            return False, "请先在设置中配置 API Key"
        try:
            resp = requests.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.3,
                    "thinking": {"type": "disabled"},
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            result = data["choices"][0]["message"]["content"]
            return True, result
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络后重试"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 API 服务器，请检查网络和 API 地址"
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                return False, "API Key 无效，请在设置中更新"
            return False, f"API 错误 ({resp.status_code}): {e}"
        except Exception as e:
            return False, f"未知错误: {e}"

    def stream_call(self, system_prompt: str, user_content: str, result: StreamResult,
                    thinking: bool = False, search: bool = False):
        if not self._api_key:
            result.finish("请先在设置中配置 API Key")
            return
        # 声明服务端工具：勾了「联网搜索」就带 web_search；内容里有链接就带上阅读链接。
        # 不声明时请求与原来完全一致（声明联网工具后服务端会忽略 temperature）。
        tools = []
        if search:
            tools.append(dict(WEB_SEARCH_TOOL))
        if search or URL_PATTERN.search(user_content or ""):
            tools.append(dict(READ_URL_TOOL))
        body = {
            "model": self._model,
            "thinking": {"type": "enabled"} if thinking else {"type": "disabled"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            "stream": True,
        }
        if tools:
            body["tools"] = tools
        try:
            resp = requests.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=TIMEOUT,
                stream=True,
            )
            resp.raise_for_status()
            # 服务端常发 `Content-Type: text/event-stream`（无 charset），requests 会按
            # ISO-8859-1 解码 → 中文变乱码、JSON 片段解不出被静默丢弃；强制 UTF-8。
            resp.encoding = "utf-8"
            full = ""
            # 按行读，不要 1 字节一读：DeepSeek 一条回复能产生几千个 SSE 事件，
            # 逐字节累加字符串是 O(n²)，长回复会拖慢到界面来不及刷新。
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                delta = _parse_sse_delta(line)
                if not delta:
                    continue
                chunk = delta.get("content") or ""
                if chunk:
                    full += chunk
                    result.update(full)
                if delta.get("annotations"):
                    result.add_annotations(delta["annotations"])
                if delta.get("server_tool_calls"):
                    result.count_tool_calls(delta["server_tool_calls"])
            result.update(full)
            if not full:
                result.finish("API 返回空结果")
            else:
                result.finish()
        except requests.exceptions.Timeout:
            result.finish("请求超时，请检查网络后重试")
        except requests.exceptions.ConnectionError:
            result.finish("无法连接到 API 服务器，请检查网络和 API 地址")
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                result.finish("API Key 无效，请在设置中更新")
            else:
                result.finish(f"API 错误 ({resp.status_code}): {e}")
        except Exception as e:
            result.finish(f"未知错误: {e}")

    def format_cleanup(self, content: str) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, content)

    def optimize(self, content: str) -> Tuple[bool, str]:
        return self._call(OPTIMIZE_SYSTEM_PROMPT, content)

    def test_connection(self) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, "test")

    def generate_title(self, content: str) -> Tuple[bool, str]:
        return self._call_fast(TITLE_SYSTEM_PROMPT, content[:500])

    def suggest_tags_and_title(self, content: str) -> Tuple[bool, dict]:
        ok, result = self._call_fast(TAG_SUGGEST_SYSTEM_PROMPT, content[:500])
        if not ok or not result:
            return False, {}
        try:
            data = json.loads(result.strip())
            return True, data
        except json.JSONDecodeError:
            return False, {}

    def _call_fast(self, system_prompt: str, user_content: str) -> Tuple[bool, str]:
        if not self._api_key:
            return False, "请先在设置中配置 API Key"
        try:
            resp = requests.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.0,
                    "thinking": {"type": "disabled"},
                },
                timeout=FAST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            return True, data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            return False, ""
        except Exception:
            return False, ""
