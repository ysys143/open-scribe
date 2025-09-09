"""데이터베이스 관리 화면"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button, DataTable
from textual.binding import Binding
from textual import events
from textual.screen import ModalScreen
from textual.events import Click, MouseEvent, MouseDown, MouseUp, MouseScrollDown, MouseScrollUp
from textual.coordinate import Coordinate

from .base import BaseScreen
from ..utils.db_manager import DatabaseManager
from ...config import Config


class DatabaseScreen(BaseScreen):
    """데이터베이스 관리 화면"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("ctrl+r", "refresh", "Refresh", priority=True),
        Binding("delete", "delete_selected", "Delete", priority=True),
        Binding("ctrl+d", "delete_all", "DelAll", priority=True),
        Binding("space", "toggle_select", "Toggle", priority=True),
        Binding("enter", "open_viewer", "Open", priority=True),
        Binding("b", "back_to_main", "Back", priority=True),
        Binding("d", "delete_selected", "Delete Selected", priority=True),
        Binding("a", "delete_all", "Delete All", priority=True),
        Binding("1", "filter_all", "All", priority=True),
        Binding("2", "filter_completed", "Completed", priority=True),
        Binding("3", "filter_running", "Running", priority=True),
        Binding("4", "filter_failed", "Failed", priority=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_filter = "all"
        self.search_query = ""
        self._confirm_mode = None  # 'selected' or 'all'
        self._selected_ids: set[int] = set()
        self._viewer_open = False
        self._last_jobs_snapshot: list[dict] = []
        self._debug = Config.DEBUG
        self._current_view_job_id: int | None = None
        self._confirm_context: dict | None = None
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Static("▣ Database", classes="screen-title")
        
        with Vertical(classes="db-container"):
            # 버튼 일렬 배치
            with Horizontal(id="db_btn_row"):
                yield Button("Back (b)", id="back_button", classes="action-button")
                yield Button("Delete Selected (d)", id="delete_selected", classes="warning-button")
                yield Button("Delete All (a)", id="delete_all", classes="danger-button")
                yield Button("All (1)", id="filter_all", classes="utility-button")
                yield Button("Completed (2)", id="filter_completed", classes="utility-button")
                yield Button("Running (3)", id="filter_running", classes="utility-button")
                yield Button("Failed (4)", id="filter_failed", classes="utility-button")
            with Vertical(id="db_table_wrap"):
                yield DataTable(id="jobs_table")
    
    def on_mount(self) -> None:
        table = self.query_one("#jobs_table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Title", "URL", "Engine", "Status", "Created", "Completed", "Size", "Files")
        # 기본 설정
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_cursor = True  # 커서 표시
        table.can_focus = True  # 포커스 가능
        # 레이아웃 강제: 래퍼/테이블이 남는 공간을 채우도록 설정
        try:
            wrapper = self.query_one("#db_table_wrap", Vertical)
            wrapper.styles.height = "1fr"
            # 최소 높이 0으로 설정하여 부모의 높이 분배를 방해하지 않도록 함
            wrapper.styles.min_height = 0
            wrapper.styles.margin = (0, 0, 0, 0)
            wrapper.styles.padding = (0, 0, 0, 0)
        except Exception:
            pass
        # 상단 행들을 고정 높이로 설정 (불필요한 공백 제거)
        try:
            sr = self.query_one("#db_search_row", Horizontal)
            br = self.query_one("#db_btn_row", Horizontal)
            sr.styles.height = 3
            sr.styles.min_height = 3
            sr.styles.margin = (0, 0, 0, 0)
            sr.styles.padding = (0, 0, 0, 0)
            br.styles.height = 3
            br.styles.min_height = 3
            br.styles.margin = (0, 0, 0, 0)
            br.styles.padding = (0, 0, 0, 0)
        except Exception:
            pass
        # table 스타일 설정 제거 - dock이 이벤트를 방해할 수 있음
        pass
        self.load_data()
        # 테이블에 포커스 설정
        table.focus()

    # --- helpers ---
    
    def load_data(self) -> None:
        jobs = self.db.get_jobs_filtered(search=self.search_query, status_filter=self.current_filter, limit=200)
        self._last_jobs_snapshot = jobs
        table = self.query_one("#jobs_table", DataTable)
        table.clear(columns=False)
        for job in jobs:
            title = job.get("title", "")
            url = job.get("url", "")
            # 제목은 30자까지만 표시
            title_disp = title[:30] + ("..." if len(title) > 30 else "")
            url_disp = url[:40] + ("..." if len(url) > 40 else "")
            size = self._format_size(job.get("file_size", 0))
            files_state = self._files_state(job)
            job_id = int(job.get("id", 0)) if job.get("id") is not None else 0
            table.add_row(
                str(job_id),
                title_disp,
                url_disp,
                job.get("engine", ""),
                job.get("status", ""),
                job.get("created_at", ""),
                job.get("completed_at", ""),
                size,
                files_state,
            )
    
    def action_refresh(self) -> None:
        self.load_data()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_button":
            self.app.pop_screen()
        elif event.button.id == "viewer_back":
            # 뷰어에서 목록으로 복귀 - 간단하게 화면 재구성
            self._close_viewer_and_restore_list()
        elif event.button.id == "viewer_delete":
            # 현재 열람 중인 항목 삭제 확인
            if self._current_view_job_id is None:
                self.show_error("선택된 항목이 없습니다")
                return
            self._confirm_mode = 'viewer'
            self._confirm_context = {"job_id": self._current_view_job_id}
            # 콘텐츠 영역 내부에 인라인 확인 바 표시
            self._show_confirm_dialog("현재 항목을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다. 관련 파일도 함께 삭제됩니다.")
        elif event.button.id == "delete_selected":
            self._delete_selected_rows()
        elif event.button.id == "delete_all":
            self._delete_all_rows()
        elif event.button.id == "confirm_delete_yes":
            mode = self._confirm_mode
            self._remove_confirm_dialog()
            if mode == 'selected':
                self._do_delete_selected()
            elif mode == 'all':
                self._do_delete_all()
            self._confirm_mode = None
        elif event.button.id == "confirm_delete_no":
            self._remove_confirm_dialog()
            self._confirm_mode = None
        elif event.button.id == "filter_all":
            self.current_filter = "all"
            self.load_data()
        elif event.button.id == "filter_completed":
            self.current_filter = "completed"
            self.load_data()
        elif event.button.id == "filter_running":
            self.current_filter = "running"
            self.load_data()
        elif event.button.id == "filter_failed":
            self.current_filter = "failed"
            self.load_data()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:  # type: ignore[override]
        # 행 하이라이트 시에는 뷰어를 열지 않음 - 클릭/선택 이벤트에서만 열기
        _ = event  # unused
        pass

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:  # type: ignore[override]
        # 셀 클릭 시 뷰어 열기 - coordinate.row 사용
        if self._viewer_open:
            return
        try:
            row_index = event.coordinate.row
            if self._debug:
                self.app.notify(f"Cell clicked at row {row_index}, opening viewer", severity="information")
            self._open_viewer_by_index(row_index)
            event.stop()  # 이벤트 전파 중지
        except Exception as e:
            import traceback
            self.show_error(f"뷰어 열기 오류: {e}\n{traceback.format_exc()}")

    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:  # type: ignore[override]
        # 셀 하이라이트 시에는 뷰어를 열지 않음 - 네비게이션만 허용
        _ = event  # unused
        pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:  # type: ignore[override]
        # Enter 키로 행 선택 시 뷰어 열기
        if self._viewer_open:
            return
        try:
            table = self.query_one("#jobs_table", DataTable)
            # cursor_row를 사용하여 현재 선택된 행 처리
            if table.cursor_row is not None and table.cursor_row >= 0:
                if self._debug:
                    self.app.notify(f"Opening viewer for row {table.cursor_row}", severity="information")
                self._open_viewer_by_index(table.cursor_row)
        except Exception as e:
            self.app.notify(f"Row selection error: {e}", severity="error")

    def _open_viewer_by_index(self, row_index: int) -> None:
        try:
            table = self.query_one("#jobs_table", DataTable)
            row = table.get_row_at(row_index)
            if not row:
                if self._debug:
                    self.app.notify(f"No row data at index {row_index}", severity="error")
                return
            job_id = int(row[0])
            if self._debug:
                self.app.notify(f"Found job_id {job_id}, opening viewer", severity="information")
            self._open_transcript_viewer(job_id)
        except Exception as e:
            import traceback
            if self._debug:
                self.app.notify(f"Error in _open_viewer_by_index: {e}", severity="error")
                self.show_error(f"Failed to open viewer: {traceback.format_exc()}")
    
    def _format_size(self, size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        s = float(size)
        i = 0
        while s >= 1024 and i < len(units) - 1:
            s /= 1024.0
            i += 1
        return f"{s:.1f}{units[i]}"

    def _files_state(self, job: dict) -> str:
        keys = ['download_path', 'transcript_path', 'srt_path', 'translation_path']
        exist = 0
        try:
            import os
            for k in keys:
                p = job.get(k)
                if p and os.path.exists(p):
                    exist += 1
        except Exception:
            pass
        return f"{exist}/{len(keys)}"

    def _selected_job_ids(self) -> list[int]:
        # 우선 다중 선택 세트가 있으면 그것을 사용
        if self._selected_ids:
            return list(self._selected_ids)
        ids: list[int] = []
        try:
            table = self.query_one("#jobs_table", DataTable)
            # 단일 선택 기준
            if table.cursor_row is not None and table.cursor_row >= 0:
                row = table.get_row_at(table.cursor_row)
                if row and len(row) > 0:
                    ids.append(int(row[0]))
        except Exception:
            pass
        return ids

    def _delete_selected_rows(self) -> None:
        ids = self._selected_job_ids()
        if not ids:
            self.show_error("선택된 항목이 없습니다.")
            return
        self._confirm_mode = 'selected'
        # 경고 알림 표시
        try:
            self.app.notify(f"선택한 {len(ids)}개 항목을 영구 삭제합니다", severity="warning")
        except Exception:
            pass
        self._show_confirm_dialog(f"[WARNING] 선택된 {len(ids)}개 항목을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다. 관련 파일도 함께 삭제됩니다.")

    def _delete_all_rows(self) -> None:
        self._confirm_mode = 'all'
        scope = {
            'all': '모든',
            'completed': '완료된',
            'running': '실행중인',
            'failed': '실패한'
        }.get(self.current_filter, '선택된')
        # 경고 알림 표시
        try:
            self.app.notify(f"{scope} 항목을 모두 영구 삭제합니다", severity="warning")
        except Exception:
            pass
        self._show_confirm_dialog(f"[WARNING] 현재 필터({scope})에 해당하는 모든 항목을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다. 관련 파일도 함께 삭제됩니다.")

    def action_delete_selected(self) -> None:
        self._delete_selected_rows()

    def action_delete_all(self) -> None:
        self._delete_all_rows()

    def _do_delete_selected(self) -> None:
        ids = self._selected_job_ids()
        removed = 0
        removed_files = 0
        for job_id in ids:
            result = self.db.delete_job(job_id, delete_files=True)
            removed += result.get("rows", 0)
            removed_files += result.get("files_removed", 0)
        self.show_success(f"Deleted {removed} record(s), files removed: {removed_files}")
        self.load_data()

    def _do_delete_all(self) -> None:
        result = self.db.delete_all_jobs(delete_files=True, status_filter=self.current_filter)
        self.show_success(f"Deleted {result.get('rows',0)} record(s), files removed: {result.get('files_removed',0)}")
        self.load_data()

    def _show_confirm_dialog(self, message: str) -> None:
        """DB 화면 내에 인라인 확인 바를 표시"""
        try:
            container = self.query_one(".db-container", Vertical)
            # 기존 확인 바 제거 후 재생성
            self._remove_confirm_dialog()
            confirm_bar = Vertical(classes="confirmation-dialog", id="confirm_delete_dialog")
            # 1) 부모 먼저 mount
            container.mount(confirm_bar)
            # 2) 그 다음 자식들 mount
            confirm_bar.mount(Static(message))
            btns = Horizontal(classes="dialog-buttons")
            confirm_bar.mount(btns)
            btns.mount(Button("Yes", id="confirm_delete_yes", classes="flat-danger"))
            btns.mount(Button("No", id="confirm_delete_no", classes="flat-button"))
        except Exception as e:
            try:
                self.show_error(f"확인 바 표시 오류: {e}")
            except Exception:
                pass
    
    def _close_viewer_and_restore_list(self) -> None:
        """뷰어 닫고 목록 화면으로 복귀"""
        try:
            self._viewer_open = False
            container = self.query_one(".db-container", Vertical)
            container.remove_children()
            
            # 원래 UI 재구성
            container.mount(Static("[DB] Database", classes="screen-title"))
            
            # 버튼 행 - 먼저 mount 후 자식 추가
            btn_row = Horizontal(id="db_btn_row")
            container.mount(btn_row)
            btn_row.mount(Button("Back", id="back_button", classes="action-button"))
            btn_row.mount(Button("Delete Selected", id="delete_selected", classes="warning-button"))
            btn_row.mount(Button("Delete All", id="delete_all", classes="danger-button"))
            btn_row.mount(Button("All", id="filter_all", classes="utility-button"))
            btn_row.mount(Button("Completed", id="filter_completed", classes="utility-button"))
            btn_row.mount(Button("Running", id="filter_running", classes="utility-button"))
            btn_row.mount(Button("Failed", id="filter_failed", classes="utility-button"))
            
            # 테이블 래퍼 - 먼저 mount 후 자식 추가
            table_wrap = Vertical(id="db_table_wrap")
            container.mount(table_wrap)
            table = DataTable(id="jobs_table")
            table_wrap.mount(table)
            
            # 테이블 초기화
            table.clear(columns=True)
            table.add_columns("ID", "Title", "URL", "Engine", "Status", "Created", "Completed", "Size", "Files")
            table.cursor_type = "row"
            table.zebra_stripes = True
            table.show_cursor = True
            table.can_focus = True
            
            # 스타일 설정
            table_wrap.styles.height = "1fr"
            table_wrap.styles.min_height = 0
            btn_row.styles.height = 3
            btn_row.styles.min_height = 3
            
            # 데이터 로드
            self.load_data()
            table.focus()
            
            if self._debug:
                self.app.notify("Returned to database list", severity="information")
            
        except Exception as e:
            import traceback
            self.show_error(f"목록 복원 오류: {e}\n{traceback.format_exc()}")

    def _on_confirm_result(self, result: bool | None) -> None:
        try:
            if not result:
                self._confirm_mode = None
                return
            mode = self._confirm_mode
            self._confirm_mode = None
            if mode == 'selected':
                self._do_delete_selected()
            elif mode == 'all':
                self._do_delete_all()
            elif mode == 'viewer':
                try:
                    job_id = int((self._confirm_context or {}).get("job_id", 0)) if self._confirm_context else 0
                except Exception:
                    job_id = 0
                self._confirm_context = None
                if job_id <= 0:
                    self.show_error("잘못된 항목입니다")
                    return
                result_info = self.db.delete_job(job_id, delete_files=True)
                if result_info.get("rows", 0) > 0:
                    self.show_success(f"Deleted 1 record, files removed: {result_info.get('files_removed',0)}")
                else:
                    self.show_error("삭제할 항목을 찾지 못했습니다")
                self._close_viewer_and_restore_list()
        except Exception:
            pass

    def _remove_confirm_dialog(self) -> None:
        try:
            dialog = self.query_one("#confirm_delete_dialog", Vertical)
            dialog.remove()
        except Exception:
            pass
    
    def _toggle_row_by_index(self, row_index: int) -> None:
        try:
            table = self.query_one("#jobs_table", DataTable)
            row = table.get_row_at(row_index)
            if not row:
                return
            job_id = int(row[0])
            if job_id in self._selected_ids:
                self._selected_ids.remove(job_id)
                # 선택 표시가 별도 컬럼이 없으므로 토글만 유지
            else:
                self._selected_ids.add(job_id)
            try:
                table.update_row(row_index, row)
            except Exception:
                pass
        except Exception:
            pass

    # 제거: 마우스 다운 전역 핸들러(포커스 간섭 방지)
    
    def on_mouse_down(self, event: MouseDown) -> None:
        """마우스 다운 이벤트로 테이블 클릭 처리"""
        # 뷰어가 열려있으면 무시
        if self._viewer_open:
            return
        
        # DataTable의 cell_selected 이벤트가 처리하도록 전파
        # 이 메서드는 백업용으로만 유지
        
    def on_key(self, event: events.Key) -> None:
        # Space: 현재 커서 행 토글 (멀티선택 UX)
        if event.key == "space":
            try:
                table = self.query_one("#jobs_table", DataTable)
                if table.cursor_row is not None and table.cursor_row >= 0:
                    self._toggle_row_by_index(table.cursor_row)
                    return
            except Exception:
                pass
        elif event.key == "enter":
            # Enter로 현재 행 뷰어 열기
            try:
                table = self.query_one("#jobs_table", DataTable)
                if table.cursor_row is not None and table.cursor_row >= 0:
                    row = table.get_row_at(table.cursor_row)
                    if row:
                        job_id = int(row[0])
                        self._open_transcript_viewer(job_id)
                        return
            except Exception:
                pass
        # Cmd/Ctrl+Click은 Textual 기본 클릭 이벤트만 들어오므로
        # on_data_table_cell_selected에서 동일 동작 처리
        super().on_key(event)

    # --- Transcript Viewer ---
    def _open_transcript_viewer(self, job_id: int) -> None:
        try:
            # 디버깅을 위한 로그
            if self._debug:
                self.app.notify(f"_open_transcript_viewer called with job_id {job_id}", severity="information")
            
            job = self.db.get_job_by_id(job_id)
            if not job:
                self.show_error(f"Job {job_id} not found in database")
                return
            
            if self._debug:
                self.app.notify(f"Job found: {job.get('title', 'No title')[:30]}", severity="information")
            # 파일 경로 결정
            orig_path = job.get("transcript_path") or job.get("translation_path")
            summary_path = None
            try:
                tp = job.get("transcript_path")
                if tp and tp.endswith(".txt"):
                    from pathlib import Path
                    p = Path(tp)
                    cand = p.with_name(f"{p.stem}_summary.txt")
                    if cand.exists():
                        summary_path = str(cand)
            except Exception:
                pass
            # 콘텐츠 읽기
            def _read_text(p: str | None, limit: int = 120000) -> str:
                if not p:
                    return ""
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = f.read(limit + 1)
                        if len(data) > limit:
                            data = data[:limit] + "\n... (truncated)"
                        return data
                except Exception:
                    return "(파일을 읽을 수 없습니다)"
            orig_text = _read_text(orig_path)
            summary_text = _read_text(summary_path)

            # 테이블 대신 뷰어 표시
            if self._debug:
                self.app.notify("Clearing container for viewer", severity="information")
            container = self.query_one(".db-container", Vertical)
            container.remove_children()
            if self._debug:
                self.app.notify("Container cleared", severity="information")
            
            # 제목과 정보 표시
            title = job.get("title", "제목 없음")
            container.mount(Static(f"[T] Transcript Viewer - {title[:50]}{'...' if len(title) > 50 else ''}", classes="screen-title"))
            # 버튼 바와 정보 표시
            if self._debug:
                self.app.notify("Mounting button bar", severity="information")
            btns = Horizontal(id="viewer_button_bar")
            # 먼저 컨테이너에 mount한 후에 자식 위젯 추가
            container.mount(btns)
            btns.mount(Button("[<] Back (b)", id="viewer_back", classes="action-button"))
            btns.mount(Button("Delete (d)", id="viewer_delete", classes="danger-button"))
            btns.mount(Static(f"Engine: {job.get('engine', 'N/A')} | Status: {job.get('status', 'N/A')}", classes="viewer-info"))
            btns.styles.height = 3
            btns.styles.min_height = 3
            if self._debug:
                self.app.notify("Button bar mounted", severity="information")
            # 본문 영역
            if summary_text:
                split = Horizontal()
                container.mount(split)
                try:
                    split.styles.height = "1fr"
                    split.styles.min_height = 0
                except Exception:
                    pass
                left = ScrollableContainer()
                right = ScrollableContainer()
                try:
                    left.styles.height = "1fr"; left.styles.min_height = 0
                    right.styles.height = "1fr"; right.styles.min_height = 0
                except Exception:
                    pass
                split.mount(left)
                split.mount(right)
                left.mount(Static("Original", classes="options-title"))
                left.mount(Static(orig_text or "(없음)", classes="output-text"))
                right.mount(Static("Summary", classes="options-title"))
                right.mount(Static(summary_text or "(없음)", classes="output-text"))
            else:
                sc = ScrollableContainer()
                try:
                    sc.styles.height = "1fr"; sc.styles.min_height = 0
                except Exception:
                    pass
                container.mount(sc)
                sc.mount(Static(orig_text or "(없음)", classes="output-text"))
            self._viewer_open = True
            self._current_view_job_id = job_id
            # 포커스를 백 버튼으로 설정
            try:
                back_btn = self.query_one("#viewer_back", Button)
                back_btn.focus()
            except Exception as e:
                if self._debug:
                    self.app.notify(f"Could not focus back button: {e}", severity="warning")
            
            if self._debug:
                self.app.notify("Transcript viewer opened successfully - Press Back button or ESC to return", severity="success")
        except Exception as e:
            import traceback
            error_msg = f"Viewer error: {e}\nTraceback:\n{traceback.format_exc()}"
            self.show_error(error_msg)
            if self._debug:
                self.app.notify(f"Failed to open viewer: {e}", severity="error")
            self._viewer_open = False

    def action_open_viewer(self) -> None:
        try:
            table = self.query_one("#jobs_table", DataTable)
            if table.cursor_row is None or table.cursor_row < 0:
                return
            row = table.get_row_at(table.cursor_row)
            if not row:
                return
            job_id = int(row[0])
            self._open_transcript_viewer(job_id)
        except Exception:
            pass
    
    def action_back_to_main(self) -> None:
        """키보드 단축키로 메인 메뉴로 돌아가기"""
        self.app.pop_screen()
    
    def action_filter_all(self) -> None:
        """키보드 단축키로 모든 항목 필터"""
        self.current_filter = "all"
        self.load_data()
    
    def action_filter_completed(self) -> None:
        """키보드 단축키로 완료된 항목 필터"""
        self.current_filter = "completed"
        self.load_data()
    
    def action_filter_running(self) -> None:
        """키보드 단축키로 실행 중인 항목 필터"""
        self.current_filter = "running"
        self.load_data()
    
    def action_filter_failed(self) -> None:
        """키보드 단축키로 실패한 항목 필터"""
        self.current_filter = "failed"
        self.load_data()


class ConfirmDialog(ModalScreen[bool]):
    """모달 확인 다이얼로그"""
    def __init__(self, message: str):
        super().__init__()
        self.message = message
    
    def compose(self) -> ComposeResult:  # type: ignore[override]
        with Vertical(classes="confirmation-dialog", id="confirm_modal"):
            yield Static(self.message)
            with Horizontal(classes="dialog-buttons"):
                yield Button("Yes", id="yes", variant="primary")
                yield Button("No", id="no", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "yes":
            self.dismiss(True)
        elif event.button.id == "no":
            self.dismiss(False)