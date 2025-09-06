"""데이터베이스 관리자"""

from typing import List, Dict, Any, Optional
from ...database import TranscriptionDatabase
from ...config import Config
import csv
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3


class DatabaseManager:
    """TUI 데이터베이스 관리자"""
    
    def __init__(self):
        self.db = TranscriptionDatabase(Config.DB_PATH)
    
    def get_jobs_filtered(self, search: str = "", status_filter: str = "all", 
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """필터링된 작업 목록 조회"""
        try:
            # 기존 database.py 스키마에 맞춰 조회
            query = """
                SELECT id, url, title, engine, status, created_at, completed_at,
                       download_path, transcript_path, srt_path, translation_path
                FROM transcription_jobs
                WHERE 1=1
            """
            params = []
            if search:
                query += " AND (title LIKE ? OR url LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if status_filter != "all":
                query += " AND status = ?"
                params.append(status_filter)
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            jobs: List[Dict[str, Any]] = []
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                cursor = conn.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    job = dict(zip(columns, row))
                    job['file_size'] = self._calculate_file_size(job)
                    jobs.append(job)
            return jobs
            
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []
    
    def get_job_statistics(self) -> Dict[str, int]:
        """작업 통계 조회"""
        try:
            stats = {
                'total': 0,
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            }
            
            query = """
                SELECT status, COUNT(*) as count
                FROM transcription_jobs
                GROUP BY status
            """
            
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                cursor = conn.execute(query)
                for row in cursor.fetchall():
                    status, count = row
                    if status in stats:
                        stats[status] = count
                    stats['total'] += count
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'total': 0, 'pending': 0, 'running': 0, 'completed': 0, 'failed': 0}
    
    def update_job_status(self, job_id: int, status: str) -> bool:
        """작업 상태 업데이트"""
        try:
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                conn.execute(
                    "UPDATE transcription_jobs SET status = ? WHERE id = ?",
                    (status, job_id)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error updating job status: {e}")
            return False
    
    def delete_jobs_by_status(self, statuses: List[str]) -> Dict[str, int]:
        """특정 상태의 작업들 삭제"""
        try:
            placeholders = ','.join('?' * len(statuses))
            query = f"""
                DELETE FROM transcription_jobs
                WHERE status IN ({placeholders})
            """
            
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                cursor = conn.execute(
                    f"SELECT COUNT(*) FROM transcription_jobs WHERE status IN ({placeholders})",
                    statuses
                )
                count = cursor.fetchone()[0]
                
                conn.execute(query, statuses)
                conn.commit()
                
            return {'rows': count, 'files_removed': 0}
            
        except Exception as e:
            print(f"Error deleting jobs: {e}")
            return {'rows': 0, 'files_removed': 0}
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 데이터 조회"""
        try:
            stats = {}
            
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                # 총 작업 수
                cursor = conn.execute("SELECT COUNT(*) FROM transcription_jobs")
                stats['total_jobs'] = cursor.fetchone()[0]
            
            # 상태별 통계
            cursor = conn.execute("""
                SELECT status, COUNT(*) 
                FROM transcription_jobs 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            stats['completed'] = status_counts.get('completed', 0)
            stats['failed'] = status_counts.get('failed', 0)
            stats['running'] = status_counts.get('running', 0)
            
            # 성공률 계산
            if stats['total_jobs'] > 0:
                stats['success_rate'] = (stats['completed'] / stats['total_jobs']) * 100
            else:
                stats['success_rate'] = 0
            
            # 엔진별 사용 현황
            cursor = conn.execute("""
                SELECT engine, COUNT(*) 
                FROM transcription_jobs 
                GROUP BY engine
            """)
            stats['engine_usage'] = dict(cursor.fetchall())
            
            # 최근 7일간 작업 수
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = conn.execute("""
                SELECT COUNT(*) 
                FROM transcription_jobs 
                WHERE created_at >= ?
            """, (week_ago,))
            stats['jobs_this_week'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def export_to_csv(self, search: str = "", status_filter: str = "all") -> str:
        """CSV 파일로 내보내기"""
        try:
            jobs = self.get_jobs_filtered(search, status_filter, limit=10000)
            
            # 내보내기 파일 경로
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Config.BASE_PATH / f"export_jobs_{timestamp}.csv"
            
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'title', 'url', 'engine', 'status', 
                             'created_at', 'completed_at', 'output_dir']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for job in jobs:
                    # CSV에 필요한 필드만 선택
                    csv_row = {field: job.get(field, '') for field in fieldnames}
                    writer.writerow(csv_row)
            
            return str(export_path)
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            raise
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """오래된 작업 정리"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 실패한 작업 중 오래된 것들을 삭제
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                cursor = conn.execute("""
                    DELETE FROM transcription_jobs 
                    WHERE status = 'failed' 
                    AND created_at < ?
                """, (cutoff_date,))
                deleted_count = cursor.rowcount
                conn.commit()
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old jobs: {e}")
            return 0
    
    def _calculate_file_size(self, job: Dict[str, Any]) -> int:
        """작업 관련 파일들의 총 크기 계산"""
        total_size = 0
        
        for file_key in ['download_path', 'transcript_path', 'srt_path', 'translation_path']:
            file_path = job.get(file_key)
            if file_path and Path(file_path).exists():
                total_size += Path(file_path).stat().st_size
        
        return total_size
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 작업 목록 조회"""
        return self.get_jobs_filtered(limit=limit, offset=0)
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """ID로 특정 작업 조회"""
        try:
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                cursor = conn.execute("""
                    SELECT * FROM transcription_jobs WHERE id = ?
                """, (job_id,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
            
        except Exception as e:
            print(f"Error fetching job {job_id}: {e}")
            return None

    def delete_job(self, job_id: int, delete_files: bool = True) -> Dict[str, int]:
        """특정 작업 삭제 및 파일 정리
        Returns: {"rows": int, "files_removed": int}
        """
        removed_files = 0
        try:
            job = self.get_job_by_id(job_id)
            if job and delete_files:
                removed_files = self._delete_files_for_job(job)
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                cursor = conn.execute("DELETE FROM transcription_jobs WHERE id = ?", (job_id,))
                rows = cursor.rowcount
                conn.commit()
            return {"rows": rows, "files_removed": removed_files}
        except Exception as e:
            print(f"Error deleting job {job_id}: {e}")
            return {"rows": 0, "files_removed": removed_files}

    def delete_all_jobs(self, delete_files: bool = True, status_filter: str = "all") -> Dict[str, int]:
        """전체(또는 필터된) 작업 삭제 및 파일 정리"""
        removed_files = 0
        removed_rows = 0
        try:
            # 먼저 대상 목록 조회하여 파일 삭제 수행
            jobs = self.get_jobs_filtered(status_filter=status_filter, limit=100000)
            if delete_files:
                for job in jobs:
                    removed_files += self._delete_files_for_job(job)
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                if status_filter == "all":
                    cursor = conn.execute("DELETE FROM transcription_jobs")
                else:
                    cursor = conn.execute("DELETE FROM transcription_jobs WHERE status = ?", (status_filter,))
                removed_rows = cursor.rowcount
                conn.commit()
            return {"rows": removed_rows, "files_removed": removed_files}
        except Exception as e:
            print(f"Error deleting all jobs: {e}")
            return {"rows": removed_rows, "files_removed": removed_files}

    def _delete_files_for_job(self, job: Dict[str, Any]) -> int:
        """작업에 연관된 파일들을 삭제하고 개수를 반환"""
        removed = 0
        file_keys = ['download_path', 'transcript_path', 'srt_path', 'translation_path']
        downloads_dir = Config.DOWNLOADS_PATH
        for key in file_keys:
            try:
                p = job.get(key)
                if not p:
                    continue
                path = Path(p)
                if path.is_dir():
                    # 안전을 위해 디렉토리는 무시
                    continue

                # 1) 주 파일 삭제
                if path.exists():
                    try:
                        path.unlink()
                        removed += 1
                    except Exception:
                        pass

                # 2) 파생 파일 후보 구성 및 삭제
                try:
                    stem = path.stem if path.suffix else path.name
                    parent = path.parent

                    derived_candidates = []
                    # 같은 stem의 기본 페어들
                    for ext in ['.txt', '.srt', '.ko.srt', '.ko.txt']:
                        derived_candidates.append(parent / f"{stem}{ext}")

                    # summary 파일: transcript 기반으로만 생성되니 여기서 함께 제거
                    # transcript_path가 있는 경우에 한해 *_summary.txt 추가
                    if key == 'transcript_path':
                        derived_candidates.append(parent / f"{stem}_summary.txt")

                    # 삭제 실행 (주 파일과 동일 파일은 제외)
                    for candidate in derived_candidates:
                        if candidate == path:
                            continue
                        if candidate.exists() and candidate.is_file():
                            try:
                                candidate.unlink()
                                removed += 1
                            except Exception:
                                pass

                    # 3) Downloads 에 복사된 파일들도 동일 파일명으로 정리
                    for candidate in derived_candidates + [path]:
                        dl = downloads_dir / candidate.name
                        if dl.exists() and dl.is_file():
                            try:
                                dl.unlink()
                                removed += 1
                            except Exception:
                                pass
                except Exception:
                    pass
            except Exception:
                # 개별 파일 삭제 실패는 계속 진행
                pass
        return removed