"""
TiDB Cloud Database Manager
===========================
Cloud-hosted MySQL-compatible database for production use.
Uses mysql-connector-python to connect to TiDB Serverless.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Import data normalizer for HackathonEvent
# Import data normalizer for HackathonEvent
try:
    from backend.utils.data_normalizer import HackathonEvent
except ImportError:
    try:
        from utils.data_normalizer import HackathonEvent
    except ImportError:
        from ..utils.data_normalizer import HackathonEvent


class TiDBManager:
    """
    TiDB Cloud database manager.
    API-compatible with DatabaseManager for easy switching.
    """
    
    def __init__(self):
        """Initialize TiDB connection using environment variables."""
        self.host = os.environ.get('TIDB_HOST')
        self.port = int(os.environ.get('TIDB_PORT', 4000))
        self.user = os.environ.get('TIDB_USER')
        self.password = os.environ.get('TIDB_PASSWORD')
        self.database = os.environ.get('TIDB_DATABASE', 'hackfind')
        
        # SSL certificate path (for TiDB Serverless)
        self.ssl_ca = os.environ.get('TIDB_SSL_CA', 'ca.pem')
        
        if not all([self.host, self.user, self.password]):
            raise ValueError("Missing TiDB connection environment variables (TIDB_HOST, TIDB_USER, TIDB_PASSWORD)")
        
        self._init_database()
        logger.info(f"TiDB connected to {self.host}:{self.port}/{self.database}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            ssl_ca=self.ssl_ca if os.path.exists(self.ssl_ca) else None,
            ssl_verify_cert=True if os.path.exists(self.ssl_ca) else False,
            autocommit=True
        )
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id VARCHAR(255) PRIMARY KEY,
                    source VARCHAR(100),
                    title TEXT,
                    url TEXT,
                    description TEXT,
                    start_date VARCHAR(20),
                    end_date VARCHAR(20),
                    deadline VARCHAR(20),
                    location TEXT,
                    mode VARCHAR(50),
                    prize_pool VARCHAR(255),
                    prize_pool_numeric DECIMAL(15, 2),
                    tags JSON,
                    organizer VARCHAR(255),
                    image_url TEXT,
                    team_size_min INT,
                    team_size_max INT,
                    participants_count INT,
                    status VARCHAR(50),
                    scraped_at DATETIME,
                    last_updated DATETIME,
                    INDEX idx_source (source),
                    INDEX idx_status (status),
                    INDEX idx_start_date (start_date),
                    INDEX idx_prize (prize_pool_numeric)
                )
            """)
            
            # Scrape metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_metadata (
                    source VARCHAR(100) PRIMARY KEY,
                    last_scraped DATETIME,
                    event_count INT,
                    success BOOLEAN,
                    error_message TEXT
                )
            """)
            
            cursor.close()
    
    def save_event(self, event: HackathonEvent) -> bool:
        """Save or update a single event."""
        # Skip ended events
        if event.status == 'ended':
            return False
        
        # Skip past deadlines
        if event.deadline:
            try:
                deadline = datetime.strptime(event.deadline[:10], "%Y-%m-%d").date()
                if deadline < datetime.now().date():
                    return False
            except:
                pass
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            tags_json = json.dumps(event.tags) if event.tags else '[]'
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO events (
                    id, source, title, url, description, start_date, end_date,
                    deadline, location, mode, prize_pool, prize_pool_numeric,
                    tags, organizer, image_url, team_size_min, team_size_max,
                    participants_count, status, scraped_at, last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    url = VALUES(url),
                    description = VALUES(description),
                    start_date = VALUES(start_date),
                    end_date = VALUES(end_date),
                    deadline = VALUES(deadline),
                    location = VALUES(location),
                    mode = VALUES(mode),
                    prize_pool = VALUES(prize_pool),
                    prize_pool_numeric = VALUES(prize_pool_numeric),
                    tags = VALUES(tags),
                    organizer = VALUES(organizer),
                    image_url = VALUES(image_url),
                    team_size_min = VALUES(team_size_min),
                    team_size_max = VALUES(team_size_max),
                    participants_count = VALUES(participants_count),
                    status = VALUES(status),
                    last_updated = VALUES(last_updated)
            """, (
                event.id, event.source, event.title, event.url, event.description,
                event.start_date, event.end_date, event.deadline, event.location,
                event.mode, event.prize_pool, event.prize_pool_numeric,
                tags_json, event.organizer, event.image_url,
                event.team_size_min, event.team_size_max, event.participants_count,
                event.status, now, now
            ))
            
            cursor.close()
            return True
    
    def save_events(self, events: List[HackathonEvent], source: str) -> int:
        """Save multiple events from a source."""
        saved = 0
        for event in events:
            if self.save_event(event):
                saved += 1
        
        # Update metadata
        self.update_scrape_metadata(source, saved, True)
        return saved
    
    def query_events(
        self,
        search: str = "",
        source: Optional[str] = None,
        sources: Optional[List[str]] = None,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_prize: Optional[float] = None,
        sort_by: str = "start_date",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[HackathonEvent], int]:
        """Query events with filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            conditions = []
            params = []
            
            if search:
                conditions.append("(title LIKE %s OR description LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            if source:
                conditions.append("source = %s")
                params.append(source)
            
            if sources:
                placeholders = ",".join(["%s"] * len(sources))
                conditions.append(f"source IN ({placeholders})")
                params.extend(sources)
            
            if mode:
                conditions.append("mode = %s")
                params.append(mode)
            
            if status:
                conditions.append("status = %s")
                params.append(status)
            
            if min_prize:
                conditions.append("prize_pool_numeric >= %s")
                params.append(min_prize)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Count total
            cursor.execute(f"SELECT COUNT(*) as cnt FROM events WHERE {where_clause}", params)
            total = cursor.fetchone()['cnt']
            
            # Sort
            sort_column = {
                "start_date": "start_date",
                "prize": "prize_pool_numeric",
                "latest": "scraped_at"
            }.get(sort_by, "start_date")
            
            order = "DESC" if sort_order.lower() == "desc" or sort_by == "prize" else "ASC"
            
            # Fetch page
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT * FROM events 
                WHERE {where_clause}
                ORDER BY {sort_column} {order}
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            
            rows = cursor.fetchall()
            events = [self._row_to_event(row) for row in rows]
            
            cursor.close()
            return events, total
    
    def get_all_sources(self) -> List[Dict]:
        """Get all sources with counts."""
        with self._get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM events 
                GROUP BY source 
                ORDER BY count DESC
            """)
            result = cursor.fetchall()
            cursor.close()
            return result
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Total events
            cursor.execute("SELECT COUNT(*) as total FROM events")
            total = cursor.fetchone()['total']
            
            # By source
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM events 
                GROUP BY source 
                ORDER BY count DESC
            """)
            by_source = {row['source']: row['count'] for row in cursor.fetchall()}
            
            # By status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM events 
                GROUP BY status
            """)
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            cursor.close()
            
            return {
                "total_events": total,
                "by_source": by_source,
                "by_status": by_status,
                "database": "TiDB Cloud"
            }
    
    def update_scrape_metadata(self, source: str, event_count: int, success: bool, error_message: str = None):
        """Update scraping metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO scrape_metadata (source, last_scraped, event_count, success, error_message)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    last_scraped = VALUES(last_scraped),
                    event_count = VALUES(event_count),
                    success = VALUES(success),
                    error_message = VALUES(error_message)
            """, (source, now, event_count, success, error_message))
            
            cursor.close()
    
    def delete_old_events(self, days: int = 90) -> int:
        """Delete events that ended more than X days ago."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - __import__('datetime').timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute("DELETE FROM events WHERE end_date < %s AND end_date IS NOT NULL", (cutoff,))
            deleted = cursor.rowcount
            cursor.close()
            
            logger.info(f"Deleted {deleted} old events (ended before {cutoff})")
            return deleted
    
    def _row_to_event(self, row: Dict) -> HackathonEvent:
        """Convert database row to HackathonEvent."""
        tags = row.get('tags')
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        
        return HackathonEvent(
            id=row['id'],
            source=row['source'],
            title=row['title'],
            url=row['url'],
            description=row.get('description'),
            start_date=row.get('start_date'),
            end_date=row.get('end_date'),
            deadline=row.get('deadline'),
            location=row.get('location'),
            mode=row.get('mode'),
            prize_pool=row.get('prize_pool'),
            prize_pool_numeric=float(row['prize_pool_numeric']) if row.get('prize_pool_numeric') else None,
            tags=tags or [],
            organizer=row.get('organizer'),
            image_url=row.get('image_url'),
            team_size_min=row.get('team_size_min'),
            team_size_max=row.get('team_size_max'),
            participants_count=row.get('participants_count'),
            status=row.get('status'),
            scraped_at=row.get('scraped_at'),
            last_updated=row.get('last_updated')
        )


# Factory function to get the right database manager
def get_database_manager():
    """
    Returns TiDBManager if USE_TIDB is set, otherwise DatabaseManager.
    """
    if os.environ.get('USE_TIDB', '').lower() == 'true':
        return TiDBManager()
    else:
        from .db_manager import DatabaseManager
        # Adjust path to be relative to project root if needed, or let it be
        # If we use relative path, we assume CWD is project root
        return DatabaseManager('hackathons.db')
