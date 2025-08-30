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
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcription_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                engine TEXT NOT NULL,
                status TEXT NOT NULL,
                transcript_path TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(video_id, engine)
            )
        ''')
        
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