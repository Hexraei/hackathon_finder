# HackFind - Hackathon Aggregator

A web application that aggregates hackathons from multiple sources into one unified platform.

## 📦 Version History

### **V0.2: Fixed Scraping Logic** (Current)
- **Consolidated Scraper**: Single entry point `scrape_all.py` combining API and Browser logic.
- **Improved Coverage**: Added Playwright support for dynamic sites (DoraHacks, TechGig, GeeksforGeeks, etc.).
- **Data Quality**: 
    - Fixed date parsing for **Devpost** and **Devfolio**.
    - Removed duplicate/broken files.

### **V0.1: Initial Commit**
- Basic Flask server.
- Initial scrapers (Devpost, Unstop).
- SQLite Database setup.

---

## 🛠️ Source Status (V0.2)

### ✅ Fully Operational
| Source | Method | Count | Notes |
|--------|--------|-------|-------|
| **Unstop** | API | 400 | High volume, robust. |
| **Devpost** | API+Regex | 200 | fixed date parsing. |
| **DevDisplay** | Browser | 70 | High quality, lazy loading handled. |
| **Devfolio** | API | 45 | Fixed ISO date parsing. |
| **MLH** | BS4 | 29 | Reliable. |
| **Superteam** | API | 26 | Reliable. |

### ⚠️ Working (Needs Monitoring)
| Source | Method | Count | Notes |
|--------|--------|-------|-------|
| **DoraHacks** | Browser | 24 | Successful browser scrape. |
| **MyCareerNet**| Browser | 16 | Fixed selector logic. |
| **TechGig** | Browser | 13 | Date parsing fixed. |
| **HackQuest** | Browser | 11 | Successful. |
| **GeeksforGeeks**| Browser | 6 | Successful. |
| **HackerEarth** | Browser | 1 | Low yield, strict bot protection. |

### ❌ Broken / Needs Fix
| Source | Method | Count | Issue |
|--------|--------|-------|-------|
| **HackCulture**| BS4 | 0 | Layout changed or bot block. |
| **Kaggle** | API | 0 | API endpoint might be changed/blocked. |
| **Contra** | API | 0 | API response changed/empty. |

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the consolidated scraper
python scrape_all.py

# Start the server
python server.py

# Open http://localhost:8001
```

## Project Structure

```
├── server.py           # Flask server
├── scrape_all.py       # Consolidated Scraper logic
├── ui/                 # Frontend files
├── database/           # SQLite database manager
├── utils/              # Data normalization logic
└── hackathons.db       # SQLite Database
```

## License

MIT
