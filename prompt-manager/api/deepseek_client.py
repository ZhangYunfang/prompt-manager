import json
from typing import Tuple, Callable
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
FAST_TEMPERATURE = 0.0
FAST_TIMEOUT = 10


def _parse_sse_line(line: str) -> str:
    if line.startswith("data: "):
        data_str = line[6:]
        if data_str.strip() == "[DONE]":
            return None
        try:
            data = json.loads(data_str)
            delta = data["choices"][0].get("delta", {})
            return delta.get("content", "")
        except (json.JSONDecodeError, KeyError, IndexError):
            return ""
    return ""


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

    def _call_stream(self, system_prompt: str, user_content: str, on_chunk: Callable[[str], None]) -> Tuple[bool, str]:
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
                    "stream": True,
                },
                timeout=TIMEOUT,
                stream=True,
            )
            resp.raise_for_status()
            full = ""
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    chunk = _parse_sse_line(line)
                    if chunk is None:
                        break
                    if chunk:
                        full += chunk
                        on_chunk(full)
            return True, full
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

    def format_cleanup(self, content: str) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, content)

    def format_cleanup_stream(self, content: str, on_chunk: Callable[[str], None]) -> Tuple[bool, str]:
        return self._call_stream(FORMAT_SYSTEM_PROMPT, content, on_chunk)

    def optimize(self, content: str) -> Tuple[bool, str]:
        return self._call(OPTIMIZE_SYSTEM_PROMPT, content)

    def optimize_stream(self, content: str, on_chunk: Callable[[str], None]) -> Tuple[bool, str]:
        return self._call_stream(OPTIMIZE_SYSTEM_PROMPT, content, on_chunk)

    def test_connection(self) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, "test")

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
                },
                timeout=FAST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            result = data["choices"][0]["message"]["content"]
            return True, result
        except requests.exceptions.Timeout:
            return False, ""
        except Exception:
            return False, ""

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
