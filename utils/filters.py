import pandas as pd

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if df.empty:
        return df
    filtered = df.copy()

    discipline = filters.get("discipline", "All")
    contractor = filters.get("contractor", "All")
    status = filters.get("status", "All")

    if discipline != "All" and "discipline" in filtered.columns:
        filtered = filtered[filtered["discipline"] == discipline]
    if contractor != "All" and "assigned_name" in filtered.columns:
        filtered = filtered[filtered["assigned_name"] == contractor]
    if status != "All" and "status" in filtered.columns:
        filtered = filtered[filtered["status"] == status]

    return filtered