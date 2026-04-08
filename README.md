# ⚠️ EDITING CURRENTLY — This document is a work in progress

---

# CriticalArc Commissioning Dashboard

A Streamlit-based web application for visualizing commissioning progress across CriticalArc projects. Data is pulled live from the CxAlloy TQ API and displayed across interactive tabs covering issue tracking, checklists, functional tests, and vertical conveyance.

---

## Project Structure

```
criticalarc-dashboard/
│
├── app.py                  # Main entry point — runs the Streamlit app
├── layout.py               # Dashboard layout and all chart/tab rendering
├── config.py               # (if used) Project-level config settings
│
├── utils/
│   ├── cxalloy.py          # CxAlloy API connection — fetches all project data
│   ├── cleaning.py         # Cleans and enriches raw API data
│   └── filters.py          # Applies sidebar filters to DataFrames
│
├── data/                   # Local CSV snapshots (written by inspect_data.py)
│   ├── SMF_Pedestrian_Walkway/
│   │   ├── issues.csv
│   │   ├── checklists.csv
│   │   ├── tests.csv
│   │   ├── people.csv
│   │   ├── companies.csv
│   │   ├── equipment.csv
│   │   └── _last_pulled.csv
│   └── SMF_Terminal_B_Parking_Garage/
│       └── ...
│
├── inspect_data.py         # Standalone script to pull raw data to CSV for inspection
├── .streamlit/
│   └── secrets.toml        # API credentials (never commit this to GitHub)
└── requirements.txt        # Python dependencies
```

---

## How the Data Flows

```
CxAlloy TQ API
     │
     ▼
utils/cxalloy.py          ← Authenticates and fetches paginated data
     │
     ▼
utils/cleaning.py         ← Standardizes columns, resolves companies, flattens nested fields
     │
     ▼
utils/filters.py          ← Applies sidebar filters (discipline, contractor, status)
     │
     ▼
layout.py                 ← Renders KPI cards, charts, and tables per tab
     │
     ▼
app.py                    ← Streamlit entry point, sidebar, header, project selector
```

---

## Script Reference

### `app.py`
The main Streamlit entry point. Handles:
- Page config and global CSS styling
- Loading the project list from the CxAlloy API
- Sidebar: project selector, discipline/contractor/status filters, refresh button
- Page header (project name, last refreshed timestamp)
- Calling `layout.py` to render the dashboard

### `layout.py`
Contains all dashboard rendering logic split across four tabs:
- **Issue Tracking** — open issue KPIs, priority/status/division/contractor breakdowns, aging issues table
- **Checklist (PFC)** — completion KPIs, status donut, completion % by division and contractor
- **Functional Tests** — pass rate KPIs, status breakdown, pass rate by division and equipment type
- **Vertical Conveyance** — filtered view of issues belonging to conveying/division 14 disciplines

### `utils/cxalloy.py`
Handles all communication with the CxAlloy TQ API (`https://tq.cxalloy.com/api/v1`). Key functions:
- `load_all_projects()` — fetches all projects on the account (no project ID needed)
- `load_project_data(project_id)` — fetches issues, checklists, tests, people, companies, and equipment for a given project, then passes through `cleaning.py`

Authentication uses HMAC-SHA256 signature generation — every request requires a fresh timestamp and signature built from the secret key.

### `utils/cleaning.py`
Cleans and enriches raw DataFrames returned from the API. Key functions:
- `standardize_columns()` — lowercases and underscores all column names
- `safe_parse()` — safely parses stringified JSON/dicts (handles NaN gracefully)
- `build_lookups()` — builds person_id → company and company_id → company name lookup dicts
- `resolve_assigned_company()` — resolves the `assigned_company` field based on `assigned_type`:
  - `"company"` → looks up company name by company_id
  - `"person"` → looks up person's company via person_id
  - `"role"` → uses the role label directly (e.g. "Mechanical Contractor") until a real company is assigned
- `flatten_extended_status()` — unpacks nested status history dicts into flat columns
- `clean_all()` — master function that runs all of the above in the correct order

### `utils/filters.py`
Single function `apply_filters(df, filters)` that filters a DataFrame by discipline, contractor (mapped to `assigned_company`), and status based on sidebar selections.

### `inspect_data.py`
A standalone utility script (not part of the Streamlit app) used to pull raw data from the API and save it locally as CSVs for inspection. Run this when:
- Setting up a new project to verify the data structure
- Debugging unexpected dashboard behavior
- Checking what columns the API is returning

```bash
python inspect_data.py
```

Output is saved to `data/<Project_Name>/` with one CSV per endpoint plus a `_last_pulled.csv` log.

---

## API Authentication

CxAlloy uses HMAC-SHA256 signed requests. Every API call requires five headers:

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |
| `cxalloy-identifier` | Your API key identifier |
| `cxalloy-signature` | HMAC-SHA256 hash of (body + timestamp) for POST, or just timestamp for GET |
| `cxalloy-timestamp` | Unix timestamp (must be within 1 hour of request) |
| `user-agent` | Any string identifying your app |

Credentials are stored in `.streamlit/secrets.toml`:

```toml
[cxalloy]
secret_key = "your-secret-key-here"
identifier = "your-identifier-here"
```

**Never commit `secrets.toml` to GitHub.** It is listed in `.gitignore`.

## Setup & Secrets

This app requires API credentials that **must not be committed to the repo**.

### Local Development
Create `.streamlit/secrets.toml` in your project root:
```toml
[cxalloy]
api_key = "your-api-key-here"
identifier = "your-identifier-here"
```

This file is listed in `.gitignore` and should **never** be pushed to GitHub.

### Deployment (Streamlit Community Cloud)
Add your secrets in the Streamlit dashboard:
1. Go to your app → Settings → Secrets
2. Paste the contents of your `secrets.toml` file
3. Save

⚠️ **If secrets are accidentally committed**, rotate your API keys immediately — git history retains all prior commits even after deletion.

---

## Running the App

```bash
# Activate virtual environment
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## Adding a New Project

> ⚠️ EDITING CURRENTLY — this workflow is still being finalized

The dashboard is designed to support multiple projects automatically. When a new project is added to your CxAlloy account:

1. **Verify the project appears** by running `inspect_data.py` — it will list all projects on the account and their IDs
2. **Check the data structure** — open the CSVs saved to `data/<Project_Name>/` and confirm columns are as expected
3. **The project will appear automatically** in the project selector dropdown in the sidebar — no code changes needed
4. The same `layout.py` template is used for all projects

If a new project has different discipline or status names than existing projects, you may need to update the color mappings in `layout.py` (e.g. `status_colors`, `priority_colors`).

---

## Sidebar Filters

| Filter | Source |
|---|---|
| Division / Discipline | Pulled from `equipment["discipline"]` — covers all divisions across the project |
| Contractor / Assigned To | Pulled from `companies["name"]` — all companies on the project |
| Status | Hardcoded list: All, Open, In Progress, Pending Review, Closed |

Filters apply across Issues, Checklists, and Tests simultaneously.

---

## Dependencies

Key packages (see `requirements.txt` for full list):

```
streamlit
pandas
plotly
requests
```

---

## Notes for Collaborators

- The `data/` folder contains local CSV snapshots for inspection only — the live app always fetches directly from the API
- `st.cache_data(ttl=300)` is used on API calls — data refreshes every 5 minutes automatically, or immediately when the Refresh button is clicked
- The `assigned_company` column is derived during cleaning and does not come directly from the API — it resolves roles and person assignments to their associated company
- All column names are standardized to lowercase with underscores during cleaning (e.g. `Assigned Name` becomes `assigned_name`)