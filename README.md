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

---

## 🔮 Future Roadmap (V0.3+)

We aim to become the **"Google Flights/Airbnb for Hackathons"**.

### 📱 **Phase 2: Mobile App (The "HackFind App")**
*   **Tech Stack**: **Flutter** (Cross-platform iOS/Android).
*   **Core Feature**: "Magic Fill" – In-app browser with JS injection to auto-fill applications on external sites (Devpost, Unstop) using a stored user profile.
*   **Engagement**: Push notifications (FCM) for "New AI Hackathons" and "Registration Closing Soon".

### 🧠 **Phase 3: AI-Powered Search**
*   **Semantic Search**: "Find me a hackathon about saving the ocean" -> Matches "BlueTech Challenge".
*   **Tech**: **TiDB Serverless** (Vector Search) + **OpenAI Embeddings**.
*   **Winning Probability Index**: Algorithm to calculate "Win Chance" based on `(Prize Pool / Participants)`.

### ✈️ **Phase 4: Decision Intelligence Features**
1.  **"Track Prices" -> "Track Deadlines"**: Watch specific events for updates.
2.  **"Anywhere Search"**: "I'm free next weekend, show me remote hacks."
3.  **Team Matchmaking**: "Tinder for Hackers" – Match frontend devs with backend engineers.
4.  **Verified Organizers**: "Superhost" badges for organizers who pay out prizes reliably.

### ⚙️ **Infrastructure Upgrades**
- **Database**: Migrate SQLite to **TiDB Cloud** to support Mobile App + Web concurrent access.
- **Backend**: Migrate Flask to **FastAPI** for async performance.
- **Frontend**: Migrate Vanilla JS to **Next.js** for better SEO and UI components.
