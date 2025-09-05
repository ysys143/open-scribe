"""메인 메뉴 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, Label
from textual.events import Key, Click
from rich.text import Text
from textual.widget import Widget
from textual.app import ComposeResult
from textual.binding import Binding
import subprocess
import os
import sys
import threading


class URLInput(Input):
    """URL 입력을 위한 커스텀 Input 위젯"""
    
    def __init__(self, parent_screen, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_screen = parent_screen
        print(f"DEBUG: URLInput created with parent_screen: {parent_screen}")
    
    def on_key(self, event) -> None:
        """키 이벤트 처리"""
        print(f"DEBUG: URLInput.on_key called, key: {event.key}")
        if event.key == "enter":
            print(f"DEBUG: Enter key pressed in URLInput, value: {self.value}")
            if hasattr(self.parent_screen, 'start_transcription'):
                self.parent_screen.start_transcription()
        else:
            super().on_key(event)
    
    def action_submit(self) -> None:
        """엔터키를 눌렀을 때 호출"""
        print(f"DEBUG: URLInput.action_submit called, value: {self.value}")
        if hasattr(self.parent_screen, 'start_transcription'):
            self.parent_screen.start_transcription()


class MainMenuScreen(Widget):
    """메인 메뉴 화면"""
    
    # 키 이벤트를 직접 받기 위해 포커스 가능하도록 설정
    can_focus = True
    
    BINDINGS = [
        Binding("1", "menu_action('transcribe')", "Transcription", priority=True),
        Binding("2", "menu_action('database')", "Database", priority=True),
        Binding("3", "menu_action('api_keys')", "API Keys", priority=True),
        Binding("4", "menu_action('settings')", "Settings", priority=True),
        Binding("5", "menu_action('monitor')", "Monitoring", priority=True),
        Binding("h", "menu_action('help')", "Help", priority=True),
        Binding("q", "menu_action('quit')", "Quit", priority=True),
        Binding("ㅂ", "menu_action('quit')", "Quit", priority=True),
        Binding("escape", "menu_action('quit')", "Quit", priority=True),
        Binding("up", "handle_up", "Up", priority=True),
        Binding("down", "handle_down", "Down", priority=True),
        Binding("left", "focus_menu", "Menu", priority=True),
        Binding("right", "focus_content", "Content", priority=True),
        Binding("j", "handle_down", "Down (vim)", priority=True),
        Binding("k", "handle_up", "Up (vim)", priority=True),
        Binding("enter", "handle_enter", "Select/Toggle", priority=True),
        Binding("space", "handle_space", "Toggle", priority=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_buttons = []
        self.current_focus = 0
        self.content_area = None
        self.selected_button_id = None
        self.focus_area = "menu"  # "menu" or "content"
        # Store URL input widget
        self.url_input = None
        # Store option states (simple boolean values)
        self.timestamp_enabled = False
        self.summary_enabled = False
        self.translate_enabled = False
        self.video_enabled = False
        self.srt_enabled = False
        self.srt_translate_enabled = False
        self.selected_engine = "gpt-4o-mini-transcribe"  # default
        # Store option widgets for updating display
        self.option_widgets = {}
        # Current focused option index (for arrow key navigation)
        self.focused_option = 0
        self.total_options = 11  # 6 checkboxes + 5 engines
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical():
            # 상단 제목
            with Vertical(classes="header-section"):
                yield Static("Open-Scribe Youtube Transcriber", classes="title")
                yield Static("(c) Jaesol Shin 2025", classes="subtitle")
            
            # 구분선 (1줄로 통합)
            yield Static("═" * 120, classes="divider-line")
            
            # 하단 메뉴와 콘텐츠 영역
            with Horizontal(classes="main-section"):
                # 왼쪽 메뉴
                with Vertical(classes="menu-section"):
                    with Vertical(classes="menu-buttons"):
                        yield Button("1. Transcribe", id="transcribe", classes="menu-button")
                        yield Button("2. Database", id="database", classes="menu-button")
                        yield Button("3. API Keys", id="api_keys", classes="menu-button")
                        yield Button("4. Settings", id="settings", classes="menu-button")
                        yield Button("5. Monitoring", id="monitor", classes="menu-button")
                        yield Button("H. Help", id="help", classes="menu-button")
                        yield Button("Q. Quit", id="quit", classes="menu-button")
                
                # 오른쪽 콘텐츠 영역
                with Vertical(classes="content-area", id="content_area"):
                    yield Static("Select a menu item to view details", classes="content-placeholder")
    
    def on_mount(self) -> None:
        """화면 마운트 시 버튼 리스트 설정 및 첫 번째 버튼에 포커스"""
        # 버튼 순서대로 저장
        button_ids = ["transcribe", "database", "api_keys", "settings", "monitor", "help", "quit"]
        self.menu_buttons = [self.query_one(f"#{btn_id}", Button) for btn_id in button_ids]
        
        # 콘텐츠 영역 저장
        self.content_area = self.query_one("#content_area", Vertical)
        
        # 첫 번째 버튼에 포커스
        self.current_focus = 0
        self.menu_buttons[self.current_focus].focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 이벤트 처리"""
        button_id = event.button.id
        
        if button_id == "transcribe":
            # 오른쪽 콘텐츠 영역에 전사 인터페이스 표시
            self.selected_button_id = "transcribe"
            self.show_transcribe_interface()
            self.focus_area = "content"
            # 키 이벤트를 이 위젯이 직접 받도록 포커스 이동
            try:
                self.app.set_focus(self)
            except Exception:
                pass
            self.set_timer(0.01, lambda btn_id="transcribe": self._update_button_selection(btn_id))
        elif button_id == "start_transcribe":
            self.start_transcription()
        elif button_id == "clear_url":
            self.clear_url_input()
            return
        elif button_id == "stop_transcribe":
            # 현재는 백그라운드 스레드/프로세스 중지 미구현 - 안내만 표시
            self.app.notify("Stop is not implemented yet", severity="warning")
            return
        elif button_id == "database":
            self.show_content("Database Management", "Database management features will be implemented in Phase 4.")
            self.set_timer(0.01, lambda btn_id="database": self._update_button_selection(btn_id))
        elif button_id == "api_keys":
            self.show_content("API Keys Management", "API keys management features will be implemented in Phase 4.")
            self.set_timer(0.01, lambda btn_id="api_keys": self._update_button_selection(btn_id))
        elif button_id == "settings":
            self.show_content("Settings", "Settings features will be implemented in Phase 4.")
            self.set_timer(0.01, lambda btn_id="settings": self._update_button_selection(btn_id))
        elif button_id == "monitor":
            self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
            self.set_timer(0.01, lambda btn_id="monitor": self._update_button_selection(btn_id))
        elif button_id == "help":
            self.show_help()
        elif button_id == "quit":
            self.app.exit()
    
    def show_help(self) -> None:
        """도움말 표시"""
        self._update_button_selection("help")
        help_text = """YouTube Transcriber TUI Help

Menu Navigation:
- ↑/↓ or K/J: Move menu
- Enter: Select
- 1-5: Direct selection by number
- H: Help, Q: Quit

General Keyboard Shortcuts:
- Ctrl+C: Exit
- F1: Help
- F2: Toggle theme
- Esc/ㅂ: Quit"""
        self.show_content("Help", help_text)
    
    def _update_button_selection(self, selected_id: str) -> None:
        """버튼 선택 상태 업데이트 ((*) 표시 제거)"""
        self.selected_button_id = selected_id
        # (*) 표시 기능 제거 - 선택 상태만 내부적으로 추적
    
    def show_error(self, message: str) -> None:
        """에러 메시지 표시"""
        self.app.notify(f"❌ {message}", severity="error")
    
    def show_success(self, message: str) -> None:
        """성공 메시지 표시"""
        self.app.notify(f"✅ {message}", severity="information")
    
    def show_content(self, title: str, content: str) -> None:
        """콘텐츠 영역에 내용 표시"""
        if self.content_area:
            self.content_area.remove_children()
            self.content_area.mount(Static(title, classes="content-title"))
            self.content_area.mount(Static(content, classes="content-text"))
    
    def show_transcribe_interface(self) -> None:
        """콘텐츠 영역에 전사 인터페이스 표시"""
        if self.content_area:
            # 모든 자식 위젯 제거
            self.content_area.remove_children()
            
            # 제목과 구분선 제거 (단순화)
            
            # 폼 스택 컨테이너 - 모든 요소를 상단부터 세로로 붙임
            form = Vertical(classes="form-stack")
            self.content_area.mount(form)
            
            # URL 입력 섹션
            form.mount(Static("YouTube URL:", classes="options-title"))
            
            # 입력창 컨테이너
            input_container = Horizontal(classes="input-container")
            form.mount(input_container)
            
            # URL 입력창
            self.url_input = Input(
                placeholder="Paste YouTube URL here...",
                classes="url-input",
                id="url_input"
            )
            input_container.mount(self.url_input)
            
            # 액션 바: Output 위로 이동 (Start/Stop/Clear)
            actions = Horizontal(classes="actions-bar")
            form.mount(actions)
            # 상단 강조 제거: 버튼만 3분할로 배치
            actions.mount(Button("Run", id="start_transcribe", variant="primary", classes="action-button"))
            actions.mount(Button("Stop", id="stop_transcribe", variant="warning", classes="warning-button"))
            actions.mount(Button("Clr", id="clear_url", variant="default", classes="utility-button"))
            
            
            # 옵션 섹션 - 텍스트 기반 UI (여백 최소화 타이틀)
            form.mount(Static("", classes="line-spacer"))
            form.mount(Static("Options:", classes="options-title section-gap"))
            
            # 옵션 표시 (체크박스 스타일)
            self.option_widgets['timestamp'] = Button(Text(self._get_option_display(0, "Include timestamps", self.timestamp_enabled)), id="opt_timestamp", classes="content-text option-button")
            self.option_widgets['summary'] = Button(Text(self._get_option_display(1, "Generate AI summary", self.summary_enabled)), id="opt_summary", classes="content-text option-button")
            self.option_widgets['translate'] = Button(Text(self._get_option_display(2, "Translate", self.translate_enabled)), id="opt_translate", classes="content-text option-button")
            self.option_widgets['video'] = Button(Text(self._get_option_display(3, "Download video", self.video_enabled)), id="opt_video", classes="content-text option-button")
            self.option_widgets['srt'] = Button(Text(self._get_option_display(4, "Generate SRT (timestamps)", self.srt_enabled)), id="opt_srt", classes="content-text option-button")
            self.option_widgets['srt_translate'] = Button(Text(self._get_option_display(5, "Translate SRT", self.srt_translate_enabled)), id="opt_srt_translate", classes="content-text option-button")
            
            form.mount(self.option_widgets['timestamp'])
            form.mount(self.option_widgets['summary'])
            form.mount(self.option_widgets['translate'])
            form.mount(self.option_widgets['video'])
            form.mount(self.option_widgets['srt'])
            form.mount(self.option_widgets['srt_translate'])
            
            # 엔진 선택
            form.mount(Static("", classes="line-spacer"))
            form.mount(Static("Engine:", classes="options-title section-gap"))
            
            self.option_widgets['engine_mini'] = Button(Text(self._get_engine_display(6, "GPT-4o-mini (default, fast)", "gpt-4o-mini-transcribe")), id="eng_mini", classes="content-text option-button")
            self.option_widgets['engine_gpt4o'] = Button(Text(self._get_engine_display(7, "GPT-4o (high quality)", "gpt-4o-transcribe")), id="eng_gpt4o", classes="content-text option-button")
            self.option_widgets['engine_whisper_api'] = Button(Text(self._get_engine_display(8, "Whisper API (OpenAI cloud)", "whisper-api")), id="eng_whisper_api", classes="content-text option-button")
            self.option_widgets['engine_whisper_cpp'] = Button(Text(self._get_engine_display(9, "Whisper-cpp (local)", "whisper-cpp")), id="eng_whisper_cpp", classes="content-text option-button")
            self.option_widgets['engine_youtube'] = Button(Text(self._get_engine_display(10, "YouTube native", "youtube-transcript-api")), id="eng_youtube", classes="content-text option-button")
            
            form.mount(self.option_widgets['engine_mini'])
            form.mount(self.option_widgets['engine_gpt4o'])
            form.mount(self.option_widgets['engine_whisper_api'])
            form.mount(self.option_widgets['engine_whisper_cpp'])
            form.mount(self.option_widgets['engine_youtube'])
            
            # (네비게이션 안내 제거)
            
            # 출력 영역 (액션 바 아래) - 타이틀과 박스 간 여백 최소화
            form.mount(Static("", classes="line-spacer"))
            form.mount(Static("Output:", classes="options-title section-gap"))
            form.mount(Static("─" * 60, classes="divider-line"))
            form.mount(Static("Ready to transcribe...", classes="transcribe-output content-text"))
            
            # URL 입력에 포커스
            self.url_input.focus()
            # 초기 포커스 설정
            self.focused_option = 0
            self.update_option_displays()
    
    def _get_option_display(self, index: int, label: str, enabled: bool) -> str:
        """체크박스 스타일 옵션 표시 생성"""
        checkbox = "[*]" if enabled else "[ ]"
        return f"{checkbox} {label}"
    
    def _get_engine_display(self, index: int, label: str, engine_value: str) -> str:
        """엔진 표시 생성 - 선택시 체크박스 스타일로 표시"""
        checkbox = "[*]" if self.selected_engine == engine_value else "[ ]"
        return f"{checkbox} {label}"
    
    def update_option_displays(self) -> None:
        """모든 옵션 표시 업데이트"""
        if not self.option_widgets:
            return
            
        # 체크박스 업데이트
        if 'timestamp' in self.option_widgets:
            self.option_widgets['timestamp'].label = Text(self._get_option_display(0, "Include timestamps", self.timestamp_enabled))
        if 'summary' in self.option_widgets:
            self.option_widgets['summary'].label = Text(self._get_option_display(1, "Generate AI summary", self.summary_enabled))
        if 'translate' in self.option_widgets:
            self.option_widgets['translate'].label = Text(self._get_option_display(2, "Translate", self.translate_enabled))
        if 'video' in self.option_widgets:
            self.option_widgets['video'].label = Text(self._get_option_display(3, "Download video", self.video_enabled))
        if 'srt' in self.option_widgets:
            self.option_widgets['srt'].label = Text(self._get_option_display(4, "Generate SRT (timestamps)", self.srt_enabled))
        if 'srt_translate' in self.option_widgets:
            self.option_widgets['srt_translate'].label = Text(self._get_option_display(5, "Translate SRT", self.srt_translate_enabled))
        
        # 엔진 옵션 업데이트
        if 'engine_mini' in self.option_widgets:
            self.option_widgets['engine_mini'].label = Text(self._get_engine_display(6, "GPT-4o-mini (default, fast)", "gpt-4o-mini-transcribe"))
        if 'engine_gpt4o' in self.option_widgets:
            self.option_widgets['engine_gpt4o'].label = Text(self._get_engine_display(7, "GPT-4o (high quality)", "gpt-4o-transcribe"))
        if 'engine_whisper_api' in self.option_widgets:
            self.option_widgets['engine_whisper_api'].label = Text(self._get_engine_display(8, "Whisper API (OpenAI cloud)", "whisper-api"))
        if 'engine_whisper_cpp' in self.option_widgets:
            self.option_widgets['engine_whisper_cpp'].label = Text(self._get_engine_display(9, "Whisper-cpp (local)", "whisper-cpp"))
        if 'engine_youtube' in self.option_widgets:
            self.option_widgets['engine_youtube'].label = Text(self._get_engine_display(10, "YouTube native", "youtube-transcript-api"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 이벤트 처리 (메뉴/옵션/엔진 모두 포함)"""
        button_id = event.button.id
        
        # 메뉴 버튼 처리 (좌측 메뉴 영역의 버튼)
        if button_id in {"transcribe", "database", "api_keys", "settings", "monitor", "help", "quit"}:
            # 좌측 메뉴 클릭 시에도 동일한 동작을 수행
            if button_id == "transcribe":
                self.selected_button_id = "transcribe"
                self.show_transcribe_interface()
                self.focus_area = "content"
                try:
                    self.app.set_focus(self)
                except Exception:
                    pass
                self.set_timer(0.01, lambda btn_id="transcribe": self._update_button_selection(btn_id))
                return
            elif button_id == "database":
                self.show_content("Database Management", "Database management features will be implemented in Phase 4.")
                self.set_timer(0.01, lambda btn_id="database": self._update_button_selection(btn_id))
                return
            elif button_id == "api_keys":
                self.show_content("API Keys Management", "API keys management features will be implemented in Phase 4.")
                self.set_timer(0.01, lambda btn_id="api_keys": self._update_button_selection(btn_id))
                return
            elif button_id == "settings":
                self.show_content("Settings", "Settings features will be implemented in Phase 4.")
                self.set_timer(0.01, lambda btn_id="settings": self._update_button_selection(btn_id))
                return
            elif button_id == "monitor":
                self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
                self.set_timer(0.01, lambda btn_id="monitor": self._update_button_selection(btn_id))
                return
            elif button_id == "help":
                self.show_help()
                return
            elif button_id == "quit":
                self.app.exit()
                return

        # 오른쪽 콘텐츠 내의 버튼 처리
        if button_id == "transcribe":
            self.selected_button_id = "transcribe"
            self.show_transcribe_interface()
            self.focus_area = "content"
            try:
                self.app.set_focus(self)
            except Exception:
                pass
            self.set_timer(0.01, lambda btn_id="transcribe": self._update_button_selection(btn_id))
            return
        elif button_id == "start_transcribe":
            self.start_transcription()
            return
        elif button_id == "clear_url":
            self.clear_url_input()
            return
        # 옵션 토글
        if button_id == 'opt_timestamp':
            self.focused_option = 0
            self.timestamp_enabled = not self.timestamp_enabled
        elif button_id == 'opt_summary':
            self.focused_option = 1
            self.summary_enabled = not self.summary_enabled
        elif button_id == 'opt_translate':
            self.focused_option = 2
            self.translate_enabled = not self.translate_enabled
        elif button_id == 'opt_video':
            self.focused_option = 3
            self.video_enabled = not self.video_enabled
        elif button_id == 'opt_srt':
            self.focused_option = 4
            self.srt_enabled = not self.srt_enabled
        elif button_id == 'opt_srt_translate':
            self.focused_option = 5
            self.srt_translate_enabled = not self.srt_translate_enabled
            if self.srt_translate_enabled:
                self.srt_enabled = True
        # 엔진 선택
        elif button_id == 'eng_mini':
            self.focused_option = 6
            self.selected_engine = 'gpt-4o-mini-transcribe'
        elif button_id == 'eng_gpt4o':
            self.focused_option = 7
            self.selected_engine = 'gpt-4o-transcribe'
        elif button_id == 'eng_whisper_api':
            self.focused_option = 8
            self.selected_engine = 'whisper-api'
        elif button_id == 'eng_whisper_cpp':
            self.focused_option = 9
            self.selected_engine = 'whisper-cpp'
        elif button_id == 'eng_youtube':
            self.focused_option = 10
            self.selected_engine = 'youtube-transcript-api'
        else:
            return
        self.update_option_displays()
    
    def action_menu_action(self, menu_id: str) -> None:
        """키보드로 메뉴 선택"""
        self._update_button_selection(menu_id)
        
        if menu_id == "transcribe":
            # 오른쪽 콘텐츠 영역에 전사 인터페이스 표시
            self.show_transcribe_interface()
            self.focus_area = "content"
            try:
                self.app.set_focus(self)
            except Exception:
                pass
        elif menu_id == "database":
            self.show_content("Database Management", "Database management features will be implemented in Phase 4.")
        elif menu_id == "api_keys":
            self.show_content("API Keys Management", "API keys management features will be implemented in Phase 4.")
        elif menu_id == "settings":
            self.show_content("Settings", "Settings features will be implemented in Phase 4.")
        elif menu_id == "monitor":
            self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
        elif menu_id == "help":
            self.show_help()
        elif menu_id == "quit":
            self.app.exit()
    
    def action_press_focused_button(self) -> None:
        """현재 포커스된 버튼 눌러"""
        # 메뉴 영역에 있을 때만 동작하도록 가드
        if self.focus_area != "menu":
            return
        if self.menu_buttons and 0 <= self.current_focus < len(self.menu_buttons):
            # 현재 포커스된 버튼의 ID를 가져와서 직접 액션 실행
            button = self.menu_buttons[self.current_focus]
            button_id = button.id
            self._update_button_selection(button_id)
            
            # 버튼 클릭 이벤트를 시뮬레이션
            if button_id == "transcribe":
                # 오른쪽 콘텐츠 영역에 전사 인터페이스 표시
                self.show_transcribe_interface()
            elif button_id == "database":
                self.show_content("Database Management", "Database management features will be implemented in Phase 4.")
            elif button_id == "api_keys":
                self.show_content("API Keys Management", "API keys management features will be implemented in Phase 4.")
            elif button_id == "settings":
                self.show_content("Settings", "Settings features will be implemented in Phase 4.")
            elif button_id == "monitor":
                self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
            elif button_id == "help":
                self.show_help()
            elif button_id == "quit":
                self.app.exit()
    
    def action_navigate_up(self) -> None:
        """위쪽 메뉴로 이동"""
        if self.focus_area != "menu":
            return
        if self.menu_buttons:
            self.current_focus = (self.current_focus - 1) % len(self.menu_buttons)
            self.menu_buttons[self.current_focus].focus()
            self._scroll_to_focused()
    
    def action_navigate_down(self) -> None:
        """아래쪽 메뉴로 이동"""
        if self.focus_area != "menu":
            return
        if self.menu_buttons:
            self.current_focus = (self.current_focus + 1) % len(self.menu_buttons)
            self.menu_buttons[self.current_focus].focus()
            self._scroll_to_focused()
    
    def _scroll_to_focused(self) -> None:
        """현재 포커스된 메뉴 항목이 보이도록 전체 화면 스크롤"""
        if self.menu_buttons and 0 <= self.current_focus < len(self.menu_buttons):
            focused_button = self.menu_buttons[self.current_focus]
            # Textual의 기본 scroll_visible 사용
            focused_button.scroll_visible(animate=True)
    
    def action_focus_menu(self) -> None:
        """메뉴 영역에 포커스"""
        self.focus_area = "menu"
        print(f"DEBUG: Focus changed to menu area")
        if self.menu_buttons and 0 <= self.current_focus < len(self.menu_buttons):
            self.menu_buttons[self.current_focus].focus()
    
    def action_focus_content(self) -> None:
        """콘텐츠 영역에 포커스"""
        self.focus_area = "content"
        print(f"DEBUG: Focus changed to content area")
    
    # 통합 키 액션 (메뉴/콘텐츠 포커스에 따라 분기)
    def action_handle_up(self) -> None:
        if self.focus_area == "menu":
            self.action_navigate_up()
        else:
            if self.focused_option > 0:
                self.focused_option -= 1
                self.update_option_displays()

    def action_handle_down(self) -> None:
        if self.focus_area == "menu":
            self.action_navigate_down()
        else:
            if self.focused_option < self.total_options - 1:
                self.focused_option += 1
                self.update_option_displays()

    def action_handle_enter(self) -> None:
        if self.focus_area == "menu":
            self.action_press_focused_button()
            self.action_focus_content()
        else:
            # 콘텐츠 영역에서는 현재 항목 토글
            self.toggle_current_option()
            self.update_option_displays()

    def action_handle_space(self) -> None:
        if self.focus_area == "content":
            self.toggle_current_option()
    
    
    def start_transcription(self) -> None:
        """전사 시작"""
        self.app.notify("start_transcription called", severity="information")
        try:
            # URL 가져오기
            if not self.url_input:
                self.show_error("URL input not found")
                return
                
            url = self.url_input.value.strip()
            
            if not url:
                self.show_error("Please enter a YouTube URL")
                return
            
            # 선택된 엔진은 이미 self.selected_engine에 저장됨
            
            # 옵션 상태 가져오기
            options_text = []
            if self.timestamp_enabled:
                options_text.append("timestamps")
            if self.summary_enabled:
                options_text.append("summary")
            if self.translate_enabled:
                options_text.append("translation")
            if self.video_enabled:
                options_text.append("video download")
            
            # 출력 영역 업데이트
            output = self.content_area.query_one(".transcribe-output", Static)
            options_str = ", ".join(options_text) if options_text else "none"
            output.update(f"🔄 Starting transcription...\nURL: {url[:50]}...\nEngine: {self.selected_engine}\nOptions: {options_str}")
            
            # 실제 전사 실행: trans.py 호출 구성
            def run_worker():
                try:
                    args = [sys.executable, "trans.py", url, "--engine", self.selected_engine]
                    if self.timestamp_enabled:
                        args.append("--timestamp")
                    if self.summary_enabled:
                        args.append("--summary")
                    if self.translate_enabled:
                        args.append("--translate")
                    if self.video_enabled:
                        args.append("--video")
                    if self.srt_enabled:
                        args.append("--srt")
                    if self.srt_translate_enabled:
                        # SRT 번역은 --srt와 함께 동작. translate 옵션을 함께 전달
                        if "--srt" not in args:
                            args.append("--srt")
                        if "--translate" not in args:
                            args.append("--translate")
                    # 진행상황(선택): 옵션 영역에서 추후 추가 가능
                    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.getcwd())
                    for line in proc.stdout:
                        try:
                            out = self.content_area.query_one(".transcribe-output", Static)
                            out.update((out.renderable or "") + f"\n{line.rstrip()}" )
                        except Exception:
                            pass
                    proc.wait()
                    if proc.returncode == 0:
                        self.show_success("Transcription finished")
                    else:
                        self.show_error(f"Transcription failed (code {proc.returncode})")
                except Exception as e:
                    self.show_error(str(e))
            threading.Thread(target=run_worker, daemon=True).start()
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {e}")
            self.show_error(f"Error: {str(e)}")
    
    def clear_url_input(self) -> None:
        """URL 입력 및 모든 옵션 초기화"""
        try:
            # URL 초기화
            if self.url_input:
                self.url_input.value = ""
                self.url_input.focus()
            
            # 옵션 상태 초기화
            self.timestamp_enabled = False
            self.summary_enabled = False
            self.translate_enabled = False
            self.video_enabled = False
            self.selected_engine = "gpt-4o-mini-transcribe"
            self.focused_option = 0
            
            # UI 업데이트
            self.update_option_displays()
            
            # 출력 영역 초기화
            output = self.content_area.query_one(".transcribe-output", Static)
            output.update("Ready to transcribe...")
        except Exception as e:
            print(f"DEBUG: Error in clear_url_input: {e}")
    
    
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Input 위젯에서 엔터키가 눌렸을 때 처리"""
        if event.input.id == "url_input" or "url-input" in event.input.classes:
            # 엔터 입력 후 옵션 영역으로 포커스 이동
            self.focus_area = "content"
            self.focused_option = 0
            self.update_option_displays()
            # 시각적으로 옵션 라인으로 스크롤
            if 'timestamp' in self.option_widgets:
                self.option_widgets['timestamp'].scroll_visible(animate=True)
            # 입력 포커스 해제 및 상위로 포커스 이동
            try:
                self.url_input.blur()
            except Exception:
                pass
            try:
                self.app.set_focus(self)
            except Exception:
                pass
            # 이벤트 전파 중단 (바인딩 충돌 방지)
            try:
                event.stop()
            except Exception:
                pass
            # 바로 전사 시작이 아니라 옵션 선택 가능하도록 종료
    
    def on_key(self, event) -> None:
        """키보드 이벤트 직접 처리"""
        key = event.key
        
        # Transcribe 인터페이스가 활성화된 경우
        if self.selected_button_id == "transcribe" and self.option_widgets and self.focus_area == "content":
            # 단축키만 유지 (s: start, c: clear). 화살표/엔터/스페이스는 바인딩 액션으로 처리
            if key == "s" or key == "S":
                self.start_transcription()
                return
            elif key == "c" or key == "C":
                self.clear_url_input()
                return
        
        # 숫자 키 처리 (메뉴 선택)
        if key == "1":
            self.action_menu_action("transcribe")
        elif key == "2":
            self.action_menu_action("database")
        elif key == "3":
            self.action_menu_action("api_keys")
        elif key == "4":
            self.action_menu_action("settings")
        elif key == "5":
            self.action_menu_action("monitor")
        elif key == "h":
            self.action_menu_action("help")
        elif key == "q" or key == "ㅂ":
            self.action_menu_action("quit")
        elif key == "escape":
            self.action_menu_action("quit")
        # 화살표 키 처리 (메뉴 네비게이션)
        elif key == "up" or key == "k":
            self.action_handle_up()
        elif key == "down" or key == "j":
            self.action_handle_down()
        elif key == "left":
            # 왼쪽 방향키로 메뉴로 복귀
            self.action_focus_menu()
        elif key == "right":
            self.action_focus_content()
        elif key == "enter":
            self.action_handle_enter()
            return
        elif key == "space":
            self.action_handle_space()
            return
        else:
            # 처리되지 않은 키는 부모로 전달
            event.prevent_default = False
    
    def toggle_current_option(self) -> None:
        """현재 포커스된 옵션 토글"""
        if self.focused_option < 4:
            # 체크박스 옵션
            if self.focused_option == 0:
                self.timestamp_enabled = not self.timestamp_enabled
            elif self.focused_option == 1:
                self.summary_enabled = not self.summary_enabled
            elif self.focused_option == 2:
                self.translate_enabled = not self.translate_enabled
            elif self.focused_option == 3:
                self.video_enabled = not self.video_enabled
            elif self.focused_option == 4:
                self.srt_enabled = not self.srt_enabled
            elif self.focused_option == 5:
                # SRT 번역은 SRT 생성이 함께 활성화되어야 함
                self.srt_translate_enabled = not self.srt_translate_enabled
                if self.srt_translate_enabled:
                    self.srt_enabled = True
        else:
            # 엔진 옵션 (라디오 버튼)
            if self.focused_option == 6:
                self.selected_engine = "gpt-4o-mini-transcribe"
            elif self.focused_option == 7:
                self.selected_engine = "gpt-4o-transcribe"
            elif self.focused_option == 8:
                self.selected_engine = "whisper-api"
            elif self.focused_option == 9:
                self.selected_engine = "whisper-cpp"
            elif self.focused_option == 10:
                self.selected_engine = "youtube-transcript-api"
        
        # UI 업데이트
        self.update_option_displays()