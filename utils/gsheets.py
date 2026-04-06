import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=300)
def load_project_data(sheet_name: str) -> dict:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_name)

    sheets = {}
    for ws in spreadsheet.worksheets():
        records = ws.get_all_records()
        sheets[ws.title] = pd.DataFrame(records) if records else pd.DataFrame()
    return sheets