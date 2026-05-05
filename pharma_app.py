import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from google import genai
from fpdf import FPDF

# --- 1. DATA LOADING FUNCTION ---
def load_data():
    # Files check aur initialization
    if not os.path.exists("inventory.csv"):
        pd.DataFrame(columns=["Medicine", "Stock", "Expiry Date", "Unit Price (₹)", "Cost Price (₹)", "Category"]).to_csv("inventory.csv", index=False)
    if not os.path.exists("sales_history.csv"):
        pd.DataFrame(columns=["Date", "Item", "Qty", "Total", "Profit", "User"]).to_csv("sales_history.csv", index=False)
    
    inv = pd.read_csv("inventory.csv")
    sales = pd.read_csv("sales_history.csv")
    
    # Safe Numeric Conversion
    for col in ["Unit Price (₹)", "Cost Price (₹)", "Stock"]:
        if col in inv.columns:
            inv[col] = pd.to_numeric(inv[col], errors='coerce').fillna(0)
    for col in ["Total", "Profit", "Qty"]:
        if col in sales.columns:
            sales[col] = pd.to_numeric(sales[col], errors='coerce').fillna(0)
    
    return inv, sales

# --- 2. LOGIN CHECK ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🛡️ Pharma Portal")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Access Dashboard"):
        users = pd.read_csv("users.csv")
        if u in users['username'].values and str(p) == str(users[users['username'] == u]['password'].values[0]):
            st.session_state.logged_in = True
            st.session_state.username = u
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# --- 3. LOAD DATA (ONLY AFTER LOGIN) ---
# Ye line ab line 60 ke error ko fix karegi kyunki 'inv' hamesha login ke baad load hoga
inv, sales = load_data()

with t1:
    col_a, col_b = st.columns([1, 1.2])
    with col_a:
        st.subheader("Quick Billing")
        if not inv.empty:
            med = st.selectbox("Select Med", inv["Medicine"].unique(), key="pos_med_select")
            med_data = inv[inv["Medicine"] == med].iloc[0]
            qty = st.number_input("Quantity", 1, int(med_data["Stock"]), key="pos_qty_input")
            
            if st.button("➕ Add to Cart", key="pos_add_btn"):
                if 'cart' not in st.session_state: st.session_state.cart = []
                st.session_state.cart.append({
                    "Item": med, "Qty": int(qty), 
                    "Price": float(med_data["Unit Price (₹)"]),
                    "Cost": float(med_data["Cost Price (₹)"]), 
                    "Total": float(qty * med_data["Unit Price (₹)"])
                })
                st.rerun()
        
    with col_b:
        st.subheader("Invoice Summary")
        if 'cart' in st.session_state and st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.table(cart_df[["Item", "Qty", "Price", "Total"]])
            
            if st.button("🚀 Finalize & Print Bill", key="pos_finalize"):
                for item in st.session_state.cart:
                    inv.loc[inv["Medicine"] == item["Item"], "Stock"] -= item["Qty"]
                    new_sale = {
                        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Item": item["Item"], "Qty": item["Qty"], "Total": item["Total"],
                        "Profit": float(item["Total"]) - (int(item["Qty"]) * float(item["Cost"])), 
                        "User": st.session_state.username
                    }
                    sales = pd.concat([sales, pd.DataFrame([new_sale])], ignore_index=True)
                
                inv.to_csv("inventory.csv", index=False)
                sales.to_csv("sales_history.csv", index=False)
                st.session_state.cart = []
                st.balloons()
                st.rerun()

with t2:
    st.subheader("Stock Management")
    st.dataframe(inv, use_container_width=True)
    # Add new item form... (Keep your existing form here but use pd.concat)

with t3:
    st.subheader("🌿 AI Botanical Lab")
    herb = st.text_input("Enter Herb Name", key="herb_input")
    if herb and st.button("Analyze", key="ai_btn"):
        if "GEMINI_API_KEY" in st.secrets:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            response = client.models.generate_content(model="gemini-1.5-flash", contents=f"Explain {herb} uses in pharma.")
            st.write(response.text)
        else: st.error("API Key missing in Secrets!")

with t4:
    if not sales.empty:
        fig = px.line(sales, x="Date", y="Profit", title="Profit Analysis")
        st.plotly_chart(fig)
