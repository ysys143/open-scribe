"""백그라운드 작업 큐 관리 시스템"""

import threading
import queue
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess
import os

from ..database import TranscriptionDatabase
from ..config import Config


@dataclass
class TranscriptionJob:
    """전사 작업 정보"""
    job_id: int
    url: str
    title: str
    engine: str
    options: Dict[str, Any]
    priority: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class JobQueue:
    """백그라운드 작업 큐 관리자 (Singleton)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        config = Config()
        self.db = TranscriptionDatabase(config.DB_PATH)
        self.job_queue = queue.PriorityQueue()
        self.active_jobs: Dict[int, TranscriptionJob] = {}
        self.worker_threads: list = []
        self.max_concurrent_jobs = 3  # 동시 실행 작업 수
        self.shutdown_flag = threading.Event()
        self.status_lock = threading.Lock()
        
        # 자동 정리 설정
        self.auto_cleanup_enabled = True
        self.cleanup_after_minutes = 30  # 완료 후 30분 뒤 자동 삭제
        self.cleanup_thread = None
        
        # 워커 스레드 시작
        self._start_workers()
        
        # 기존 pending 작업들 큐에 복원
        self._restore_pending_jobs()
        
        # 자동 정리 스레드 시작
        self._start_cleanup_thread()
    
    def _start_workers(self):
        """워커 스레드 시작"""
        for i in range(self.max_concurrent_jobs):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"JobWorker-{i}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
    
    def _restore_pending_jobs(self):
        """DB에서 pending 상태 작업들 복원"""
        try:
            # pending/running 상태 작업들 가져오기
            pending_jobs = self.db.get_pending_jobs()
            
            for job_data in pending_jobs:
                job = TranscriptionJob(
                    job_id=job_data['id'],
                    url=job_data['url'],
                    title=job_data['title'],
                    engine=job_data['engine'],
                    options=job_data.get('options', {}),
                    priority=job_data.get('priority', 0)
                )
                
                # running 상태는 pending으로 변경
                if job_data['status'] == 'running':
                    self.db.update_job_status(job.job_id, 'pending')
                
                # 큐에 추가
                self.job_queue.put((-job.priority, job.created_at, job))
                
            if pending_jobs:
                print(f"[JobQueue] Restored {len(pending_jobs)} pending jobs")
                
        except Exception as e:
            print(f"[JobQueue] Error restoring pending jobs: {e}")
    
    def add_job(self, 
                url: str, 
                title: str, 
                engine: str,
                options: Optional[Dict[str, Any]] = None,
                priority: int = 0) -> int:
        """
        작업을 큐에 추가
        
        Args:
            url: YouTube URL
            title: 비디오 제목
            engine: 전사 엔진
            options: 추가 옵션
            priority: 우선순위 (높을수록 먼저 처리)
            
        Returns:
            job_id
        """
        # DB에 작업 생성
        job_id = self.db.create_job(
            url=url,
            title=title,
            engine=engine,
            status='pending',
            options=options
        )
        
        # 작업 객체 생성
        job = TranscriptionJob(
            job_id=job_id,
            url=url,
            title=title,
            engine=engine,
            options=options or {},
            priority=priority
        )
        
        # 우선순위 큐에 추가 (음수로 변환하여 높은 값이 먼저 처리되도록)
        self.job_queue.put((-priority, job.created_at, job))
        
        print(f"[JobQueue] Added job #{job_id}: {title[:50]}")
        return job_id
    
    def _worker_loop(self):
        """워커 스레드 메인 루프"""
        while not self.shutdown_flag.is_set():
            try:
                # 큐에서 작업 가져오기 (1초 타임아웃)
                priority, created_at, job = self.job_queue.get(timeout=1.0)
                
                # 활성 작업 등록
                with self.status_lock:
                    self.active_jobs[job.job_id] = job
                
                # 작업 실행
                self._execute_job(job)
                
                # 활성 작업에서 제거
                with self.status_lock:
                    if job.job_id in self.active_jobs:
                        del self.active_jobs[job.job_id]
                
                # 큐 작업 완료 표시
                self.job_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[JobQueue] Worker error: {e}")
    
    def _execute_job(self, job: TranscriptionJob):
        """
        작업 실행
        
        Args:
            job: 실행할 작업
        """
        print(f"[JobQueue] Starting job #{job.job_id}: {job.title[:50]}")
        
        # 상태를 running으로 업데이트
        self.db.update_job_status(job.job_id, 'running')
        self.db.update_job_field(job.job_id, 'started_at', datetime.now().isoformat())
        
        try:
            # main.py를 subprocess로 실행
            cmd = [
                'python', 'main.py',
                job.url,
                '--engine', job.engine
            ]
            
            # 옵션 추가
            if job.options.get('summary'):
                cmd.append('--summary')
            if job.options.get('verbose'):
                cmd.append('--verbose')
            if job.options.get('timestamp'):
                cmd.append('--timestamp')
            if job.options.get('translate'):
                cmd.append('--translate')
            if job.options.get('video'):
                cmd.append('--video')
            if job.options.get('srt'):
                cmd.append('--srt')
            
            # 환경 변수 설정
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # 실시간 출력
            
            # 프로세스 실행
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            # 진행률 모니터링
            self._monitor_process(process, job)
            
            # 프로세스 완료 대기
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # 성공
                self.db.update_job_status(job.job_id, 'completed')
                self.db.update_job_field(job.job_id, 'completed_at', datetime.now().isoformat())
                self.db.update_job_field(job.job_id, 'progress', 100)
                print(f"[JobQueue] Completed job #{job.job_id}")
            else:
                # 실패
                error_msg = stderr or "Unknown error"
                self.db.update_job_status(job.job_id, 'failed')
                self.db.update_job_field(job.job_id, 'error_message', error_msg)
                print(f"[JobQueue] Failed job #{job.job_id}: {error_msg}")
                
        except Exception as e:
            # 에러 처리
            self.db.update_job_status(job.job_id, 'failed')
            self.db.update_job_field(job.job_id, 'error_message', str(e))
            print(f"[JobQueue] Error executing job #{job.job_id}: {e}")
    
    def _monitor_process(self, process: subprocess.Popen, job: TranscriptionJob):
        """
        프로세스 출력 모니터링 및 진행률 업데이트
        
        Args:
            process: 실행 중인 프로세스
            job: 작업 정보
        """
        import re
        
        # 진행률 패턴들
        progress_patterns = [
            r'(\d+)%',  # 일반적인 퍼센트 표시
            r'Progress:\s*(\d+)',  # Progress: 숫자
            r'\[(\d+)/(\d+)\]',  # [현재/전체] 형식
            r'Chunk\s+(\d+)/(\d+)',  # Chunk 진행률
        ]
        
        # stdout 실시간 읽기
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
                
            # 진행률 추출
            for pattern in progress_patterns:
                match = re.search(pattern, line)
                if match:
                    if len(match.groups()) == 1:
                        # 퍼센트 직접 표시
                        progress = float(match.group(1))
                    elif len(match.groups()) == 2:
                        # 현재/전체 계산
                        current = float(match.group(1))
                        total = float(match.group(2))
                        if total > 0:
                            progress = (current / total) * 100
                        else:
                            progress = 0
                    else:
                        continue
                    
                    # DB 업데이트 (너무 자주 하지 않도록)
                    self.db.update_job_field(job.job_id, 'progress', min(progress, 99))
                    break
    
    def cancel_job(self, job_id: int) -> bool:
        """
        작업 취소
        
        Args:
            job_id: 취소할 작업 ID
            
        Returns:
            성공 여부
        """
        with self.status_lock:
            # 활성 작업인 경우
            if job_id in self.active_jobs:
                # TODO: 실행 중인 프로세스 종료
                self.db.update_job_status(job_id, 'cancelled')
                return True
            
            # 큐에서 제거 시도
            # PriorityQueue는 직접 제거가 어려우므로
            # 실행 시점에 cancelled 상태 확인으로 처리
            self.db.update_job_status(job_id, 'cancelled')
            return True
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        큐 상태 조회
        
        Returns:
            큐 상태 정보
        """
        with self.status_lock:
            return {
                'queue_size': self.job_queue.qsize(),
                'active_jobs': len(self.active_jobs),
                'max_concurrent': self.max_concurrent_jobs,
                'active_job_ids': list(self.active_jobs.keys())
            }
    
    def _start_cleanup_thread(self):
        """자동 정리 스레드 시작"""
        def cleanup_loop():
            """완료된 작업 자동 정리"""
            while not self.shutdown_flag.is_set():
                try:
                    # 30초마다 체크
                    time.sleep(30)
                    
                    if not self.auto_cleanup_enabled:
                        continue
                    
                    # 완료된 작업들 조회
                    completed_jobs = self.db.get_old_completed_jobs(self.cleanup_after_minutes)
                    
                    if completed_jobs:
                        print(f"[JobQueue] Auto-cleaning {len(completed_jobs)} old completed jobs")
                        for job in completed_jobs:
                            try:
                                # 파일도 함께 삭제
                                self.db.delete_job(job['id'], delete_files=True)
                            except Exception as e:
                                print(f"[JobQueue] Error deleting job {job['id']}: {e}")
                        
                        print(f"[JobQueue] Cleaned {len(completed_jobs)} old jobs")
                        
                except Exception as e:
                    print(f"[JobQueue] Cleanup thread error: {e}")
        
        self.cleanup_thread = threading.Thread(
            target=cleanup_loop,
            name="JobCleanup",
            daemon=True
        )
        self.cleanup_thread.start()
    
    def set_cleanup_timeout(self, minutes: int):
        """
        완료 후 자동 삭제 시간 설정
        
        Args:
            minutes: 완료 후 삭제까지 대기 시간 (분)
        """
        self.cleanup_after_minutes = minutes
        print(f"[JobQueue] Auto-cleanup timeout set to {minutes} minutes")
    
    def enable_auto_cleanup(self, enabled: bool = True):
        """
        자동 정리 기능 활성화/비활성화
        
        Args:
            enabled: 활성화 여부
        """
        self.auto_cleanup_enabled = enabled
        print(f"[JobQueue] Auto-cleanup {'enabled' if enabled else 'disabled'}")
    
    def shutdown(self):
        """큐 시스템 종료"""
        print("[JobQueue] Shutting down...")
        self.shutdown_flag.set()
        
        # 워커 스레드 종료 대기
        for worker in self.worker_threads:
            worker.join(timeout=5.0)
        
        # 정리 스레드 종료 대기
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=2.0)
        
        print("[JobQueue] Shutdown complete")


# 전역 큐 인스턴스
job_queue = JobQueue()