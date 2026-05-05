import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
from google import genai
import time

# 1. SETTINGS & THEME
st.set_page_config(page_title="Nivesh Pharma Ultra v3.0", layout="wide", page_icon="💊")

st.markdown("""
    <style>
    .main { background: #0e1117; color: #e6edf3; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #238636; color: white; height: 3em; }
    div[data-testid="stMetric"] { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE
DB_FILES = {"inv": "inventory.csv", "sales": "sales_history.csv", "users": "users.csv"}

def load_enterprise_data():
    # Files initialize karna agar nahi hain
    if not os.path.exists(DB_FILES["inv"]):
        pd.DataFrame(columns=["Medicine", "Stock", "Expiry Date", "Unit Price (₹)", "Cost Price (₹)", "Category"]).to_csv(DB_FILES["inv"], index=False)
    if not os.path.exists(DB_FILES["sales"]):
        pd.DataFrame(columns=["Date", "Item", "Qty", "Total", "Profit", "User"]).to_csv(DB_FILES["sales"], index=False)
    if not os.path.exists(DB_FILES["users"]):
        pd.DataFrame([{"username": "admin", "password": "pharma2026"}]).to_csv(DB_FILES["users"], index=False)

    inv = pd.read_csv(DB_FILES["inv"])
    sales = pd.read_csv(DB_FILES["sales"])
    
    # Force Numeric (Errors fix karne ke liye)
    for col in ["Unit Price (₹)", "Cost Price (₹)", "Stock"]:
        if col in inv.columns: inv[col] = pd.to_numeric(inv[col], errors='coerce').fillna(0)
    for col in ["Total", "Profit", "Qty"]:
        if col in sales.columns: sales[col] = pd.to_numeric(sales[col], errors='coerce').fillna(0)
    
    return inv, sales

# Data Load Karo
inv, sales = load_enterprise_data()

# 3. AUTHENTICATION SYSTEM
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.title("🛡️ Pharma Portal Login")
        u = st.text_input("Username (Default: admin)")
        p = st.text_input("Password (Default: pharma2026)", type="password")
        if st.button("Login"):
            users_db = pd.read_csv(DB_FILES["users"])
            if u in users_db['username'].values and str(p) == str(users_db[users_db['username'] == u]['password'].values[0]):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop() # Dashboard tabhi dikhega jab login hoga

# --- DASHBOARD STARTS HERE ---
st.title(f"🚀 Nivesh Pharma Ultra (User: {st.session_state.username})")

# Tabs Setup
t1, t2, t3, t4 = st.tabs(["🛒 Super POS", "📦 Inventory Pro", "🌿 AI Herbal Lab", "📈 Analytics"])
