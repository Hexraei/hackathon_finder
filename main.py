"""
HackFind - Hackathon Aggregator
===============================
Main entry point for the hackathon aggregation system.

Usage:
    python main.py scrape                    # Scrape all sites
    python main.py scrape --site mlh         # Scrape single site
    python main.py scrape --tier tier_1      # Scrape high-priority sites
    python main.py search "AI hackathons"    # Search cached data
    python main.py stats                     # Show database statistics
    python main.py serve                     # Start web UI (coming soon)
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HackFind:
    """
    Main application class for HackFind.
    Orchestrates scraping, caching, and querying.
    """
    
    def __init__(self, config_path: str = "config/websites.json"):
        self.config_path = Path(config_path)
        self.db = None
        self.normalizer = None
        self._initialize()
    
    def _initialize(self):
        """Initialize components."""
        from backend.database.tidb_manager import get_database_manager
        from backend.utils.data_normalizer import DataNormalizer
        
        self.db = get_database_manager()  # Auto-selects TiDB or SQLite
        self.normalizer = DataNormalizer()
        
        # Load config for site list
        with open(self.config_path, 'r') as f:
            self.config = __import__('json').load(f)
        
        logger.info("HackFind initialized")
    
    def scrape_site(self, site_key: str, force: bool = False) -> int:
        """
        Scrape a single site using scrape_all module.
        
        Args:
            site_key: Key from websites.json (e.g., "mlh", "devpost")
            force: Force refresh even if cache is fresh
            
        Returns:
            Number of events scraped
        """
        logger.info(f"Scraping {site_key}...")
        
        # Map site keys to scrape_all functions
        from scraper.scrape_all import (
            scrape_devpost, scrape_devfolio, scrape_unstop, scrape_mlh,
            scrape_dorahacks, scrape_hackerearth, scrape_kaggle, scrape_devdisplay,
            scrape_techgig, scrape_geeksforgeeks, scrape_hackquest, scrape_mycareernet,
            scrape_hackculture, scrape_superteam
        )
        
        scrapers = {
            'devpost': scrape_devpost,
            'devfolio': scrape_devfolio,
            'unstop': scrape_unstop,
            'mlh': scrape_mlh,
            'dorahacks': scrape_dorahacks,
            'hackerearth': scrape_hackerearth,
            'kaggle': scrape_kaggle,
            'devdisplay': scrape_devdisplay,
            'techgig': scrape_techgig,
            'geeksforgeeks': scrape_geeksforgeeks,
            'hackquest': scrape_hackquest,
            'mycareernet': scrape_mycareernet,
            'hackculture': scrape_hackculture,
            'superteam': scrape_superteam
        }
        
        try:
            if site_key in scrapers:
                count = scrapers[site_key]()
                logger.info(f"✓ {site_key}: {count} events")
                return count if count else 0
            else:
                logger.error(f"Unknown site: {site_key}")
                return 0
        except Exception as e:
            logger.error(f"✗ {site_key}: {e}")
            return 0
    
    def scrape_all(self, tier: Optional[str] = None, force: bool = False) -> dict:
        """
        Scrape all configured sites using scrape_all.main().
        
        Args:
            tier: Optional tier filter (ignored - uses scrape_all.main)
            force: Force refresh (ignored)
            
        Returns:
            Dict with results
        """
        from scraper.scrape_all import main as scrape_main
        
        logger.info("Running full scrape via scrape_all.py...")
        scrape_main()
        
        # Return stats
        stats = self.db.get_statistics()
        return {'total': stats.get('total_events', 0)}
    
    def search(
        self,
        query: str = "",
        source: Optional[str] = None,
        mode: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple:
        """
        Search cached hackathons.
        
        Args:
            query: Search query
            source: Filter by source
            mode: Filter by mode (online, in-person, hybrid)
            tags: Filter by tags
            page: Page number
            page_size: Results per page
            
        Returns:
            Tuple of (events, total_count)
        """
        events, total = self.db.query_events(
            search=query if query else None,
            source=source,
            mode=mode,
            tags=tags,
            page=page,
            page_size=page_size
        )
        
        return events, total
    
    def get_statistics(self) -> dict:
        """Get database statistics."""
        return self.db.get_statistics()
    
    def get_stale_sources(self, max_age_hours: int = 6) -> List[str]:
        """Get sources that need refreshing."""
        return self.db.get_stale_sources(max_age_hours)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HackFind - Hackathon Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py scrape                    # Scrape all sites
    python main.py scrape --site mlh         # Scrape single site
    python main.py scrape --tier tier_1_high_value
    python main.py search "AI hackathons"
    python main.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape hackathon sites')
    scrape_parser.add_argument('--site', '-s', help='Specific site to scrape')
    scrape_parser.add_argument('--tier', '-t', help='Tier to scrape (tier_1_high_value, tier_2_medium, tier_3_low)')
    scrape_parser.add_argument('--force', '-f', action='store_true', help='Force refresh')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search hackathons')
    search_parser.add_argument('query', nargs='?', default='', help='Search query')
    search_parser.add_argument('--source', help='Filter by source')
    search_parser.add_argument('--mode', help='Filter by mode (online, in-person, hybrid)')
    search_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    search_parser.add_argument('--page', type=int, default=1, help='Page number')
    search_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available sites')
    
    # Stale command
    stale_parser = subparsers.add_parser('stale', help='List sites needing refresh')
    stale_parser.add_argument('--hours', type=int, default=6, help='Max age in hours')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize
    app = HackFind()
    
    # Execute command
    if args.command == 'scrape':
        if args.site:
            app.scrape_site(args.site, args.force)
        else:
            app.scrape_all(args.tier, args.force)
    
    elif args.command == 'search':
        events, total = app.search(
            query=args.query,
            source=args.source,
            mode=args.mode,
            tags=args.tags,
            page=args.page
        )
        
        if args.json:
            print(json.dumps([e.to_dict() for e in events], indent=2))
        else:
            print(f"\nFound {total} hackathons (showing page {args.page}):\n")
            for event in events:
                print(f"  [{event.source}] {event.title}")
                if event.start_date:
                    print(f"    📅 {event.start_date}")
                if event.location:
                    print(f"    📍 {event.location}")
                if event.prize_pool:
                    print(f"    💰 {event.prize_pool}")
                if event.url:
                    print(f"    🔗 {event.url}")
                print()
    
    elif args.command == 'stats':
        stats = app.get_statistics()
        print("\n📊 Database Statistics:")
        print(f"  Total events: {stats['total_events']}")
        print(f"\n  By status:")
        for status, count in stats.get('by_status', {}).items():
            print(f"    {status}: {count}")
        print(f"\n  By source:")
        for source, count in list(stats.get('by_source', {}).items())[:10]:
            print(f"    {source}: {count}")
        print(f"\n  By mode:")
        for mode, count in stats.get('by_mode', {}).items():
            print(f"    {mode}: {count}")
    
    elif args.command == 'list':
        print("\n📋 Available sites:")
        for key in app.factory.available_sites:
            config = app.factory.config['websites'][key]
            print(f"  • {key}: {config['name']} [{config['difficulty']}]")
        print(f"\n🎯 Priority tiers:")
        for tier, sites in app.factory.priority_tiers.items():
            print(f"  {tier}: {', '.join(sites)}")
    
    elif args.command == 'stale':
        stale = app.get_stale_sources(args.hours)
        if stale:
            print(f"\n⏰ Sources needing refresh (>{args.hours}h old):")
            for source in stale:
                print(f"  • {source}")
        else:
            print(f"\n✓ All sources are fresh (<{args.hours}h old)")


if __name__ == "__main__":
    main()
