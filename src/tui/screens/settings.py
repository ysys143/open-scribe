"""설정 화면"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button, Input
from textual.binding import Binding

from .base import BaseScreen
from ..utils.config_manager import ConfigManager
from ...config import Config


class SettingsScreen(BaseScreen):
    """설정 화면"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("ctrl+s", "save", "Save", priority=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager()
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Static("⚈ Settings", classes="screen-title")
        
        with ScrollableContainer(classes="settings-container"):
            # Worker 설정
            with Vertical(classes="setting-group"):
                yield Static("Workers", classes="options-title")
                with Horizontal():
                    yield Input(placeholder="MIN_WORKER", id="min_worker", classes="main-input")
                    yield Input(placeholder="MAX_WORKER", id="max_worker", classes="main-input")
            # 경로 설정 (BASE_PATH만 직접 설정, 나머지는 config.py에서 조합)
            with Vertical(classes="setting-group"):
                yield Static("Paths", classes="options-title")
                yield Input(placeholder="OPEN_SCRIBE_BASE_PATH", id="base_path", classes="main-input")
                yield Input(placeholder="OPEN_SCRIBE_DOWNLOADS_PATH", id="downloads_path", classes="main-input")
            # 엔진/언어/모델
            with Vertical(classes="setting-group"):
                yield Static("Engine & Language", classes="options-title")
                yield Input(placeholder="OPEN_SCRIBE_ENGINE", id="engine", classes="main-input")
                yield Input(placeholder="OPENAI_SUMMARY_MODEL", id="summary_model", classes="main-input")
                yield Input(placeholder="OPENAI_SUMMARY_LANGUAGE", id="summary_language", classes="main-input")
                yield Input(placeholder="OPENAI_TRANSLATE_MODEL", id="translate_model", classes="main-input")
                yield Input(placeholder="OPENAI_TRANSLATE_LANGUAGE", id="translate_language", classes="main-input")
            # 기능 토글 (true/false)
            with Vertical(classes="setting-group"):
                yield Static("Feature Flags (true/false)", classes="options-title")
                with Horizontal():
                    yield Input(placeholder="OPEN_SCRIBE_STREAM", id="stream", classes="main-input")
                    yield Input(placeholder="OPEN_SCRIBE_DOWNLOADS", id="copy_downloads", classes="main-input")
                with Horizontal():
                    yield Input(placeholder="OPEN_SCRIBE_SUMMARY", id="enable_summary", classes="main-input")
                    yield Input(placeholder="OPEN_SCRIBE_VERBOSE", id="verbose", classes="main-input")
                with Horizontal():
                    yield Input(placeholder="OPEN_SCRIBE_AUDIO", id="keep_audio", classes="main-input")
                    yield Input(placeholder="OPEN_SCRIBE_VIDEO", id="download_video", classes="main-input")
                with Horizontal():
                    yield Input(placeholder="OPEN_SCRIBE_SRT", id="generate_srt", classes="main-input")
                    yield Input(placeholder="OPEN_SCRIBE_TRANSLATE", id="enable_translate", classes="main-input")
                with Horizontal():
                    yield Input(placeholder="OPEN_SCRIBE_TIMESTAMP", id="include_timestamp", classes="main-input")
            # 버튼
            with Horizontal(classes="actions-bar"):
                yield Button("Save", id="save_btn", classes="action-button")
                yield Button("Back", id="back_button", classes="warning-button")
            yield Static("", id="status_line", classes="output-text")
    
    def on_mount(self) -> None:
        try:
            self.query_one("#min_worker", Input).value = str(Config.MIN_WORKER)
            self.query_one("#max_worker", Input).value = str(Config.MAX_WORKER)
            # Paths
            self.query_one("#base_path", Input).value = str(Config.BASE_PATH)
            self.query_one("#downloads_path", Input).value = str(Config.DOWNLOADS_PATH)
            # Engine & Language
            self.query_one("#engine", Input).value = str(Config.ENGINE)
            self.query_one("#summary_model", Input).value = str(Config.OPENAI_SUMMARY_MODEL)
            self.query_one("#summary_language", Input).value = str(Config.OPENAI_SUMMARY_LANGUAGE)
            self.query_one("#translate_model", Input).value = str(Config.OPENAI_TRANSLATE_MODEL)
            self.query_one("#translate_language", Input).value = str(Config.OPENAI_TRANSLATE_LANGUAGE)
            # Flags
            self.query_one("#stream", Input).value = str(Config.ENABLE_STREAM).lower()
            self.query_one("#copy_downloads", Input).value = str(Config.COPY_TO_DOWNLOADS).lower()
            self.query_one("#enable_summary", Input).value = str(Config.ENABLE_SUMMARY).lower()
            self.query_one("#verbose", Input).value = str(Config.VERBOSE).lower()
            self.query_one("#keep_audio", Input).value = str(Config.KEEP_AUDIO).lower()
            self.query_one("#download_video", Input).value = str(Config.DOWNLOAD_VIDEO).lower()
            self.query_one("#generate_srt", Input).value = str(Config.GENERATE_SRT).lower()
            self.query_one("#enable_translate", Input).value = str(Config.ENABLE_TRANSLATE).lower()
            self.query_one("#include_timestamp", Input).value = str(Config.INCLUDE_TIMESTAMP).lower()
        except Exception:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_button":
            self.app.pop_screen()
        elif event.button.id == "save_btn":
            self.action_save()
    
    def _set_status(self, msg: str) -> None:
        try:
            self.query_one("#status_line", Static).update(msg)
        except Exception:
            pass
    
    def action_save(self) -> None:
        try:
            min_w = int(self.query_one("#min_worker", Input).value or "1")
            max_w = int(self.query_one("#max_worker", Input).value or "5")
            if min_w < 1 or max_w < 1 or min_w > max_w:
                self.show_error("MIN/MAX 값이 올바르지 않습니다")
                return
            # .env 업데이트 (workers)
            self.cfg.update_env_file("MIN_WORKER", str(min_w))
            self.cfg.update_env_file("MAX_WORKER", str(max_w))
            # 경로
            self.cfg.update_env_file("OPEN_SCRIBE_BASE_PATH", self.query_one("#base_path", Input).value)
            self.cfg.update_env_file("OPEN_SCRIBE_DOWNLOADS_PATH", self.query_one("#downloads_path", Input).value)
            # 엔진/언어/모델
            self.cfg.update_env_file("OPEN_SCRIBE_ENGINE", self.query_one("#engine", Input).value)
            self.cfg.update_env_file("OPENAI_SUMMARY_MODEL", self.query_one("#summary_model", Input).value)
            self.cfg.update_env_file("OPENAI_SUMMARY_LANGUAGE", self.query_one("#summary_language", Input).value)
            self.cfg.update_env_file("OPENAI_TRANSLATE_MODEL", self.query_one("#translate_model", Input).value)
            self.cfg.update_env_file("OPENAI_TRANSLATE_LANGUAGE", self.query_one("#translate_language", Input).value)
            # 플래그 값
            self.cfg.update_env_file("OPEN_SCRIBE_STREAM", self.query_one("#stream", Input).value or "true")
            self.cfg.update_env_file("OPEN_SCRIBE_DOWNLOADS", self.query_one("#copy_downloads", Input).value or "true")
            self.cfg.update_env_file("OPEN_SCRIBE_SUMMARY", self.query_one("#enable_summary", Input).value or "true")
            self.cfg.update_env_file("OPEN_SCRIBE_VERBOSE", self.query_one("#verbose", Input).value or "true")
            self.cfg.update_env_file("OPEN_SCRIBE_AUDIO", self.query_one("#keep_audio", Input).value or "false")
            self.cfg.update_env_file("OPEN_SCRIBE_VIDEO", self.query_one("#download_video", Input).value or "false")
            self.cfg.update_env_file("OPEN_SCRIBE_SRT", self.query_one("#generate_srt", Input).value or "false")
            self.cfg.update_env_file("OPEN_SCRIBE_TRANSLATE", self.query_one("#enable_translate", Input).value or "false")
            self.cfg.update_env_file("OPEN_SCRIBE_TIMESTAMP", self.query_one("#include_timestamp", Input).value or "false")
            # 런타임 반영
            try:
                from dotenv import load_dotenv
                load_dotenv(override=True)
            except Exception:
                pass
            Config.MIN_WORKER = min_w
            Config.MAX_WORKER = max_w
            Config.BASE_PATH = Config.BASE_PATH.__class__(self.query_one("#base_path", Input).value)
            Config.DOWNLOADS_PATH = Config.DOWNLOADS_PATH.__class__(self.query_one("#downloads_path", Input).value)
            Config.ENGINE = self.query_one("#engine", Input).value
            Config.OPENAI_SUMMARY_MODEL = self.query_one("#summary_model", Input).value
            Config.OPENAI_SUMMARY_LANGUAGE = self.query_one("#summary_language", Input).value
            Config.OPENAI_TRANSLATE_MODEL = self.query_one("#translate_model", Input).value
            Config.OPENAI_TRANSLATE_LANGUAGE = self.query_one("#translate_language", Input).value
            # booleans
            def _to_bool(v: str) -> bool:
                return str(v).strip().lower() == "true"
            Config.ENABLE_STREAM = _to_bool(self.query_one("#stream", Input).value)
            Config.COPY_TO_DOWNLOADS = _to_bool(self.query_one("#copy_downloads", Input).value)
            Config.ENABLE_SUMMARY = _to_bool(self.query_one("#enable_summary", Input).value)
            Config.VERBOSE = _to_bool(self.query_one("#verbose", Input).value)
            Config.KEEP_AUDIO = _to_bool(self.query_one("#keep_audio", Input).value)
            Config.DOWNLOAD_VIDEO = _to_bool(self.query_one("#download_video", Input).value)
            Config.GENERATE_SRT = _to_bool(self.query_one("#generate_srt", Input).value)
            Config.ENABLE_TRANSLATE = _to_bool(self.query_one("#enable_translate", Input).value)
            Config.INCLUDE_TIMESTAMP = _to_bool(self.query_one("#include_timestamp", Input).value)
            try:
                Config.create_directories()
            except Exception:
                pass
            self._set_status("[OK] 저장되었습니다")
            self.show_success("설정 저장 완료")
        except Exception as e:
            self.show_error(str(e))