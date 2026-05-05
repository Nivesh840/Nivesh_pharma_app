import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from google import genai
from fpdf import FPDF

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Nivesh Pharma Ultra", layout="wide", page_icon="💊")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4CAF50; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FILES & INITIALIZATION ---
FILES = {
    "inv": "inventory.csv",
    "sales": "sales_history.csv",
    "users": "users.csv"
}

def init_db():
    for key, f in FILES.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            if key == "inv":
                pd.DataFrame(columns=["Medicine", "Stock", "Expiry Date", "Unit Price (₹)", "Cost Price (₹)", "Category"]).to_csv(f, index=False)
            elif key == "sales":
                pd.DataFrame(columns=["Date", "Item", "Qty", "Total", "Profit", "User"]).to_csv(f, index=False)
            elif key == "users":
                pd.DataFrame([{"username": "nivesh", "password": "pharma2026"}]).to_csv(f, index=False)

init_db()

# --- 3. LOGIN & SIGNUP LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div style="background-color: #1e1e1e; padding: 30px; border-radius: 15px; border: 1px solid #4CAF50;">', unsafe_allow_html=True)
        st.title("🛡️ Pharma Portal")
        
        # Mode selector: Login ya Sign Up
        auth_mode = st.radio("Chunno:", ["Login", "Sign Up"], horizontal=True)
        
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        
        if auth_mode == "Sign Up":
            email = st.text_input("Email (Optional)")
            if st.button("Register Karo"):
                if u and p:
                    users = pd.read_csv("users.csv")
                    if u in users['username'].values:
                        st.warning("Ye username pehle se hai!")
                    else:
                        new_user = pd.DataFrame([{"username": u, "password": p}])
                        new_user.to_csv("users.csv", mode='a', header=False, index=False)
                        st.success("Account ban gaya! Ab Login mode select karke enter karein.")
                else:
                    st.error("Username aur Password bharna zaroori hai.")
        
        else: # Login Mode
            if st.button("Access Dashboard"):
                users = pd.read_csv("users.csv")
                # Username aur password check
                if u in users['username'].values:
                    stored_pw = str(users[users['username'] == u]['password'].values[0])
                    if str(p) == stored_pw:
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.rerun()
                    else:
                        st.error("Galat Password!")
                else:
                    st.error("Username nahi mila!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 4. DASHBOARD CONTENT (Dhashu Features) ---
inv = pd.read_csv("inventory.csv")
sales = pd.read_csv("sales_history.csv")

# Sidebar Stats
st.sidebar.title(f"👤 {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.title("🚀 Nivesh Pharma Ultra-Dashboard")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Items in Stock", len(inv))
m2.metric("Total Revenue", f"₹{sales['Total'].sum() if not sales.empty else 0}")
m3.metric("Net Profit", f"₹{sales['Profit'].sum() if not sales.empty else 0}", delta="Live")
m4.metric("Low Stock Alerts", len(inv[inv['Stock'] < 10]) if not inv.empty else 0)

t1, t2, t3, t4 = st.tabs(["🛒 Super POS", "📦 Inventory Pro", "🌿 AI Herbal Lab", "📈 Analytics"])

# --- TAB 1: SUPER POS (FAST BILLING) ---
with t1:
    col_a, col_b = st.columns([1, 1.2])
             with col_b:
        st.subheader("Invoice Summary")
        if 'cart' in st.session_state and st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.dataframe(cart_df[["Item", "Qty", "Price", "Total"]], use_container_width=True)
            
            total_amt = cart_df["Total"].sum()
            st.header(f"Total: ₹{total_amt}")
            
        # --- TAB 1: SUPER POS (No Duplicate ID Version) ---
with t1:
    col_a, col_b = st.columns([1, 1.2])
             with col_a:
        st.subheader("Quick Billing")
        if not inv.empty:
            # UNIQUE KEY: 'pos_med_select'
            med = st.selectbox("Select Med", inv["Medicine"].unique(), key="pos_med_select")
            med_data = inv[inv["Medicine"] == med].iloc[0]
            
            # Stock display
            current_stock = int(med_data["Stock"])
            st.info(f"📦 Stock available: {current_stock}")
            
            # UNIQUE KEY: 'pos_qty_input'
            qty = st.number_input("Quantity", 1, max(1, current_stock), step=1, key="pos_qty_input")
            
            # UNIQUE KEY: 'pos_add_btn'
            if st.button("➕ Add to Cart", key="pos_add_btn"):
                if 'cart' not in st.session_state: 
                    st.session_state.cart = []
                
                st.session_state.cart.append({
                    "Item": med, 
                    "Qty": int(qty), 
                    "Price": float(med_data["Unit Price (₹)"]),
                    "Cost": float(med_data["Cost Price (₹)"]), 
                    "Total": float(qty * med_data["Unit Price (₹)"])
                })
                st.rerun()
        else:
            st.warning("Inventory khali hai!")
             with col_b:
        st.subheader("Invoice Summary")
        if 'cart' in st.session_state and len(st.session_state.cart) > 0:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.table(cart_df[["Item", "Qty", "Price", "Total"]])
            
            total_amt = cart_df["Total"].sum()
            st.success(f"### Total Amount: ₹{total_amt}")
            
            # UNIQUE KEY: 'pos_finalize_btn'
            if st.button("🚀 Finalize & Print Bill", key="pos_finalize_btn"):
                for item in st.session_state.cart:
                    inv.loc[inv["Medicine"] == item["Item"], "Stock"] -= int(item["Qty"])
                    
                    new_sale = {
                        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Item": item["Item"], "Qty": item["Qty"], "Total": item["Total"],
                        "Profit": item["Total"] - (item["Qty"] * item["Cost"]), 
                        "User": st.session_state.username
                    }
                    sales = pd.concat([sales, pd.DataFrame([new_sale])], ignore_index=True)
                
                inv.to_csv("inventory.csv", index=False)
                sales.to_csv("sales_history.csv", index=False)
                st.session_state.cart = []
                st.balloons()
                st.success("Sale Recorded!")
                st.rerun()
        else:
            st.write("Cart is empty.")
    
# --- TAB 2: INVENTORY PRO ---
with t2:
    st.subheader("Stock Management")
    with st.expander("➕ Add New Medicine"):
        with st.form("add_form"):
            name = st.text_input("Medicine Name")
            c1, c2, c3 = st.columns(3)
            stock = c1.number_input("Initial Stock", 0)
            cost = c2.number_input("Cost Price", 0.0)
            price = c3.number_input("Selling Price", 0.0)
            exp = st.date_input("Expiry Date")
            cat = st.selectbox("Category", ["Tablet", "Syrup", "Herbal", "Cosmetic"])
            
            if st.form_submit_button("Save to Inventory"):
                new_item = {"Medicine": name, "Stock": stock, "Expiry Date": str(exp), 
                            "Unit Price (₹)": price, "Cost Price (₹)": cost, "Category": cat}
                pd.concat([inv, pd.DataFrame([new_item])], ignore_index=True).to_csv("inventory.csv", index=False)
                st.success("Stock Updated!")
                st.rerun()
    st.dataframe(inv, use_container_width=True)

# --- TAB 3: AI HERBAL LAB (B.Pharm Project Special) ---
with t3:
    st.subheader("🌿 AI Botanical & Clinical Analysis")
    herb = st.text_input("Enter Herb/Ingredient Name for Research", key="herb_input")
    
    if herb:
        if st.button("Run AI Analysis", key="ai_btn"):
            with st.spinner("Analyzing Clinical Data..."):
                try:
                    # SECRETS SE KEY UTHANA (Sahi Tarika)
                    if "GEMINI_API_KEY" in st.secrets:
                        api_val = st.secrets["GEMINI_API_KEY"]
                        client = genai.Client(api_key=api_val)
                        
                        response = client.models.generate_content(
                            model="gemini-1.5-flash", 
                            contents=f"Analyze {herb} for B.Pharm project: Uses, Side effects, and Role in Cosmetics in Hinglish."
                        )
                        st.markdown(response.text)
                    else:
                        st.error("❌ API Key nahi mili! Streamlit Settings > Secrets mein GEMINI_API_KEY dalo.")
                except Exception as e:
                    st.error(f"⚠️ AI Connection Error: {e}")

# --- TAB 4: ANALYTICS ---
with t4:
    if not sales.empty:
        st.subheader("Business Insights")
        fig = px.line(sales, x="Date", y="Profit", title="Profit over Time")
        st.plotly_chart(fig, use_container_width=True)
