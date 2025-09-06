"""백그라운드 작업 모니터링 화면"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button, DataTable, ProgressBar, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
from textual.timer import Timer

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import threading
import asyncio

from .base import BaseScreen
from ..utils.db_manager import DatabaseManager


class JobMonitorWidget(Static):
    """개별 작업 모니터 위젯"""
    
    def __init__(self, job_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_id = job_id
        self.start_time = datetime.now()
        
    def update_job(self, job_data: dict):
        """작업 상태 업데이트"""
        status = job_data.get('status', 'pending')
        title = job_data.get('title', 'Unknown')[:40]
        engine = job_data.get('engine', 'unknown')
        progress = job_data.get('progress', 0)
        
        # 상태 이모지
        status_emoji = {
            'pending': '[P]',
            'running': '[R]',
            'completed': '[D]',
            'failed': '[F]',
            'cancelled': '[X]'
        }.get(status, '[?]')
        
        # 진행률 바
        bar_length = 30
        filled = int(bar_length * progress / 100)
        progress_bar = '█' * filled + '░' * (bar_length - filled)
        
        # 경과 시간
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        content = (
            f"{status_emoji} Job #{self.job_id}: {title}\n"
            f"Engine: {engine} | Status: {status}\n"
            f"[{progress_bar}] {progress:.1f}% | Elapsed: {elapsed_str}"
        )
        
        self.update(content)


class MonitorScreen(BaseScreen):
    """백그라운드 작업 모니터링 화면"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("c", "cancel_job", "Cancel", priority=True),
        Binding("delete", "remove_completed", "Clear", priority=True),
        Binding("a", "add_job", "Add Job", priority=True),
    ]
    
    # Reactive properties
    total_jobs = reactive(0)
    pending_jobs = reactive(0)
    running_jobs = reactive(0)
    completed_jobs = reactive(0)
    failed_jobs = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.job_widgets: Dict[int, JobMonitorWidget] = {}
        self.update_timer: Optional[Timer] = None
        self.selected_job_id: Optional[int] = None
        
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Static("== Job Monitor ==", classes="screen-title")
        
        with Vertical(classes="monitor-container"):
            # 통계 섹션
            with Horizontal(classes="stats-section", id="stats_section"):
                yield Label(f"Total: {self.total_jobs}", id="total_label")
                yield Label(f"[PENDING] Pending: {self.pending_jobs}", id="pending_label")
                yield Label(f"[RUNNING] Running: {self.running_jobs}", id="running_label")
                yield Label(f"[DONE] Completed: {self.completed_jobs}", id="completed_label")
                yield Label(f"[FAILED] Failed: {self.failed_jobs}", id="failed_label")
            
            # 작업 큐 테이블
            with Vertical(classes="queue-section", id="queue_section"):
                yield Static("== Job Queue ==", classes="section-title")
                yield DataTable(id="queue_table")
            
            # 활성 작업 모니터
            with Vertical(classes="active-jobs", id="active_jobs_section"):
                yield Static("== Active Jobs ==", classes="section-title")
                yield ScrollableContainer(id="active_container")
            
            # 컨트롤 버튼
            with Horizontal(classes="control-buttons"):
                yield Button("Back", id="back_btn", variant="primary")
                yield Button("Refresh", id="refresh_btn", variant="default")
                yield Button("Cancel Selected", id="cancel_btn", variant="warning")
                yield Button("Clear Completed", id="clear_btn", variant="default")
                yield Button("Add Job", id="add_btn", variant="success")
    
    def on_mount(self) -> None:
        """화면 마운트 시"""
        # 큐 테이블 설정
        table = self.query_one("#queue_table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Title", "URL", "Engine", "Status", "Priority", "Created", "Started", "Progress")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_cursor = True
        
        # 초기 데이터 로드
        self.load_data()
        
        # 자동 업데이트 타이머 시작 (2초마다)
        self.update_timer = self.set_interval(2.0, self.auto_refresh)
    
    def load_data(self) -> None:
        """데이터 로드 및 표시"""
        # 통계 업데이트
        stats = self.db.get_job_statistics()
        self.total_jobs = stats.get('total', 0)
        self.pending_jobs = stats.get('pending', 0)
        self.running_jobs = stats.get('running', 0)
        self.completed_jobs = stats.get('completed', 0)
        self.failed_jobs = stats.get('failed', 0)
        
        # 라벨 업데이트
        self.query_one("#total_label", Label).update(f"Total: {self.total_jobs}")
        self.query_one("#pending_label", Label).update(f"[PENDING] Pending: {self.pending_jobs}")
        self.query_one("#running_label", Label).update(f"[RUNNING] Running: {self.running_jobs}")
        self.query_one("#completed_label", Label).update(f"[DONE] Completed: {self.completed_jobs}")
        self.query_one("#failed_label", Label).update(f"[FAILED] Failed: {self.failed_jobs}")
        
        # 큐 테이블 업데이트
        self.update_queue_table()
        
        # 활성 작업 업데이트
        self.update_active_jobs()
    
    def update_queue_table(self) -> None:
        """큐 테이블 업데이트"""
        table = self.query_one("#queue_table", DataTable)
        table.clear(columns=False)
        
        # 최근 작업들 가져오기 (pending, running 우선)
        jobs = self.db.get_jobs_filtered(limit=50)
        
        # pending/running 작업을 상단에 표시
        sorted_jobs = sorted(jobs, key=lambda x: (
            0 if x.get('status') == 'running' else
            1 if x.get('status') == 'pending' else
            2 if x.get('status') == 'failed' else
            3
        ))
        
        for job in sorted_jobs[:20]:  # 최대 20개 표시
            job_id = job.get('id', 0)
            title = job.get('title', '')[:30] + ('...' if len(job.get('title', '')) > 30 else '')
            url = job.get('url', '')[:30] + ('...' if len(job.get('url', '')) > 30 else '')
            engine = job.get('engine', '')
            status = job.get('status', 'unknown')
            priority = job.get('priority', 0)
            created = job.get('created_at', '')[:16] if job.get('created_at') else ''
            started = job.get('started_at', '')[:16] if job.get('started_at') else ''
            progress = job.get('progress', 0)
            
            # 진행률 표시
            if status == 'running':
                progress_str = f"{progress:.1f}%"
            elif status == 'completed':
                progress_str = "100%"
            else:
                progress_str = "-"
            
            table.add_row(
                str(job_id),
                title,
                url,
                engine,
                status,
                str(priority),
                created,
                started,
                progress_str
            )
    
    def update_active_jobs(self) -> None:
        """활성 작업 모니터 업데이트"""
        container = self.query_one("#active_container", ScrollableContainer)
        
        # 실행 중인 작업들 가져오기
        running_jobs = self.db.get_jobs_filtered(status_filter='running', limit=10)
        
        # 현재 표시된 작업 ID들
        current_ids = set(self.job_widgets.keys())
        new_ids = {job['id'] for job in running_jobs}
        
        # 제거할 위젯 (완료되거나 실패한 작업)
        to_remove = current_ids - new_ids
        for job_id in to_remove:
            if job_id in self.job_widgets:
                self.job_widgets[job_id].remove()
                del self.job_widgets[job_id]
        
        # 새로운 위젯 추가 또는 업데이트
        for job in running_jobs:
            job_id = job['id']
            if job_id not in self.job_widgets:
                # 새 위젯 생성
                widget = JobMonitorWidget(job_id, classes="job-monitor")
                self.job_widgets[job_id] = widget
                container.mount(widget)
            
            # 위젯 업데이트
            self.job_widgets[job_id].update_job(job)
    
    def auto_refresh(self) -> None:
        """자동 새로고침"""
        self.load_data()
    
    def action_refresh(self) -> None:
        """수동 새로고침"""
        self.load_data()
        self.app.notify("Refreshed", severity="information")
    
    def action_cancel_job(self) -> None:
        """선택된 작업 취소"""
        table = self.query_one("#queue_table", DataTable)
        if table.cursor_row is not None and table.cursor_row >= 0:
            row = table.get_row_at(table.cursor_row)
            if row:
                job_id = int(row[0])
                status = row[4]  # Status column
                
                if status in ['pending', 'running']:
                    # 작업 취소 처리
                    self.db.update_job_status(job_id, 'cancelled')
                    self.app.notify(f"Job #{job_id} cancelled", severity="warning")
                    self.load_data()
                else:
                    self.app.notify(f"Cannot cancel job with status: {status}", severity="error")
    
    def action_remove_completed(self) -> None:
        """완료된 작업들 제거"""
        # 완료된 작업들 삭제
        result = self.db.delete_jobs_by_status(['completed', 'failed', 'cancelled'])
        count = result.get('rows', 0)
        self.app.notify(f"Removed {count} completed/failed jobs", severity="information")
        self.load_data()
    
    def action_add_job(self) -> None:
        """새 작업 추가 (transcribe 화면으로 이동)"""
        # transcribe 화면으로 이동
        self.app.push_screen("transcribe_screen")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 이벤트 처리"""
        button_id = event.button.id
        
        if button_id == "back_btn":
            self.app.pop_screen()
        elif button_id == "refresh_btn":
            self.action_refresh()
        elif button_id == "cancel_btn":
            self.action_cancel_job()
        elif button_id == "clear_btn":
            self.action_remove_completed()
        elif button_id == "add_btn":
            self.action_add_job()
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """테이블 행 선택 시"""
        table = self.query_one("#queue_table", DataTable)
        if table.cursor_row is not None and table.cursor_row >= 0:
            row = table.get_row_at(table.cursor_row)
            if row:
                self.selected_job_id = int(row[0])
    
    def on_unmount(self) -> None:
        """화면 언마운트 시"""
        # 타이머 정지
        if self.update_timer:
            self.update_timer.stop()