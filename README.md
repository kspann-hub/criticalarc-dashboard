# CriticalArc Commissioning Dashboard — Aviation Template

A Streamlit dashboard for tracking commissioning progress on aviation projects. Pulls data from the CxAlloy API, syncs it to a local SQLite database, and renders interactive visualizations — loading in seconds instead of minutes.

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [Data Flow](#data-flow)
3. [Project Structure](#project-structure)
4. [File-by-File Breakdown](#file-by-file-breakdown)
5. [Setup](#setup)
6. [Running the Dashboard](#running-the-dashboard)
7. [Understanding the Data](#understanding-the-data)
8. [Dashboard Tabs & Analysis](#dashboard-tabs--analysis)
9. [Configuration](#configuration)
10. [Creating a New Project from This Template](#creating-a-new-project-from-this-template)
11. [Deploying to Streamlit Cloud](#deploying-to-streamlit-cloud)
12. [Troubleshooting](#troubleshooting)

---

## How It Works

The dashboard solves a core problem: the CxAlloy API can take several minutes to return data for large projects. Instead of making users wait on every page load, a background sync process pulls data on a schedule and stores it locally in SQLite. The dashboard reads from this local database, making page loads near-instant.

```
CxAlloy API → sync_logic.py → dashboard_data.db → cxalloy.py reads DB → cleaning.py → layout.py renders
```

The first time the app runs, data is pulled from the API and stored locally. Every subsequent page load reads from SQLite in milliseconds. The sync repeats every 12 hours to keep data fresh.

On Streamlit Cloud, a background thread handles the sync automatically. The database file is committed to the repo so the app has data immediately on deploy.

---

## Data Flow

### Step 1: Sync (sync_logic.py)

The sync process authenticates with CxAlloy using HMAC-SHA256 signatures, then pulls six datasets for each project:

| Endpoint | Method | Dataset | What It Contains |
|----------|--------|---------|------------------|
| `/project` | GET | Projects | Project list with IDs, names, status |
| `/issue` | POST | Issues | Deficiencies, punch list items, RFIs |
| `/checklist` | POST | Checklists | Pre-functional checklists by level |
| `/test` | POST | Tests | Functional performance tests |
| `/person` | GET | People | Team members assigned to the project |
| `/company` | GET | Companies | Contractor and subcontractor firms |
| `/equipment` | GET | Equipment | Mechanical/electrical units with attributes |

Each dataset is paginated (500 records per page). The sync fetches all pages, then writes results to SQLite. Nested JSON fields are serialized as JSON strings. If different projects have different columns, missing columns are automatically added to the table.

### Step 2: Read (utils/cxalloy.py)

`load_project_data()` checks if `dashboard_data.db` exists. If yes, reads from SQLite (milliseconds). If no, falls back to live API calls (minutes).

### Step 3: Clean (utils/cleaning.py)

`clean_all()` standardizes columns, flattens extended_status dates, resolves company lookups, calculates aging, and parses dates.

### Step 4: Filter (utils/filters.py)

Sidebar filters by discipline, status, contractor, and date range.

### Step 5: Render (layout.py)

Filtered data rendered as Plotly charts, KPI cards, and data tables across tabs.

---

## Project Structure

```
SMF-Dashboard.AVIATION-TEMPLATE/
│
├── app.py                   # Entry point — config, sidebar, CSS, launches everything
├── layout.py                # All visualizations — charts, KPIs, tables across tabs
├── config.py                # Project-specific settings (statuses, colors, pipeline)
│
├── sync_logic.py            # Core sync engine — API calls + SQLite writes
├── sync_job.py              # Local runner — calls sync_logic on a timer
├── background_sync.py       # Cloud runner — daemon thread for Streamlit Cloud
│
├── utils/
│   ├── cxalloy.py           # Data loader — reads SQLite or falls back to API
│   ├── cleaning.py          # Data transformation — standardize, flatten, resolve lookups
│   └── filters.py           # Sidebar filter application
│
├── .streamlit/
│   └── secrets.toml         # API credentials (NEVER commit this)
│
├── data/                    # CSV exports from inspect_data.py (for debugging)
├── dashboard_data.db        # SQLite database (auto-generated, committed to repo)
├── inspect_data.py          # Debug utility — dumps raw API data to CSVs
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

---

## File-by-File Breakdown

### app.py — The Entry Point

Handles page config, starts the background sync thread, loads the project list for the sidebar, renders filters, applies global CSS, and calls `layout.render()`. Run with: `streamlit run app.py`

### layout.py — All Visualizations

`render()` builds tabs with Plotly charts, KPI cards, and data tables. Each tab: extract data → compute metrics → render visuals.

### config.py — Project Configuration

Controls statuses, pipeline stages, and branding. First file to update for a new project.

### sync_logic.py — The Sync Engine

Shared logic for local and cloud sync: HMAC auth, paginated API calls, SQLite writes with automatic schema migration (adds missing columns when projects have different data shapes).

### sync_job.py — Local Sync Runner

Runs `sync_all()` immediately then repeats every 12 hours via APScheduler.

### background_sync.py — Cloud Sync Runner

Starts a daemon thread on app startup. Works on both local and Streamlit Cloud.

### utils/cxalloy.py — Data Loader

Reads from SQLite if database exists, falls back to live API. Cached with `@st.cache_data(ttl=60)`.

### utils/cleaning.py — Data Cleaning

`clean_all()` orchestrates: `clean_issues()`, `clean_checklists()`, `clean_tests()`, `clean_equipment()`.

### utils/filters.py — Sidebar Filters

`apply_filters()` takes a DataFrame and filter dict, returns matching rows.

### inspect_data.py — Debug Utility

Dumps raw API data to CSV in `data/`. Run with `python inspect_data.py`.

---

## Setup

### Prerequisites

- Python 3.11+
- A CxAlloy API account with identifier and secret
- VS Code (recommended)
- VS Code extension: **SQLite Viewer** (optional, for browsing the database)

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/kspann-hub/SMF-Dashboard.AVIVATION-TEMPLATE.git
   cd SMF-Dashboard.AVIVATION-TEMPLATE
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your secrets file at `.streamlit/secrets.toml`:
   ```toml
   [cxalloy]
   identifier = "your-identifier-here"
   secret = "your-secret-here"
   ```

---

## Running the Dashboard

### Quick Start (single terminal)

```bash
streamlit run app.py
```

Background sync starts automatically. If `dashboard_data.db` exists (committed in repo), the app loads instantly. Sync refreshes every 12 hours.

### Development Mode (two terminals)

```bash
# Terminal 1 — sync data (Ctrl+Shift+5 in VS Code to split)
python sync_job.py

# Terminal 2 — run dashboard
streamlit run app.py
```

### Inspecting Raw Data

```bash
python inspect_data.py
```

### Querying the Database Directly

```bash
# Row counts
python -c "
import sqlite3
conn = sqlite3.connect('dashboard_data.db')
for table in ['Issues', 'Checklists', 'Tests', 'People', 'Companies', 'Equipment']:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM [{table}]').fetchone()[0]
        print(f'{table}: {count} rows')
    except: pass
"

# Check statuses
python -c "
import sqlite3, pandas as pd
conn = sqlite3.connect('dashboard_data.db')
print(pd.read_sql('SELECT DISTINCT status FROM [Issues]', conn))
print(pd.read_sql('SELECT DISTINCT status FROM [Checklists]', conn))
"

# Last sync time
python -c "
import sqlite3, pandas as pd
conn = sqlite3.connect('dashboard_data.db')
print(pd.read_sql('SELECT * FROM _sync_log ORDER BY synced_at DESC LIMIT 5', conn))
"
```

---

## Understanding the Data

### Issues

Deficiencies, punch list items, or problems found during commissioning.

| Field | Description |
|-------|-------------|
| `name` | Issue identifier |
| `status` | Open, In Progress, Pending Review, Closed |
| `priority` | Severity level |
| `discipline` | Trade/division |
| `assigned_company` | Contractor (resolved from lookup) |
| `days_open` | Calculated age in days |
| `aging_category` | ">60 Days", "45-60 Days", or "Under 45 Days" |

### Checklists

Pre-functional checklists verifying equipment installation before testing.

| Field | Description |
|-------|-------------|
| `status` | Workflow status |
| `discipline` | Trade responsible |
| `assigned_company` | Contractor assigned |
| Pipeline dates | `script_in_development_date`, `assigned_date`, `in_progress_date`, `contractor_complete_date`, `verified_date` |

### Tests

Functional performance tests run after checklists complete.

| Field | Description |
|-------|-------------|
| `status` | Passed, Failed, Not Started, In Progress |
| `asset_name` | Equipment unit being tested |
| `attempt_count` | Number of test attempts |

### Equipment

Physical equipment units tracked in the project.

| Field | Description |
|-------|-------------|
| `name` | Equipment tag/identifier |
| `type` | Equipment category |
| `status` | Delivery/installation status |
| `attributes` | JSON with floor, zone, and other metadata |

---

## Dashboard Tabs & Analysis

### Tab 1: Issue Tracking

KPI cards (open issues, aging, high priority), priority donut, status bar chart, issues by division and contractor, open issues detail table.

**Answers:** Which contractors have the most unresolved issues? Are issues aging out? Which disciplines generate the most deficiencies?

### Tab 2: Checklist (PFC)

Pipeline progress, completion by discipline and contractor, pending assignments.

**Answers:** What percentage of checklists are complete per trade? Which contractors are behind? Any checklists still unassigned?

### Tab 3: Functional Tests

Pass rates, results by equipment unit and contractor, attempt tracking.

**Answers:** What's the overall pass rate? Which units are failing? Which contractors produce the best results?

### Tab 4: Vertical Conveyance / Equipment

Equipment inventory linked to checklists, tests, and issues. Filterable by floor and space.

**Answers:** Which equipment has incomplete checklists? Which has open issues blocking progress?

---

## Configuration

Edit `config.py` to match your project. To discover what values exist:

```bash
python -c "
import sqlite3, pandas as pd, json
conn = sqlite3.connect('dashboard_data.db')
print('=== Issue Statuses ===')
print(pd.read_sql('SELECT DISTINCT status FROM [Issues]', conn))
print()
print('=== Checklist Statuses ===')
print(pd.read_sql('SELECT DISTINCT status FROM [Checklists]', conn))
print()
print('=== Extended Status Fields ===')
df = pd.read_sql('SELECT extended_status FROM [Checklists] LIMIT 5', conn)
for val in df['extended_status']:
    try:
        print(list(json.loads(val).keys()))
        break
    except: pass
"
```

Update `config.py` and the `flatten_extended_status` call in `cleaning.py` to match.

### Sync Interval

- **Local:** edit `SYNC_INTERVAL_MINUTES` in `sync_job.py`
- **Cloud:** edit `interval_hours` in `start_background_sync()` call in `app.py`

---

## Creating a New Project from This Template

### Step 1 — Create a New Repo

Go to this repo on GitHub → **"Use this template"** → **"Create a new repository"** → name it for the project.

### Step 2 — Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/your-new-repo.git
cd your-new-repo
pip install -r requirements.txt
```

### Step 3 — Add Credentials

Create `.streamlit/secrets.toml`:

```toml
[cxalloy]
identifier = "your-identifier-here"
secret = "your-secret-here"
```

### Step 4 — Sync Data

```bash
python sync_job.py
```

Watch for row counts. Verify with SQLite Viewer or query commands.

### Step 5 — Update Config

Run the status discovery commands, then update `config.py` and `cleaning.py`.

### Step 6 — Run and Verify

```bash
streamlit run app.py
```

### Step 7 — Commit and Deploy

```bash
git add -A
git commit -m "Initial setup with synced data"
git push
```

---

## Deploying to Streamlit Cloud

1. Push all files to GitHub (`secrets.toml` in `.gitignore`, `dashboard_data.db` NOT in `.gitignore`)
2. Connect repo at [share.streamlit.io](https://share.streamlit.io)
3. Add credentials under **Settings → Secrets**:
   ```toml
   [cxalloy]
   identifier = "your-identifier-here"
   secret = "your-secret-here"
   ```
4. Deploy — loads instantly from committed database, background sync keeps it fresh

**Note:** Streamlit Cloud apps sleep after inactivity. On wake, they re-clone the repo — because `dashboard_data.db` is in the repo, the app has data immediately.

---

## Troubleshooting

**"No data available" on all tabs**
- Sync hasn't finished. Check terminal for progress. Verify credentials. Run `python sync_job.py` manually.

**"Found 0 projects"**
- Check API credentials. Test: `python -c "from sync_logic import api_get; print(api_get('project'))"`

**"type dict is not supported" during sync**
- Verify `save_to_db()` in `sync_logic.py` has the dict/list to JSON conversion loop.

**"table X has no column named Y"**
- Different projects have different columns. Verify `save_to_db()` has the ALTER TABLE logic.

**"UnboundLocalError: cannot access local variable"**
- A dataset is missing from `all_sheets`. Ensure all keys use `.get()` fallbacks in `layout.py`.

**Charts show wrong percentages**
- Check `config.py` statuses match actual data. Check `cleaning.py` for empty strings vs `pd.NA`.

**Git push rejected**
- `git pull --rebase` then `git push`. If stuck: `git rebase --abort` then retry. Last resort: `git push --force`.

---

## Security

- **NEVER commit `.streamlit/secrets.toml`** to GitHub
- Credentials go in two places only: local `secrets.toml` and Streamlit Cloud Secrets settings
- If accidentally committed, immediately rotate your API key in CxAlloy

---

## Customization

| What's Different | File to Edit |
|---|---|
| Status labels or pipeline stages | `config.py` |
| Column names from CxAlloy | `utils/cleaning.py` |
| API endpoints | `utils/cxalloy.py` and `sync_logic.py` |
| Charts, KPI cards, tab layout | `layout.py` |
| Sidebar filters | `utils/filters.py` and `app.py` |
| Branding (colors, fonts) | CSS section in `app.py` |
| Sync interval | `sync_job.py` or `background_sync.py` call in `app.py` |

---

## .gitignore

```
.streamlit/secrets.toml
__pycache__/
*.pyc
data/
venv/
```

Note: `dashboard_data.db` is intentionally NOT in `.gitignore` — it needs to be in the repo for Streamlit Cloud to have data on deploy.
