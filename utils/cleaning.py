import pandas as pd
import re

# ─── Column Name Standardization ──────────────────────────────────────────────
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip spaces, replace spaces with underscores in column names."""
    if df.empty:
        return df
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_', regex=False)
        .str.replace(r'[^\w]', '_', regex=True)
    )
    return df

# ─── People Tab ───────────────────────────────────────────────────────────────
def clean_people(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)
    df['person_id'] = df['person_id'].astype(str).str.strip()
    df['company'] = df['company'].astype(str).str.strip()
    df['first_name'] = df['first_name'].astype(str).str.strip()
    df['last_name'] = df['last_name'].astype(str).str.strip()
    df['full_name'] = df['first_name'] + ' ' + df['last_name']
    df['role'] = df['role'].astype(str).str.strip()
    return df

# ─── Build Company Lookup ─────────────────────────────────────────────────────
def build_company_lookup(people: pd.DataFrame) -> dict:
    """Returns person_id → company name dict."""
    if people.empty:
        return {}
    return dict(zip(people['person_id'], people['company']))

# ─── Resolve Assigned Company ─────────────────────────────────────────────────
def resolve_assigned_company(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    """
    Adds assigned_company column by resolving:
    - If assigned_key matches a person_id in People tab → use that person's company
    - If no match → use assigned_name directly (already a company name or role)
    """
    if df.empty or 'assigned_name' not in df.columns:
        return df
    df = df.copy()

    def resolve(row):
        key = str(row.get('assigned_key', '')).strip()
        # Try to find this key in the person lookup first
        if key in lookup:
            return lookup[key]  # returns the company from People tab
        # If no match, assigned_name is already a company name or role — use it
        return str(row.get('assigned_name', '')).strip()

    df['assigned_company'] = df.apply(resolve, axis=1)
    return df

# ─── Issues Tab ───────────────────────────────────────────────────────────────
def clean_issues(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)

    # Dates
    for col in ['date_created', 'date_closed', 'due_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Days open
    today = pd.Timestamp.now()
    if 'date_created' in df.columns:
        df['days_open'] = (today - df['date_created']).dt.days.fillna(0).astype(int)
    
    # Aging category — only for non-closed issues
    def aging_cat(row):
        if str(row.get('status', '')).lower() == 'closed':
            return 'Closed'
        d = row.get('days_open', 0)
        if d > 60:
            return '>60 Days'
        elif d >= 45:
            return '45-60 Days'
        return 'Under 45 Days'
    df['aging_category'] = df.apply(aging_cat, axis=1)

    # Strip whitespace from key string columns
    for col in ['status', 'priority', 'discipline', 'assigned_name', 'assigned_type']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Resolve company
    df = resolve_assigned_company(df, lookup)

    return df

# ─── Checklists Tab ───────────────────────────────────────────────────────────
def clean_checklists(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)

    # Dates
    for col in ['date_created']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Strip whitespace
    for col in ['status', 'discipline', 'assigned_name', 'assigned_type', 'type_name']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Resolve company
    df = resolve_assigned_company(df, lookup)

    return df

# ─── Tests Tab ────────────────────────────────────────────────────────────────
def clean_tests(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)

    # Dates
    for col in ['date_created']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Strip whitespace
    for col in ['status', 'discipline', 'assigned_name', 'assigned_type']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Resolve company
    df = resolve_assigned_company(df, lookup)

    return df

# ─── Equipment Tab ────────────────────────────────────────────────────────────
def clean_equipment(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)

    for col in ['status', 'discipline', 'type', 'floor', 'building']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

# ─── Master Clean Function ────────────────────────────────────────────────────
def clean_all(sheets: dict) -> dict:
    """
    Takes the raw dict of DataFrames from gsheets.py and returns
    a fully cleaned version. This is the single entry point.
    """
    cleaned = {}

    # Clean People first so we can build the lookup
    people = clean_people(sheets.get('People', pd.DataFrame()))
    cleaned['People'] = people
    lookup = build_company_lookup(people)

    # Clean everything else using the lookup
    cleaned['Issues'] = clean_issues(sheets.get('Issues', pd.DataFrame()), lookup)
    cleaned['Checklists'] = clean_checklists(sheets.get('Checklists', pd.DataFrame()), lookup)
    cleaned['Tests'] = clean_tests(sheets.get('Tests', pd.DataFrame()), lookup)
    cleaned['Equipment'] = clean_equipment(sheets.get('Equipment', pd.DataFrame()))

    # Pass through any other tabs unchanged but with standardized columns
    for tab, df in sheets.items():
        if tab not in cleaned:
            cleaned[tab] = standardize_columns(df)

    return cleaned