"""
Crash database for persistence and deduplication
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from protocrash.core.types import CrashInfo
from protocrash.monitors.crash_bucketing import CrashBucket
class CrashDatabase:
    """SQLite-based crash database for persistence and querying"""
    def __init__(self, db_path: str = "crashes.db"):
        """
        Initialize crash database
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._init_database()
    def _init_database(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        # Crashes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crash_hash TEXT NOT NULL UNIQUE,
                bucket_id TEXT NOT NULL,
                crash_type TEXT NOT NULL,
                exploitability TEXT,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                count INTEGER DEFAULT 1,
                input_hash TEXT,
                input_size INTEGER,
                minimized_size INTEGER,
                stack_trace TEXT,
                stderr TEXT,
                signal_number INTEGER,
                exit_code INTEGER
            )
        """)
        # Crash inputs table (for storing actual inputs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crash_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crash_id INTEGER NOT NULL,
                input_data BLOB NOT NULL,
                is_minimized BOOLEAN DEFAULT 0,
                FOREIGN KEY (crash_id) REFERENCES crashes(id)
            )
        """)
        # Create indexes for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_crash_hash
            ON crashes(crash_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bucket
            ON crashes(bucket_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_crash_type
            ON crashes(crash_type)
        """)
        self.conn.commit()
    def add_crash(self, bucket: CrashBucket, crash_info: CrashInfo) -> int:
        """
        Add or update crash in database
        Args:
            bucket: Crash bucket
            crash_info: Crash information
        Returns:
            Crash ID
        """
        import hashlib
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        # Generate input hash
        input_hash = hashlib.sha256(crash_info.input_data or b"").hexdigest()[:16]
        # Check if crash already exists
        cursor.execute(
            "SELECT id, count FROM crashes WHERE crash_hash = ?",
            (bucket.crash_hash,)
        )
        row = cursor.fetchone()
        if row:
            # Update existing crash
            crash_id = row['id']
            new_count = row['count'] + 1
            cursor.execute("""
                UPDATE crashes
                SET last_seen = ?, count = ?
                WHERE id = ?
            """, (now, new_count, crash_id))
        else:
            # Insert new crash
            cursor.execute("""
                INSERT INTO crashes (
                    crash_hash, bucket_id, crash_type, exploitability,
                    first_seen, last_seen, count,
                    input_hash, input_size,
                    stack_trace, stderr, signal_number, exit_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bucket.crash_hash,
                bucket.bucket_id,
                bucket.crash_type,
                bucket.exploitability,
                now,
                now,
                1,
                input_hash,
                len(crash_info.input_data) if crash_info.input_data else 0,
                str(bucket.stack_trace) if bucket.stack_trace else None,
                crash_info.stderr.decode('utf-8', errors='ignore') if crash_info.stderr else None,
                crash_info.signal_number,
                crash_info.exit_code
            ))
            crash_id = cursor.lastrowid
            # Store input data
            if crash_info.input_data:
                cursor.execute("""
                    INSERT INTO crash_inputs (crash_id, input_data, is_minimized)
                    VALUES (?, ?, ?)
                """, (crash_id, crash_info.input_data, False))
        self.conn.commit()
        return crash_id
    def get_crash_by_hash(self, crash_hash: str) -> Optional[Dict]:
        """Get crash by hash"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM crashes WHERE crash_hash = ?", (crash_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None
    def get_crashes_by_bucket(self, bucket_id: str) -> List[Dict]:
        """Get all crashes in a bucket"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM crashes WHERE bucket_id = ? ORDER BY first_seen DESC",
            (bucket_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    def get_top_crashes(self, limit: int = 10) -> List[Dict]:
        """Get top crashes by count"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM crashes
            ORDER BY count DESC, last_seen DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        # Total crashes
        cursor.execute("SELECT COUNT(*) as total FROM crashes")
        total = cursor.fetchone()['total']
        # Total occurrences
        cursor.execute("SELECT SUM(count) as total_occurrences FROM crashes")
        total_occurrences = cursor.fetchone()['total_occurrences'] or 0
        # By crash type
        cursor.execute("""
            SELECT crash_type, COUNT(*) as count, SUM(count) as occurrences
            FROM crashes
            GROUP BY crash_type
        """)
        by_type = {row['crash_type']: {
            'unique': row['count'],
            'total': row['occurrences']
        } for row in cursor.fetchall()}
        # By exploitability
        cursor.execute("""
            SELECT exploitability, COUNT(*) as count
            FROM crashes
            GROUP BY exploitability
        """)
        by_exploitability = {row['exploitability']: row['count']
                            for row in cursor.fetchall()}
        return {
            'total_unique_crashes': total,
            'total_occurrences': total_occurrences,
            'by_type': by_type,
            'by_exploitability': by_exploitability
        }
    def export_to_json(self, output_path: str):
        """Export database to JSON"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM crashes")
        crashes = [dict(row) for row in cursor.fetchall()]
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'crashes': crashes
        }
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
