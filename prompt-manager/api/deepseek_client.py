from typing import Optional, Tuple
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

TIMEOUT = 30


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

    def format_cleanup(self, content: str) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, content)

    def optimize(self, content: str) -> Tuple[bool, str]:
        return self._call(OPTIMIZE_SYSTEM_PROMPT, content)

    def test_connection(self) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, "test")
