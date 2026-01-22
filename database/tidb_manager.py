"""
TiDB Cloud Database Manager
===========================
MySQL-compatible database manager for TiDB Cloud Serverless.
Maintains the same API as DatabaseManager for drop-in replacement.
"""

import os
import json
import pymysql
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

# Import HackathonEvent
try:
    from utils.data_normalizer import HackathonEvent
except ImportError:
    from data_normalizer import HackathonEvent


class TiDBManager:
    """
    TiDB Cloud storage for hackathon events.
    MySQL-compatible replacement for DatabaseManager.
    """
    
    def __init__(self):
        """Initialize TiDB connection using environment variables."""
        self.config = {
            'host': os.environ.get('TIDB_HOST', 'localhost'),
            'port': int(os.environ.get('TIDB_PORT', 4000)),
            'user': os.environ.get('TIDB_USER', 'root'),
            'password': os.environ.get('TIDB_PASSWORD', ''),
            'database': os.environ.get('TIDB_DATABASE', 'test'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': False,
        }
        
        # SSL configuration for TiDB Cloud
        ssl_ca = os.environ.get('TIDB_SSL_CA')
        if ssl_ca and os.path.exists(ssl_ca):
            self.config['ssl'] = {'ca': ssl_ca}
        else:
            # TiDB Cloud requires SSL, use system CA if no custom cert
            self.config['ssl'] = {'ssl': True}
        
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = pymysql.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id VARCHAR(255) PRIMARY KEY,
                    source VARCHAR(100) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    url VARCHAR(1000) NOT NULL,
                    start_date VARCHAR(20),
                    end_date VARCHAR(20),
                    registration_deadline VARCHAR(20),
                    location VARCHAR(500),
                    mode VARCHAR(50),
                    description TEXT,
                    prize_pool VARCHAR(200),
                    prize_pool_numeric DECIMAL(15,2) DEFAULT 0,
                    image_url VARCHAR(1000),
                    logo_url VARCHAR(1000),
                    organizer VARCHAR(300),
                    participants_count INT,
                    team_size_min INT,
                    team_size_max INT,
                    status VARCHAR(50),
                    scraped_at VARCHAR(30),
                    last_updated VARCHAR(30),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_source (source),
                    INDEX idx_start_date (start_date),
                    INDEX idx_status (status),
                    INDEX idx_mode (mode),
                    INDEX idx_prize (prize_pool_numeric)
                )
            """)
            
            # Tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_tags (
                    event_id VARCHAR(255) NOT NULL,
                    tag VARCHAR(100) NOT NULL,
                    PRIMARY KEY (event_id, tag),
                    INDEX idx_tag (tag)
                )
            """)
            
            # Themes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_themes (
                    event_id VARCHAR(255) NOT NULL,
                    theme VARCHAR(100) NOT NULL,
                    PRIMARY KEY (event_id, theme)
                )
            """)
            
            # Scraping metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_metadata (
                    source VARCHAR(100) PRIMARY KEY,
                    last_scraped VARCHAR(30),
                    event_count INT DEFAULT 0,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            """)
    
    # ============ CRUD Operations ============
    
    def save_event(self, event: HackathonEvent) -> bool:
        """Save or update a single event."""
        # Filter out past events
        if event.status == 'ended':
            return False
            
        # Filter out events with past registration deadline
        if event.registration_deadline:
            try:
                reg_deadline = datetime.strptime(event.registration_deadline, "%Y-%m-%d").date()
                if reg_deadline < datetime.now().date():
                    return False
            except ValueError:
                pass

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Upsert event (MySQL ON DUPLICATE KEY UPDATE)
            cursor.execute("""
                INSERT INTO events (
                    id, source, title, url, start_date, end_date,
                    registration_deadline, location, mode, description,
                    prize_pool, prize_pool_numeric, image_url, logo_url,
                    organizer, participants_count, team_size_min, team_size_max,
                    status, scraped_at, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    source = VALUES(source),
                    title = VALUES(title),
                    url = VALUES(url),
                    start_date = VALUES(start_date),
                    end_date = VALUES(end_date),
                    registration_deadline = VALUES(registration_deadline),
                    location = VALUES(location),
                    mode = VALUES(mode),
                    description = VALUES(description),
                    prize_pool = VALUES(prize_pool),
                    prize_pool_numeric = VALUES(prize_pool_numeric),
                    image_url = VALUES(image_url),
                    logo_url = VALUES(logo_url),
                    organizer = VALUES(organizer),
                    participants_count = VALUES(participants_count),
                    team_size_min = VALUES(team_size_min),
                    team_size_max = VALUES(team_size_max),
                    status = VALUES(status),
                    scraped_at = VALUES(scraped_at),
                    last_updated = VALUES(last_updated)
            """, (
                event.id, event.source, event.title, event.url,
                event.start_date, event.end_date, event.registration_deadline,
                event.location, event.mode, event.description,
                event.prize_pool, event.prize_pool_numeric,
                event.image_url, event.logo_url, event.organizer,
                event.participants_count, event.team_size_min, event.team_size_max,
                event.status, event.scraped_at, event.last_updated
            ))
            
            # Update tags
            cursor.execute("DELETE FROM event_tags WHERE event_id = %s", (event.id,))
            for tag in event.tags:
                cursor.execute(
                    "INSERT IGNORE INTO event_tags (event_id, tag) VALUES (%s, %s)",
                    (event.id, tag)
                )
            
            # Update themes
            cursor.execute("DELETE FROM event_themes WHERE event_id = %s", (event.id,))
            for theme in event.themes:
                cursor.execute(
                    "INSERT IGNORE INTO event_themes (event_id, theme) VALUES (%s, %s)",
                    (event.id, theme)
                )
            
            return True
    
    def save_events(self, events: List[HackathonEvent], source: str) -> int:
        """Save multiple events from a source."""
        count = 0
        for event in events:
            if self.save_event(event):
                count += 1
        
        self.update_scrape_metadata(source, count, True)
        return count
    
    def get_event(self, event_id: str) -> Optional[HackathonEvent]:
        """Get a single event by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_event(row, cursor)
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            return cursor.rowcount > 0
    
    def delete_old_events(self, days: int = 90) -> int:
        """Delete events that ended more than X days ago."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM events WHERE end_date < %s OR (end_date IS NULL AND start_date < %s)",
                (cutoff, cutoff)
            )
            return cursor.rowcount
    
    # ============ Query Operations ============
    
    def query_events(
        self,
        search: Optional[str] = None,
        source: Optional[str] = None,
        sources: Optional[List[str]] = None,
        mode: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        start_after: Optional[str] = None,
        start_before: Optional[str] = None,
        min_prize: Optional[float] = None,
        sort_by: str = "start_date",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[HackathonEvent], int]:
        """Advanced query with filtering, sorting, and pagination."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            # Full-text search (MySQL LIKE pattern)
            if search:
                conditions.append("(title LIKE %s OR description LIKE %s OR location LIKE %s)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            # Source filter
            if source:
                conditions.append("source = %s")
                params.append(source)
            elif sources:
                placeholders = ",".join(["%s"] * len(sources))
                conditions.append(f"source IN ({placeholders})")
                params.extend(sources)
            
            # Mode filter
            if mode:
                conditions.append("mode = %s")
                params.append(mode)
            
            # Status filter
            if status:
                conditions.append("status = %s")
                params.append(status)
            
            # Date filters
            if start_after:
                conditions.append("start_date >= %s")
                params.append(start_after)
            if start_before:
                conditions.append("start_date <= %s")
                params.append(start_before)
            
            # Prize filter
            if min_prize is not None:
                conditions.append("prize_pool_numeric >= %s")
                params.append(min_prize)
            
            # Tags filter
            if tags:
                tag_placeholders = ",".join(["%s"] * len(tags))
                conditions.append(f"""
                    id IN (
                        SELECT event_id FROM event_tags
                        WHERE tag IN ({tag_placeholders})
                    )
                """)
                params.extend(tags)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Validate sort field
            valid_sort_fields = ["start_date", "prize_pool_numeric", "title", "scraped_at", "source"]
            if sort_by not in valid_sort_fields:
                sort_by = "start_date"
            
            sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
            
            # Get total count
            count_query = f"SELECT COUNT(*) as cnt FROM events WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['cnt']
            
            # Get paginated results
            offset = (page - 1) * page_size
            query = f"""
                SELECT * FROM events
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_direction}
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [page_size, offset])
            
            events = [self._row_to_event(row, cursor) for row in cursor.fetchall()]
            
            return events, total
    
    def get_all_tags(self) -> List[Tuple[str, int]]:
        """Get all unique tags with their counts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tag, COUNT(*) as count
                FROM event_tags
                GROUP BY tag
                ORDER BY count DESC
            """)
            return [(row['tag'], row['count']) for row in cursor.fetchall()]
    
    def get_all_sources(self) -> List[Tuple[str, int]]:
        """Get all sources with their event counts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM events
                GROUP BY source
                ORDER BY count DESC
            """)
            return [(row['source'], row['count']) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as cnt FROM events")
            total = cursor.fetchone()['cnt']
            
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM events GROUP BY status
            """)
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM events GROUP BY source
            """)
            by_source = {row['source']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute("""
                SELECT mode, COUNT(*) as count
                FROM events GROUP BY mode
            """)
            by_mode = {row['mode']: row['count'] for row in cursor.fetchall()}
            
            return {
                "total_events": total,
                "by_status": by_status,
                "by_source": by_source,
                "by_mode": by_mode
            }
    
    # ============ Cache Operations ============
    
    def is_cache_fresh(self, source: str, max_age_hours: int = 6) -> bool:
        """Check if cached data for a source is still fresh."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_scraped FROM scrape_metadata WHERE source = %s",
                (source,)
            )
            row = cursor.fetchone()
            
            if not row or not row['last_scraped']:
                return False
            
            last_scraped = datetime.fromisoformat(row['last_scraped'])
            age = datetime.now() - last_scraped
            
            return age.total_seconds() < max_age_hours * 3600
    
    def update_scrape_metadata(
        self,
        source: str,
        event_count: int,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Update scraping metadata for a source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scrape_metadata 
                (source, last_scraped, event_count, success, error_message)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    last_scraped = VALUES(last_scraped),
                    event_count = VALUES(event_count),
                    success = VALUES(success),
                    error_message = VALUES(error_message)
            """, (
                source,
                datetime.now().isoformat(),
                event_count,
                success,
                error_message
            ))
    
    def get_scrape_metadata(self, source: str) -> Optional[Dict]:
        """Get scraping metadata for a source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM scrape_metadata WHERE source = %s",
                (source,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_stale_sources(self, max_age_hours: int = 6) -> List[str]:
        """Get list of sources that need refreshing."""
        cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source FROM scrape_metadata
                WHERE last_scraped < %s OR last_scraped IS NULL
            """, (cutoff,))
            
            return [row['source'] for row in cursor.fetchall()]
    
    # ============ Helper Methods ============
    
    def _row_to_event(self, row: Dict, cursor) -> HackathonEvent:
        """Convert database row to HackathonEvent object."""
        # Get tags
        cursor.execute(
            "SELECT tag FROM event_tags WHERE event_id = %s",
            (row['id'],)
        )
        tags = [r['tag'] for r in cursor.fetchall()]
        
        # Get themes
        cursor.execute(
            "SELECT theme FROM event_themes WHERE event_id = %s",
            (row['id'],)
        )
        themes = [r['theme'] for r in cursor.fetchall()]
        
        return HackathonEvent(
            id=row['id'],
            source=row['source'],
            title=row['title'],
            url=row['url'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            registration_deadline=row['registration_deadline'],
            location=row['location'],
            mode=row['mode'],
            description=row['description'],
            prize_pool=row['prize_pool'],
            prize_pool_numeric=float(row['prize_pool_numeric'] or 0),
            tags=tags,
            themes=themes,
            image_url=row['image_url'],
            logo_url=row['logo_url'],
            organizer=row['organizer'],
            participants_count=row['participants_count'],
            team_size_min=row['team_size_min'],
            team_size_max=row['team_size_max'],
            status=row['status'],
            scraped_at=row['scraped_at'],
            last_updated=row['last_updated'],
        )


if __name__ == "__main__":
    # Test the TiDB manager
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    print("Testing TiDB connection...")
    db = TiDBManager()
    
    stats = db.get_statistics()
    print(f"✓ Connected! Stats: {stats}")
