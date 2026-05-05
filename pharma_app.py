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

# ==========================================
# 4. MODULE: ADVANCED POS SYSTEM
# ==========================================
with t1:
    st.markdown("### 🛒 Enterprise Point of Sale")
    
    # Cart State Initialization
    if 'cart' not in st.session_state:
        st.session_state.cart = []

    pos_l, pos_r = st.columns([1, 1.2])

    with pos_l:
        st.subheader("Quick Billing")
        if not inv.empty:
            # Searchable Selection
            med_list = inv["Medicine"].unique()
            selected_med = st.selectbox("Search Medicine", med_list, key="pos_search")
            
            # Fetching real-time data
            m_data = inv[inv["Medicine"] == selected_med].iloc[0]
            stock_left = int(m_data["Stock"])
            
            # Inventory Alerts
            if stock_left < 10:
                st.warning(f"⚠️ Low Stock: Only {stock_left} left!")
            else:
                st.info(f"✅ Availability: {stock_left} in stock")

            # Selection Inputs
            c1, c2 = st.columns(2)
            u_price = c1.number_input("Unit Price (₹)", value=float(m_data["Unit Price (₹)"]), disabled=True)
            sel_qty = c2.number_input("Quantity", 1, max(1, stock_left), step=1, key="pos_qty")

            if st.button("➕ Add to Invoice", key="pos_add"):
                item_total = sel_qty * u_price
                # Adding to session cart with full metadata
                st.session_state.cart.append({
                    "Item": selected_med,
                    "Qty": int(sel_qty),
                    "Price": float(u_price),
                    "Cost": float(m_data["Cost Price (₹)"]),
                    "Total": float(item_total),
                    "Timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                })
                st.toast(f"Added {selected_med} to cart!")
                st.rerun()
        else:
            st.error("Inventory database is empty. Please add stock in 'Inventory Pro'.")

    with pos_r:
        st.subheader("Invoice Summary")
        if st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            
            # Interactive Table
            st.table(cart_df[["Item", "Qty", "Price", "Total"]])
            
            final_total = cart_df["Total"].sum()
            st.markdown(f"## **Payable: ₹{final_total:,.2f}**")
            
            # Action Buttons
            cb1, cb2 = st.columns(2)
            if cb1.button("🗑️ Clear Cart"):
                st.session_state.cart = []
                st.rerun()
                
            if cb2.button("🚀 Finalize & Print"):
                with st.spinner("Syncing Inventory & Ledger..."):
                    invoice_id = f"INV-{int(time.time())}"
                    
                    for item in st.session_state.cart:
                        # 1. Atomic Stock Update
                        inv.loc[inv["Medicine"] == item["Item"], "Stock"] -= item["Qty"]
                        inv.loc[inv["Medicine"] == item["Item"], "Last Updated"] = str(datetime.date.today())
                        
                        # 2. Profit Calculation (Strict Numeric)
                        profit_val = float(item["Total"]) - (int(item["Qty"]) * float(item["Cost"]))
                        
                        # 3. Append to Sales History
                        new_sale = {
                            "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Invoice_ID": invoice_id,
                            "Item": item["Item"],
                            "Qty": item["Qty"],
                            "Total": item["Total"],
                            "Profit": profit_val,
                            "User": st.session_state.username
                        }
                        sales = pd.concat([sales, pd.DataFrame([new_sale])], ignore_index=True)
                    
                    # 4. Save to Disk
                    inv.to_csv(DB_FILES["inv"], index=False)
                    sales.to_csv(DB_FILES["sales"], index=False)
                    
                    # Success State
                    st.session_state.cart = []
                    st.balloons()
                    st.success(f"Invoice {invoice_id} generated successfully!")
                    time.sleep(2)
                    st.rerun()
        else:
            st.caption("Scan items or search to start billing.")
