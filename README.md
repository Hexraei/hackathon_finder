# HackFind

**The Hackathon Discovery Platform** 🚀

Aggregating 1000+ hackathons from 15+ sources into one unified experience.

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11+-green" alt="Python">
  <img src="https://img.shields.io/badge/react-19-61dafb" alt="React">
  <img src="https://img.shields.io/badge/TiDB-Cloud-4A89DC" alt="TiDB">
  <img src="https://img.shields.io/badge/status-production-brightgreen" alt="Production">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">
</p>

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Changelog](#changelog)
- [Data Sources](#data-sources)
- [Architecture](#architecture)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Source Aggregation** | Devpost, Devfolio, Unstop, MLH, DoraHacks, Kaggle, and 9 more platforms |
| **AI Semantic Search** | Natural language queries powered by Gemini + ChromaDB |
| **TiDB Cloud** | Scalable MySQL-compatible cloud database for production |
| **GitHub Actions** | Automated scraping every 8 hours |
| **Smart Shortcuts** | `Ctrl+K` to search, `/` to focus, auto-fill suggestion chips |
| **Privacy-First** | No login required. Bookmarks stored locally. |
| **React Frontend** | Modern UI with Vite, Tailwind CSS v4, shadcn/ui |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/hackfind.git
cd hackfind
pip install -r requirements.txt
playwright install chromium

# Run scraper (local SQLite)
python scrape_all.py

# Run scraper (TiDB Cloud)
export USE_TIDB=true
export TIDB_HOST=... TIDB_PORT=4000 TIDB_USER=... TIDB_PASSWORD=... TIDB_DATABASE=...
python scrape_all.py

# Start backend
python server.py

# Start React dev server
cd ui-react && npm install && npm run dev
```

**Tech Stack:**
- **Frontend:** React 19, Vite, Tailwind CSS v4, shadcn/ui
- **Backend:** FastAPI, Python 3.11+
- **Database:** TiDB Cloud (prod) / SQLite (dev)

**Access Points:**
- React UI: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Changelog

### 1.0 "Production Ready" (2026-01-23)

**Cloud Infrastructure**
- **TiDB Cloud:** Migrated from SQLite to MySQL-compatible cloud database
- **GitHub Actions:** Automated scraper runs every 8 hours
- **SSL Support:** Secure connections to cloud database

**Configuration**
- Conditional DB selection via `USE_TIDB` environment variable
- Added `.env.example` with all required configuration
- Updated `requirements.txt` with PyMySQL, cryptography

---

### 0.7 "Clean UX" (2026-01-18)

**UX Improvements**
- Visited state tracking, share button, keyboard shortcuts
- Smart toggle filters (Solo/Team, Weekend/Weekday)
- AI suggestion chips, smooth animations

---

### 0.6.1 (2026-01-17)

**Scraper Improvements**
- **Maximized Limits**: Scrapers now fetch thousands of events deep (30 pages for Unstop/Devpost).
- **Quality Filter**: Implemented strict filtering to prevent saving "ended" events or those with past registration deadlines.
- **Kaggle Upgrade**: Detailed scraping via browser to extract exact deadlines, description, and team size.
- **Database Cleanup**: Automated removal of historical events to keep the database fresh.

**Refined defaults**
- Frontend defaults to Unstop, Devpost, Devfolio, and DevDisplay on load.

---

### 0.6.0 (2026-01-17)

**Tech Stack Migration**
- **Tailwind CSS v4**: completely replaced custom CSS with utility-first styling.
- **shadcn/ui**: Integrated accessible component library (Card, Button, Badge, etc.).
- **Vite + React 19**: Migrated from vanilla HTML/JS for better performance and modularity.

**Frontend Features**
- Created 12 modular components: Header, Hero, FilterBar, HackathonCard, etc.
- Implemented custom hooks: `useHackathons`, `useAISearch`, `useBookmarks`, `useScrollBehavior`
- Added paginated API loading for all 1347 hackathons (200 per page)

**UI Improvements**
- 4-column responsive grid layout (4/3/2/1 columns at breakpoints)
- Card footer with horizontal divider, View Details button, and star bookmark
- Bookmark active state changes only icon color (gold)
- Aligned source filter height with location input (36px)
- Added visible border to location input

**Bug Fixes**
- Fixed location parsing for stringified JSON objects
- Fixed card CSS class names (`card-*` to `bento-*`)

---

### 0.5.2 (2026-01-16)

**UI Layout**
- Split column filter layout: Pills/Sources (left), Search/Location/Sort (right)
- Sticky header on scroll-up with floating island effect
- Scroll-to-top button with hover effect

**Bug Fixes**
- Restored missing source filter functions
- Fixed CSS class mismatch for source panel expansion
- Removed duplicate event listener bindings

---

### 0.5.1 (2026-01-15)

**UI Revamp**
- AI search hero section with animated gradient border
- Thinking steps visual feedback during AI search
- AI reasons displayed on recommendation cards
- Inline search row layout

**AI Search v2**
- Gemini Flash integration for query parsing
- Extracts mode, tags, prize requirements, and location from natural language

---

### 0.5.0 (2026-01-14)

**Data Accuracy**
- MLH scraper overhaul for new Tailwind structure
- Deep enrichment via Devpost/Devfolio integrations
- Fixed Kaggle title truncation

**UI**
- Source logos on event cards
- Default sort by highest prize

---

### 0.4.x (2026-01-13 - 2026-01-14)

- Bento card design with calendar badge and source icons
- Flask to FastAPI migration with Swagger docs
- Unstop API integration for accurate data
- Hybrid search with reciprocal rank fusion

---

### 0.3.x (2026-01-12)

- Source filter with multi-select checkboxes
- Prize display improvements (TBD, non-cash, monetary)
- AI semantic search with ChromaDB + MiniLM
- 961 events vectorized

---

## Data Sources

| Platform | Method | Events (Est) |
|----------|--------|--------|
| Unstop | API | ~3000 |
| Devpost | Scraper | ~1500 |
| Devfolio | API | ~1000 |
| MLH | Scraper | ~170 |
| Kaggle | Scraper | ~120 |
| DoraHacks | Scraper | ~50 |
| DevDisplay| Browser| ~30 |
| Others | Various | ~100 |

---

## Architecture

```
hackfind/
├── scrapers/           # Platform-specific scrapers
├── database/           # SQLite + ChromaDB vector store
├── utils/              # Embeddings, parsing, helpers
├── ui/                 # Original vanilla HTML/CSS/JS
├── ui-react/           # React + Vite frontend
│   ├── src/components/ # 12 React components
│   ├── src/hooks/      # Custom hooks
│   ├── src/utils/      # API, formatters
│   └── src/styles/     # Global CSS
└── server.py           # FastAPI backend
```

---

## Roadmap

| Version | Focus |
|---------|-------|
| 0.7 | Production build, server integration |
| 0.8 | Mobile responsive polish |
| 0.9 | User accounts, saved searches |
| 1.0 | Team matchmaking, notifications |

---

## License

MIT © 2026 HackFind
