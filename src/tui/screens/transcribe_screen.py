"""Transcribe 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, Label, Switch, RadioButton, RadioSet
from textual.widget import Widget
from textual.app import ComposeResult
from textual.binding import Binding
from typing import Optional
import subprocess
import os
import asyncio


class TranscribeScreen(Widget):
    """Transcribe 화면"""
    
    BINDINGS = [
        Binding("escape", "back_to_menu", "Back", priority=True),
        Binding("ctrl+t", "start_transcription", "Start", priority=True),
        Binding("ctrl+c", "clear_form", "Clear", priority=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url_input = None
        self.engine_radio = None
        self.timestamp_switch = None
        self.summary_switch = None
        self.translate_switch = None
        self.video_switch = None
        self.srt_switch = None
        self.output_display = None
        
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="transcribe-container"):
            yield Static("New Transcription", classes="screen-title")
            yield Static("─" * 80, classes="divider-line")
            
            # URL 입력
            with Vertical(classes="input-group"):
                yield Label("YouTube URL:")
                yield Input(
                    placeholder="https://www.youtube.com/watch?v=...", 
                    id="url_input", 
                    classes="main-input",
                    value="",  # 초기값 명시
                )
            
            # 엔진 선택
            with Vertical(classes="input-group"):
                yield Label("Transcription Engine:")
                with RadioSet(id="engine_radio"):
                    yield RadioButton("gpt-4o-mini-transcribe (default)", id="engine_mini", value=True)
                    yield RadioButton("gpt-4o-transcribe (high quality)", id="engine_4o")
                    yield RadioButton("whisper-api (OpenAI Whisper)", id="engine_whisper")
                    yield RadioButton("whisper-cpp (Local whisper)", id="engine_cpp")
                    yield RadioButton("youtube-transcript-api (YouTube native)", id="engine_youtube")
            
            # 옵션들
            with Horizontal(classes="checkbox-group"):
                with Vertical():
                    yield Label("Options:")
                    with Horizontal():
                        yield Switch(id="timestamp_switch", value=False)
                        yield Label(" Include timestamps")
                    with Horizontal():
                        yield Switch(id="summary_switch", value=False)
                        yield Label(" Generate AI summary")
                    with Horizontal():
                        yield Switch(id="translate_switch", value=False)
                        yield Label(" Translate")
                
                with Vertical():
                    yield Label("Video Options:")
                    with Horizontal():
                        yield Switch(id="video_switch", value=False)
                        yield Label(" Download video")
                    with Horizontal():
                        yield Switch(id="srt_switch", value=False)
                        yield Label(" Generate SRT subtitles")
            
            # 출력 영역
            yield Static("─" * 80, classes="divider-line")
            yield Static("Output:", classes="section-title")
            with Vertical(classes="output-display", id="output_display"):
                yield Static("Transcription output will appear here...", classes="output-placeholder")
            
            # 버튼들 (하단에 위치)
            yield Static("─" * 80, classes="divider-line")
            with Horizontal(classes="button-group"):
                yield Button("Start Transcription", id="start_btn", variant="primary", classes="action-button")
                yield Button("Clear", id="clear_btn", variant="default", classes="utility-button")
                yield Button("Back", id="back_btn", variant="default", classes="utility-button")
    
    def on_mount(self) -> None:
        """화면 마운트 시 위젯 저장"""
        self.url_input = self.query_one("#url_input", Input)
        self.engine_radio = self.query_one("#engine_radio", RadioSet)
        self.timestamp_switch = self.query_one("#timestamp_switch", Switch)
        self.summary_switch = self.query_one("#summary_switch", Switch)
        self.translate_switch = self.query_one("#translate_switch", Switch)
        self.video_switch = self.query_one("#video_switch", Switch)
        self.srt_switch = self.query_one("#srt_switch", Switch)
        self.output_display = self.query_one("#output_display", Vertical)
        
        # URL 입력 초기화 및 포커스
        self.url_input.value = ""
        # 약간의 지연 후 포커스 설정 (화면이 완전히 로드된 후)
        self.set_timer(0.1, lambda: self.url_input.focus())
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Input 값이 변경될 때 호출"""
        if event.input.id == "url_input":
            # URL이 입력되고 있음을 확인 (디버깅용)
            self.app.notify(f"URL Input: {event.value[:50]}...", timeout=1)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 이벤트 처리"""
        button_id = event.button.id
        
        if button_id == "start_btn":
            self.start_transcription()
        elif button_id == "clear_btn":
            self.clear_form()
        elif button_id == "back_btn":
            self.action_back_to_menu()
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """스위치 변경 이벤트 처리"""
        # video가 켜지면 srt도 자동으로 켜짐
        if event.switch.id == "video_switch" and event.value:
            self.srt_switch.value = True
        
        # srt가 켜지면 translate도 자동으로 켜짐 (필요시)
        if event.switch.id == "srt_switch" and event.value:
            # 향후 언어 감지 후 한국어가 아닌 경우만 translate 활성화
            pass
    
    def get_selected_engine(self) -> str:
        """선택된 엔진 가져오기"""
        if self.query_one("#engine_mini", RadioButton).value:
            return "gpt-4o-mini-transcribe"
        elif self.query_one("#engine_4o", RadioButton).value:
            return "gpt-4o-transcribe"
        elif self.query_one("#engine_whisper", RadioButton).value:
            return "whisper-api"
        elif self.query_one("#engine_cpp", RadioButton).value:
            return "whisper-cpp"
        elif self.query_one("#engine_youtube", RadioButton).value:
            return "youtube-transcript-api"
        return "gpt-4o-mini-transcribe"
    
    def start_transcription(self) -> None:
        """전사 시작"""
        url = self.url_input.value.strip()
        
        if not url:
            self.show_output("Error: Please enter a YouTube URL", error=True)
            return
        
        # 명령어 구성
        cmd = ["python", "main.py", url]
        
        # 엔진 옵션
        engine = self.get_selected_engine()
        cmd.extend(["--engine", engine])
        
        # 옵션들 추가
        if self.timestamp_switch.value:
            cmd.append("--timestamp")
        if self.summary_switch.value:
            cmd.append("--summary")
        if self.translate_switch.value:
            cmd.append("--translate")
        if self.video_switch.value:
            cmd.append("--video")
        if self.srt_switch.value:
            cmd.append("--srt")
        
        # 진행 상황 표시
        cmd.append("--progress")
        
        # 출력 표시
        self.show_output(f"Starting transcription...\nCommand: {' '.join(cmd)}\n")
        
        # 비동기로 명령 실행
        self.run_transcription_async(cmd)
    
    def run_transcription_async(self, cmd: list) -> None:
        """비동기로 전사 실행"""
        async def run():
            try:
                # Virtual environment 활성화 확인
                venv_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                    '.venv'
                )
                
                # 환경 변수 설정
                env = os.environ.copy()
                
                # venv가 있으면 사용
                if os.path.exists(venv_path):
                    if os.name == 'posix':  # Unix/Linux/Mac
                        env['PATH'] = f"{os.path.join(venv_path, 'bin')}:{env.get('PATH', '')}"
                        python_cmd = os.path.join(venv_path, 'bin', 'python')
                    else:  # Windows
                        env['PATH'] = f"{os.path.join(venv_path, 'Scripts')};{env.get('PATH', '')}"
                        python_cmd = os.path.join(venv_path, 'Scripts', 'python.exe')
                    
                    # Python 경로를 venv 경로로 변경
                    cmd[0] = python_cmd
                
                # subprocess 실행
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                )
                
                # stdout과 stderr를 동시에 읽기
                async def read_stream(stream, prefix=""):
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        text = line.decode('utf-8', errors='replace')
                        if prefix and not text.strip().startswith(prefix):
                            text = f"{prefix}: {text}"
                        self.app.call_from_thread(self.append_output, text)
                
                # 두 스트림을 동시에 읽기
                await asyncio.gather(
                    read_stream(process.stdout),
                    read_stream(process.stderr, "")
                )
                
                # 프로세스 종료 대기
                await process.wait()
                
                if process.returncode == 0:
                    self.app.call_from_thread(self.append_output, "\nTranscription completed successfully!\n")
                else:
                    self.app.call_from_thread(self.append_output, f"\nTranscription failed with code {process.returncode}\n")
                    
            except Exception as e:
                self.app.call_from_thread(self.append_output, f"\nError: {str(e)}\n")
        
        # 태스크 생성 및 실행
        asyncio.create_task(run())
    
    def show_output(self, text: str, error: bool = False) -> None:
        """출력 영역에 텍스트 표시"""
        self.output_display.remove_children()
        style_class = "error" if error else "output-text"
        self.output_display.mount(Static(text, classes=style_class))
    
    def append_output(self, text: str) -> None:
        """출력 영역에 텍스트 추가"""
        # placeholder 제거
        placeholder = self.output_display.query(".output-placeholder")
        if placeholder:
            for p in placeholder:
                p.remove()
        
        # 텍스트 처리 - 여러 줄인 경우 각 줄을 별도로 추가
        lines = text.rstrip().split('\n')
        for line in lines:
            if line:  # 빈 줄 제외
                # 진행 상황 표시줄이나 특별한 출력 스타일링
                if "%" in line and ("━" in line or "=" in line or "-" in line):  # Progress bar
                    self.output_display.mount(Static(line, classes="output-text progress-line"))
                elif line.startswith("Error:") or "failed" in line.lower():
                    self.output_display.mount(Static(line, classes="output-text error"))
                elif "completed" in line.lower() or "success" in line.lower():
                    self.output_display.mount(Static(line, classes="output-text success"))
                elif line.startswith("Warning:"):
                    self.output_display.mount(Static(line, classes="output-text warning"))
                else:
                    self.output_display.mount(Static(line, classes="output-text"))
        
        # 스크롤을 맨 아래로
        self.output_display.scroll_end()
    
    def clear_form(self) -> None:
        """폼 초기화"""
        self.url_input.value = ""
        self.query_one("#engine_mini", RadioButton).value = True
        self.timestamp_switch.value = False
        self.summary_switch.value = False
        self.translate_switch.value = False
        self.video_switch.value = False
        self.srt_switch.value = False
        self.show_output("Transcription output will appear here...", error=False)
        self.url_input.focus()
    
    def action_back_to_menu(self) -> None:
        """메뉴로 돌아가기"""
        # 부모 앱에 이벤트 전달
        if hasattr(self.app, 'show_main_menu'):
            self.app.show_main_menu()
    
    def action_start_transcription(self) -> None:
        """단축키로 전사 시작"""
        self.start_transcription()
    
    def action_clear_form(self) -> None:
        """단축키로 폼 초기화"""
        self.clear_form()