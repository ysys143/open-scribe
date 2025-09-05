"""설정 화면"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Button
from textual.binding import Binding

from .base import BaseScreen


class SettingsScreen(BaseScreen):
    """설정 화면"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
    ]
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Static("Settings Screen", classes="screen-title")
        
        with Vertical(classes="transcribe-container"):
            yield Static("Settings features will be implemented in Phase 4.")
            yield Button("Back", id="back_button", classes="action-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 이벤트"""
        if event.button.id == "back_button":
            self.app.pop_screen()