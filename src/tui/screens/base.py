"""기본 화면 클래스"""

from textual.screen import Screen
from textual import events
from typing import Any


class BaseScreen(Screen):
    """모든 화면의 기본 클래스"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_key(self, event: events.Key) -> None:
        """공통 키 이벤트 처리"""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "f5":
            self.refresh_data()
    
    def refresh_data(self) -> None:
        """데이터 새로고침 (하위 클래스에서 구현)"""
        pass
    
    def show_error(self, message: str) -> None:
        """에러 메시지 표시"""
        self.notify(f"❌ {message}", severity="error")
    
    def show_success(self, message: str) -> None:
        """성공 메시지 표시"""
        self.notify(f"✅ {message}", severity="information")