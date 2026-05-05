import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from fpdf import FPDF
import time

# ==========================================
# 1. ENTERPRISE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="Nivesh Pharma Ultra v3.0", 
    layout="wide", 
    page_icon="💊",
    initial_sidebar_state="expanded"
)

# Custom UI Injection for Premium Feel
st.markdown("""
    <style>
    /* Main Background & Glassmorphism */
    .main { background: linear-gradient(135deg, #0e1117 0%, #161b22 100%); color: #e6edf3; }
    
    /* Advanced Sidebar */
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    
    /* Enterprise Metrics Card */
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #4CAF50 !important; }
    div[data-testid="stMetric"] { 
        background: rgba(23, 28, 36, 0.8); 
        border: 1px solid #30363d; 
        padding: 20px; 
        border-radius: 12px;
        transition: 0.3s ease;
    }
    div[data-testid="stMetric"]:hover { border-color: #4CAF50; transform: translateY(-3px); }
    
    /* Professional Buttons */
    .stButton>button { 
        width: 100%; border-radius: 8px; font-weight: 600; 
        height: 3.2em; transition: all 0.2s ease;
        background-color: #238636; border: none; color: white;
    }
    .stButton>button:hover { background-color: #2ea043; border: none; box-shadow: 0px 4px 15px rgba(46, 160, 67, 0.4); }
    
    /* Success/Error Styling */
    .stAlert { border-radius: 10px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA ENGINE (ZERO-ERROR ARCHITECTURE)
# ==========================================
DB_FILES = {
    "inv": "inventory.csv",
    "sales": "sales_history.csv",
    "users": "users.csv",
    "logs": "system_logs.csv"
}

def secure_init():
    """Initializes system files with correct headers if they don't exist."""
    headers = {
        "inv": ["Medicine", "Stock", "Expiry Date", "Unit Price (₹)", "Cost Price (₹)", "Category", "Last Updated"],
        "sales": ["Date", "Invoice_ID", "Item", "Qty", "Total", "Profit", "User"],
        "users": ["username", "password", "role", "created_at"],
        "logs": ["Timestamp", "User", "Action", "Status"]
    }
    
    for key, filename in DB_FILES.items():
        if not os.path.exists(filename) or os.stat(filename).st_size == 0:
            df = pd.DataFrame(columns=headers[key])
            if key == "users":
                # Default Admin Account
                df = pd.DataFrame([{"username": "admin", "password": "pharma2026", "role": "Owner", "created_at": str(datetime.date.today())}])
            df.to_csv(filename, index=False)

def load_enterprise_data():
    """Loads and sanitizes all data to prevent UFuncNoLoopError."""
    secure_init()
    
    try:
        # Load Inventory
        inv = pd.read_csv(DB_FILES["inv"])
        num_cols_inv = ["Unit Price (₹)", "Cost Price (₹)", "Stock"]
        for col in num_cols_inv:
            inv[col] = pd.to_numeric(inv[col], errors='coerce').fillna(0.0)
        
        # Load Sales
        sales = pd.read_csv(DB_FILES["sales"])
        num_cols_sales = ["Qty", "Total", "Profit"]
        for col in num_cols_sales:
            sales[col] = pd.to_numeric(sales[col], errors='coerce').fillna(0.0)
            
        return inv, sales
    except Exception as e:
        st.error(f"Critical System Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Initialize Global Data
inv, sales = load_enterprise_data()

# ==========================================
# 3. AUTHENTICATION MODULE (BYPASS PROOF)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

def login_system():
    if not st.session_state.logged_in:
        left, mid, right = st.columns([1, 1.2, 1])
        with mid:
            st.image("https://cdn-icons-png.flaticon.com/512/3209/3209101.png", width=100)
            st.title("Pharma Enterprise Login")
            
            with st.container(border=True):
                user_input = st.text_input("Admin ID", placeholder="Enter username")
                pass_input = st.text_input("Access Key", type="password", placeholder="Enter password")
                
                if st.button("Authenticate System"):
                    users_db = pd.read_csv(DB_FILES["users"])
                    # Check credentials against DB
                    match = users_db[(users_db['username'] == user_input) & (users_db['password'] == str(pass_input))]
                    
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.username = user_input
                        st.session_state.user_role = match.iloc[0]['role']
                        st.success("Authentication successful! Loading modules...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Access Denied: Invalid Credentials")
            
            st.caption("v3.0 Secure Enterprise Access | Authorized Personnel Only")
        st.stop()

login_system()
