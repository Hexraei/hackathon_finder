import sqlite3
import os

DB_PATH = 'hackathons.db'

def analyze_quality():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {os.path.abspath(DB_PATH)}")
        return

    print(f"Database found at {os.path.abspath(DB_PATH)}")
    print(f"Size: {os.path.getsize(DB_PATH)} bytes")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM events")
        count = cursor.fetchone()[0]
        print(f"Total events in DB: {count}")
        
        if count == 0:
            return

        cursor.execute("SELECT source, count(*) as cnt FROM events GROUP BY source")
        sources = cursor.fetchall()
        print("\nBreakdown by Source:")
        for row in sources:
            print(f"  {row['source']}: {row['cnt']}")

        print("\nQuality Check:")
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()
        
        print("\nQuality Check (Missing Dates/Prizes):")
        for row in events:
            src = row['source']
            if src in ['Devpost', 'Devfolio', 'HackQuest', 'TechGig', 'MyCareerNet', 'DevDisplay', 'HackerEarth']:
                has_date = bool(row['start_date'] or row['end_date'])
                prize = row['prize_pool']
                has_prize = bool(prize and prize != '0')
                
                if not has_date:
                    print(f"  [{src}] Missing Date: {row['title'][:40]}...")
                # Ignore prize for now, focus on date


    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_quality()
