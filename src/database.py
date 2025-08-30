"""
Database operations for Open-Scribe
Handles SQLite database for tracking transcription jobs
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

class TranscriptionDatabase:
    """Manage transcription job database"""
    
    def __init__(self, db_path: Path):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create jobs table with detailed progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcription_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                engine TEXT NOT NULL,
                status TEXT NOT NULL,
                download_completed BOOLEAN DEFAULT 0,
                download_path TEXT,
                transcription_completed BOOLEAN DEFAULT 0,
                transcript_path TEXT,
                summary_completed BOOLEAN DEFAULT 0,
                summary TEXT,
                srt_completed BOOLEAN DEFAULT 0,
                srt_path TEXT,
                translation_completed BOOLEAN DEFAULT 0,
                translation_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(video_id, engine)
            )
        ''')
        
        # Migrate existing database if needed
        cursor.execute("PRAGMA table_info(transcription_jobs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add new columns if they don't exist (for migration)
        new_columns = [
            ("download_completed", "BOOLEAN DEFAULT 0"),
            ("download_path", "TEXT"),
            ("transcription_completed", "BOOLEAN DEFAULT 0"),
            ("summary_completed", "BOOLEAN DEFAULT 0"),
            ("srt_completed", "BOOLEAN DEFAULT 0"),
            ("srt_path", "TEXT"),
            ("translation_completed", "BOOLEAN DEFAULT 0"),
            ("translation_path", "TEXT"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE transcription_jobs ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass  # Column might already exist
        
        conn.commit()
        conn.close()
    
    def create_job(self, video_id: str, url: str, title: str, engine: str) -> int:
        """
        Create a new transcription job
        
        Args:
            video_id: YouTube video ID
            url: Video URL
            title: Video title
            engine: Transcription engine used
            
        Returns:
            int: Job ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO transcription_jobs 
            (video_id, url, title, engine, status, created_at)
            VALUES (?, ?, ?, ?, 'processing', ?)
        ''', (video_id, url, title, engine, datetime.now()))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return job_id
    
    def update_job_status(self, job_id: int, status: str, 
                         transcript_path: Optional[str] = None,
                         summary: Optional[str] = None):
        """
        Update job status
        
        Args:
            job_id: Job ID
            status: New status ('processing', 'completed', 'failed')
            transcript_path: Path to transcript file
            summary: Generated summary text
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if status == 'completed':
            cursor.execute('''
                UPDATE transcription_jobs 
                SET status = ?, transcript_path = ?, summary = ?, completed_at = ?
                WHERE id = ?
            ''', (status, transcript_path, summary, datetime.now(), job_id))
        else:
            cursor.execute('''
                UPDATE transcription_jobs 
                SET status = ?
                WHERE id = ?
            ''', (status, job_id))
        
        conn.commit()
        conn.close()
    
    def check_existing_job(self, video_id: str, engine: str) -> Optional[Dict[str, Any]]:
        """
        Check if a job already exists for video and engine
        
        Args:
            video_id: YouTube video ID
            engine: Transcription engine
            
        Returns:
            dict: Job details if exists, None otherwise
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transcription_jobs 
            WHERE video_id = ? AND engine = ? AND status = 'completed'
        ''', (video_id, engine))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_job_stats(self) -> Dict[str, int]:
        """
        Get statistics about transcription jobs
        
        Returns:
            dict: Statistics including total, completed, failed counts
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM transcription_jobs')
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transcription_jobs WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transcription_jobs WHERE status = 'failed'")
        failed = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'processing': total - completed - failed
        }
    
    def update_download_status(self, job_id: int, completed: bool, path: Optional[str] = None):
        """Update download completion status"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transcription_jobs 
            SET download_completed = ?, download_path = ?, updated_at = ?
            WHERE id = ?
        ''', (completed, path, datetime.now(), job_id))
        
        conn.commit()
        conn.close()
    
    def update_transcription_status(self, job_id: int, completed: bool, path: Optional[str] = None):
        """Update transcription completion status"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transcription_jobs 
            SET transcription_completed = ?, transcript_path = ?, updated_at = ?
            WHERE id = ?
        ''', (completed, path, datetime.now(), job_id))
        
        conn.commit()
        conn.close()
    
    def update_summary_status(self, job_id: int, completed: bool, text: Optional[str] = None):
        """Update summary completion status"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transcription_jobs 
            SET summary_completed = ?, summary = ?, updated_at = ?
            WHERE id = ?
        ''', (completed, text, datetime.now(), job_id))
        
        conn.commit()
        conn.close()
    
    def update_srt_status(self, job_id: int, completed: bool, path: Optional[str] = None):
        """Update SRT generation status"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transcription_jobs 
            SET srt_completed = ?, srt_path = ?, updated_at = ?
            WHERE id = ?
        ''', (completed, path, datetime.now(), job_id))
        
        conn.commit()
        conn.close()
    
    def update_translation_status(self, job_id: int, completed: bool, path: Optional[str] = None):
        """Update translation completion status"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transcription_jobs 
            SET translation_completed = ?, translation_path = ?, updated_at = ?
            WHERE id = ?
        ''', (completed, path, datetime.now(), job_id))
        
        conn.commit()
        conn.close()
    
    def get_job_progress(self, video_id: str, engine: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed progress for a job
        
        Args:
            video_id: YouTube video ID
            engine: Transcription engine
            
        Returns:
            dict: Job progress details if exists, None otherwise
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transcription_jobs 
            WHERE video_id = ? AND engine = ?
        ''', (video_id, engine))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None