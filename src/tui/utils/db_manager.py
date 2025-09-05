"""데이터베이스 관리자"""

from typing import List, Dict, Any, Optional
from ...database import TranscriptionDatabase
from ...config import Config
import csv
from datetime import datetime, timedelta
from pathlib import Path


class DatabaseManager:
    """TUI 데이터베이스 관리자"""
    
    def __init__(self):
        self.db = TranscriptionDatabase(Config.DB_PATH)
    
    def get_jobs_filtered(self, search: str = "", status_filter: str = "all", 
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """필터링된 작업 목록 조회"""
        try:
            # 기존 database.py의 메서드를 확장하여 구현
            query = """
                SELECT id, url, title, engine, status, created_at, completed_at, 
                       output_dir, audio_file, video_file, transcript_file
                FROM transcription_jobs 
                WHERE 1=1
            """
            params = []
            
            # 검색 조건 추가
            if search:
                query += " AND (title LIKE ? OR url LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            # 상태 필터 추가
            if status_filter != "all":
                query += " AND status = ?"
                params.append(status_filter)
            
            # 정렬 및 제한
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = self.db.conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            
            jobs = []
            for row in cursor.fetchall():
                job_dict = dict(zip(columns, row))
                # 파일 크기 계산
                job_dict['file_size'] = self._calculate_file_size(job_dict)
                jobs.append(job_dict)
            
            return jobs
            
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 데이터 조회"""
        try:
            stats = {}
            
            # 총 작업 수
            cursor = self.db.conn.execute("SELECT COUNT(*) FROM transcription_jobs")
            stats['total_jobs'] = cursor.fetchone()[0]
            
            # 상태별 통계
            cursor = self.db.conn.execute("""
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
            cursor = self.db.conn.execute("""
                SELECT engine, COUNT(*) 
                FROM transcription_jobs 
                GROUP BY engine
            """)
            stats['engine_usage'] = dict(cursor.fetchall())
            
            # 최근 7일간 작업 수
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = self.db.conn.execute("""
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
            cursor = self.db.conn.execute("""
                DELETE FROM transcription_jobs 
                WHERE status = 'failed' 
                AND created_at < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            self.db.conn.commit()
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old jobs: {e}")
            return 0
    
    def _calculate_file_size(self, job: Dict[str, Any]) -> int:
        """작업 관련 파일들의 총 크기 계산"""
        total_size = 0
        
        for file_key in ['audio_file', 'video_file', 'transcript_file']:
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
            cursor = self.db.conn.execute("""
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