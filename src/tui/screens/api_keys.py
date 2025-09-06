"""API 키 관리 화면"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, Input
from textual.binding import Binding
import asyncio

from .base import BaseScreen
from ..utils.config_manager import ConfigManager
from ...config import Config


class ApiKeysScreen(BaseScreen):
    """API 키 관리 화면"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("ctrl+v", "validate", "Validate", priority=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager()
        self._validating = False
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Static("◆ API Keys", classes="screen-title")
        
        with Vertical(classes="transcribe-container"):
            # 현재 키 입력
            with Vertical():
                yield Static("OpenAI API Key", classes="options-title")
                yield Input(placeholder="sk-...", id="openai_key_input", classes="main-input")
                yield Static(self._masked_key_text(), id="openai_key_masked", classes="content-text")
            # 동작 버튼
            with Horizontal(classes="actions-bar"):
                yield Button("Save", id="save_key", classes="action-button")
                yield Button("Validate", id="validate_key", classes="utility-button")
                yield Button("Back", id="back_button", classes="warning-button")
            # 상태 표시
            yield Static("", id="status_line", classes="output-text")
    
    def on_mount(self) -> None:
        try:
            key_input = self.query_one("#openai_key_input", Input)
            current = Config.OPENAI_API_KEY or ""
            key_input.value = current
            key_input.focus()
            self._update_mask()
        except Exception:
            pass
    
    def _masked_key_text(self) -> str:
        try:
            key = Config.OPENAI_API_KEY or ""
            if not key:
                return "현재 설정된 키가 없습니다."
            if len(key) <= 8:
                return "현재 키: ********"
            return f"현재 키: {key[:4]}********{key[-4:]}"
        except Exception:
            return ""
    
    def _update_mask(self) -> None:
        try:
            self.query_one("#openai_key_masked", Static).update(self._masked_key_text())
        except Exception:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_button":
            self.app.pop_screen()
        elif event.button.id == "save_key":
            self.action_save()
        elif event.button.id == "validate_key":
            self.action_validate()
    
    def action_save(self) -> None:
        try:
            key_input = self.query_one("#openai_key_input", Input)
            value = key_input.value.strip()
            if not value:
                self.show_error("키 값을 입력하세요")
                return
            ok = self.cfg.save_api_key("OpenAI API Key", value)
            if ok:
                # Config 클래스의 값을 즉시 반영하기 위해 재로드
                try:
                    from dotenv import load_dotenv
                    load_dotenv(override=True)
                    Config.OPENAI_API_KEY = value  # 런타임 반영
                except Exception:
                    pass
                self._update_mask()
                self.show_success("저장되었습니다")
            else:
                self.show_error("저장에 실패했습니다")
        except Exception as e:
            self.show_error(str(e))
    
    def action_validate(self) -> None:
        if self._validating:
            return
        try:
            key_input = self.query_one("#openai_key_input", Input)
            value = key_input.value.strip()
            if not value:
                self.show_error("키 값을 입력하세요")
                return
            self._set_status("◆ 검증 중...")
            self._validating = True
            asyncio.create_task(self._validate_async(value))
        except Exception:
            self._validating = False
    
    async def _validate_async(self, key: str) -> None:
        try:
            ok = await self.cfg.validate_api_key_async(key, env_key="OPENAI_API_KEY")
            if ok:
                self._set_status("[OK] 키가 유효합니다")
                self.show_success("검증 완료")
                self._update_mask()
            else:
                self._set_status("[ERROR] 키가 유효하지 않습니다")
                self.show_error("검증 실패")
        except Exception as e:
            self._set_status(f"오류: {e}")
            self.show_error(str(e))
        finally:
            self._validating = False
    
    def _set_status(self, text: str) -> None:
        try:
            self.query_one("#status_line", Static).update(text)
        except Exception:
            pass