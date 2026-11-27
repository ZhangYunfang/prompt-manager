import json
import os
from pathlib import Path

# 版本号唯一来源：关于页与 build.spec 的 Info.plist 都读这里，避免两处写法漂移
APP_VERSION = "1.6.8"


class Config:
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-v4-flash"
    DEFAULT_APPEARANCE = "dark"
    DEFAULT_ACCENT = "cyan"
    DEFAULT_FONT_SCALE = 1.0
    MIN_FONT_SCALE = 0.8
    MAX_FONT_SCALE = 1.4

    def __init__(self):
        self._config_dir = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "prompt-manager"
        self._config_file = self._config_dir / "settings.json"
        self._ensure_config_dir()
        self._data = self._load() if self._config_file.exists() else {}
        self._set_defaults()

    def _ensure_config_dir(self):
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _set_defaults(self):
        self._data.setdefault("api_key", "")
        self._data.setdefault("base_url", self.DEFAULT_BASE_URL)
        self._data.setdefault("model", self.DEFAULT_MODEL)
        self._data.setdefault("appearance", self.DEFAULT_APPEARANCE)
        self._data.setdefault("accent", self.DEFAULT_ACCENT)
        self._data.setdefault("font_scale", self.DEFAULT_FONT_SCALE)

    def _load(self) -> dict:
        with open(self._config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        self._ensure_config_dir()
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(self._config_file, 0o600)   # 含 API Key，只给本人读写
        except OSError:
            pass

    @property
    def api_key(self) -> str:
        return self._data.get("api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._data["api_key"] = value

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", self.DEFAULT_BASE_URL)

    @base_url.setter
    def base_url(self, value: str):
        self._data["base_url"] = value

    @property
    def model(self) -> str:
        return self._data.get("model", self.DEFAULT_MODEL)

    @model.setter
    def model(self, value: str):
        self._data["model"] = value

    @property
    def appearance(self) -> str:
        return self._data.get("appearance", self.DEFAULT_APPEARANCE)

    @appearance.setter
    def appearance(self, value: str):
        self._data["appearance"] = "light" if value == "light" else "dark"

    @property
    def accent(self) -> str:
        return self._data.get("accent", self.DEFAULT_ACCENT)

    @accent.setter
    def accent(self, value: str):
        self._data["accent"] = value

    @property
    def font_scale(self) -> float:
        try:
            return float(self._data.get("font_scale", self.DEFAULT_FONT_SCALE))
        except (TypeError, ValueError):
            return self.DEFAULT_FONT_SCALE

    @font_scale.setter
    def font_scale(self, value: float):
        self._data["font_scale"] = round(
            max(self.MIN_FONT_SCALE, min(self.MAX_FONT_SCALE, float(value))), 2)

    @property
    def data_dir(self) -> Path:
        return self._config_dir
