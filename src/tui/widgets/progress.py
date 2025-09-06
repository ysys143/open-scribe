"""진행률 및 상태 표시 위젯"""

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import ProgressBar, Static, Label, Log
from textual.widget import Widget
from textual.app import ComposeResult
from textual.reactive import reactive
from typing import Optional
from datetime import datetime
import asyncio


class TaskProgressWidget(Widget):
    """개별 작업 진행률 위젯"""
    
    progress = reactive(0.0)
    status = reactive("대기 중")
    task_name = reactive("작업")
    
    def __init__(
        self,
        task_name: str = "작업",
        show_percentage: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.task_name = task_name
        self.show_percentage = show_percentage
        self.start_time = None
        self.end_time = None
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Container(classes="task-progress"):
            yield Label(self.task_name, classes="task-name")
            yield ProgressBar(
                total=100,
                show_percentage=self.show_percentage,
                classes="task-bar"
            )
            yield Static(self.status, classes="task-status")
            yield Static("", id="task-time", classes="task-time")
    
    def watch_progress(self, progress: float) -> None:
        """진행률 변경 감지"""
        progress_bar = self.query_one(ProgressBar)
        progress_bar.progress = min(100, max(0, progress))
        
        if progress > 0 and self.start_time is None:
            self.start_time = datetime.now()
            
        if progress >= 100 and self.end_time is None:
            self.end_time = datetime.now()
        
        self.update_time_display()
    
    def watch_status(self, status: str) -> None:
        """상태 변경 감지"""
        status_widget = self.query_one(".task-status", Static)
        status_widget.update(status)
    
    def watch_task_name(self, task_name: str) -> None:
        """작업명 변경 감지"""
        name_widget = self.query_one(".task-name", Label)
        name_widget.update(task_name)
    
    def update_time_display(self) -> None:
        """시간 표시 업데이트"""
        time_widget = self.query_one("#task-time", Static)
        
        if self.start_time is None:
            time_widget.update("")
            return
        
        if self.end_time:
            elapsed = self.end_time - self.start_time
            time_widget.update(f"완료 ({elapsed.total_seconds():.1f}초)")
        else:
            elapsed = datetime.now() - self.start_time
            time_widget.update(f"진행 중 ({elapsed.total_seconds():.1f}초)")
    
    def set_progress(self, progress: float, status: str = None) -> None:
        """진행률 및 상태 설정"""
        self.progress = progress
        if status:
            self.status = status
    
    def set_completed(self, status: str = "완료") -> None:
        """완료 상태로 설정"""
        self.set_progress(100, status)
    
    def set_error(self, error_msg: str) -> None:
        """에러 상태로 설정"""
        self.status = f"❌ {error_msg}"
        self.query_one(ProgressBar).add_class("error")


class MultiTaskProgressWidget(Widget):
    """다중 작업 진행률 위젯"""
    
    overall_progress = reactive(0.0)
    current_task = reactive("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks = {}  # task_id -> TaskProgressWidget
        self.task_order = []
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Container(classes="multi-task-progress"):
            yield Static("▲ 전체 진행률", classes="section-title")
            
            with Container(classes="overall-progress"):
                yield Label("전체 진행률", classes="overall-label")
                yield ProgressBar(
                    total=100,
                    show_percentage=True,
                    classes="overall-bar"
                )
                yield Static("대기 중", id="overall-status", classes="overall-status")
            
            yield Static("≡ 작업 목록", classes="section-title")
            with Vertical(id="task-list", classes="task-list"):
                pass  # 동적으로 작업 추가됨
    
    def watch_overall_progress(self, progress: float) -> None:
        """전체 진행률 변경 감지"""
        progress_bar = self.query_one(".overall-bar", ProgressBar)
        progress_bar.progress = min(100, max(0, progress))
    
    def watch_current_task(self, task: str) -> None:
        """현재 작업 변경 감지"""
        status_widget = self.query_one("#overall-status", Static)
        if task:
            status_widget.update(f"현재: {task}")
        else:
            status_widget.update("대기 중")
    
    def add_task(self, task_id: str, task_name: str) -> TaskProgressWidget:
        """작업 추가"""
        if task_id in self.tasks:
            return self.tasks[task_id]
        
        task_widget = TaskProgressWidget(task_name=task_name)
        self.tasks[task_id] = task_widget
        self.task_order.append(task_id)
        
        # UI에 추가
        task_list = self.query_one("#task-list", Vertical)
        task_list.mount(task_widget)
        
        self.update_overall_progress()
        return task_widget
    
    def update_task(self, task_id: str, progress: float, status: str = None) -> None:
        """작업 업데이트"""
        if task_id in self.tasks:
            self.tasks[task_id].set_progress(progress, status)
            if status:
                self.current_task = f"{self.tasks[task_id].task_name}: {status}"
            self.update_overall_progress()
    
    def complete_task(self, task_id: str, status: str = "완료") -> None:
        """작업 완료"""
        if task_id in self.tasks:
            self.tasks[task_id].set_completed(status)
            self.update_overall_progress()
    
    def error_task(self, task_id: str, error_msg: str) -> None:
        """작업 에러"""
        if task_id in self.tasks:
            self.tasks[task_id].set_error(error_msg)
            self.update_overall_progress()
    
    def update_overall_progress(self) -> None:
        """전체 진행률 계산 및 업데이트"""
        if not self.tasks:
            self.overall_progress = 0
            return
        
        total_progress = sum(task.progress for task in self.tasks.values())
        self.overall_progress = total_progress / len(self.tasks)
    
    def clear_tasks(self) -> None:
        """모든 작업 제거"""
        task_list = self.query_one("#task-list", Vertical)
        for task_widget in self.tasks.values():
            task_widget.remove()
        
        self.tasks.clear()
        self.task_order.clear()
        self.overall_progress = 0
        self.current_task = ""


class RealTimeLogWidget(Widget):
    """실시간 로그 표시 위젯"""
    
    def __init__(self, max_lines: int = 1000, **kwargs):
        super().__init__(**kwargs)
        self.max_lines = max_lines
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Container(classes="realtime-log"):
            yield Static("📜 실시간 로그", classes="section-title")
            yield Log(
                highlight=True,
                markup=True,
                max_lines=self.max_lines,
                id="log-display",
                classes="log-display"
            )
    
    def add_log(self, message: str, level: str = "info") -> None:
        """로그 메시지 추가"""
        log_widget = self.query_one("#log-display", Log)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 레벨에 따른 색상 및 아이콘
        level_styles = {
            "debug": ("○", "dim"),
            "info": ("ℹ️", "blue"),
            "warning": ("⚠️", "yellow"),
            "error": ("❌", "red"),
            "success": ("✅", "green")
        }
        
        icon, color = level_styles.get(level, ("📝", "white"))
        
        formatted_message = f"[{color}]{timestamp} {icon} {message}[/{color}]"
        log_widget.write_line(formatted_message)
    
    def clear_log(self) -> None:
        """로그 지우기"""
        log_widget = self.query_one("#log-display", Log)
        log_widget.clear()
    
    def add_debug(self, message: str) -> None:
        """디버그 로그 추가"""
        self.add_log(message, "debug")
    
    def add_info(self, message: str) -> None:
        """정보 로그 추가"""
        self.add_log(message, "info")
    
    def add_warning(self, message: str) -> None:
        """경고 로그 추가"""
        self.add_log(message, "warning")
    
    def add_error(self, message: str) -> None:
        """에러 로그 추가"""
        self.add_log(message, "error")
    
    def add_success(self, message: str) -> None:
        """성공 로그 추가"""
        self.add_log(message, "success")


class StatusBarWidget(Widget):
    """상태 바 위젯"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_status = "준비"
        self.progress_info = ""
        self.time_info = ""
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Horizontal(classes="status-bar"):
            yield Static("🟢", id="status-icon", classes="status-icon")
            yield Static(self.current_status, id="status-text", classes="status-text")
            yield Static("", id="progress-info", classes="progress-info")
            yield Static("", id="time-info", classes="time-info")
    
    def update_status(self, status: str, icon: str = "🟢") -> None:
        """상태 업데이트"""
        self.current_status = status
        
        self.query_one("#status-icon", Static).update(icon)
        self.query_one("#status-text", Static).update(status)
    
    def update_progress_info(self, info: str) -> None:
        """진행률 정보 업데이트"""
        self.progress_info = info
        self.query_one("#progress-info", Static).update(info)
    
    def update_time_info(self, info: str) -> None:
        """시간 정보 업데이트"""
        self.time_info = info
        self.query_one("#time-info", Static).update(info)
    
    def set_working(self, status: str = "작업 중") -> None:
        """작업 중 상태"""
        self.update_status(status, "🟡")
    
    def set_error(self, status: str = "오류") -> None:
        """오류 상태"""
        self.update_status(status, "🔴")
    
    def set_success(self, status: str = "완료") -> None:
        """완료 상태"""
        self.update_status(status, "🟢")
    
    def set_ready(self, status: str = "준비") -> None:
        """준비 상태"""
        self.update_status(status, "🟢")


class CompactProgressWidget(Widget):
    """간단한 진행률 위젯 (작은 공간용)"""
    
    def __init__(self, task_name: str = "", **kwargs):
        super().__init__(**kwargs)
        self.task_name = task_name
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Horizontal(classes="compact-progress"):
            if self.task_name:
                yield Label(f"{self.task_name}:", classes="compact-label")
            yield ProgressBar(total=100, classes="compact-bar")
            yield Static("0%", id="compact-percent", classes="compact-percent")
    
    def update_progress(self, progress: float, status: str = None) -> None:
        """진행률 업데이트"""
        progress_bar = self.query_one(ProgressBar)
        percent_widget = self.query_one("#compact-percent", Static)
        
        progress = min(100, max(0, progress))
        progress_bar.progress = progress
        
        if status:
            percent_widget.update(status)
        else:
            percent_widget.update(f"{progress:.0f}%")