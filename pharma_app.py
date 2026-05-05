import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from fpdf import FPDF
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
    if not os.path.exists(DB_FILES["inv"]):
        pd.DataFrame(columns=["Medicine", "Stock", "Expiry Date", "Unit Price (₹)", "Cost Price (₹)", "Category"]).to_csv(DB_FILES["inv"], index=False)
    if not os.path.exists(DB_FILES["sales"]):
        pd.DataFrame(columns=["Date", "Item", "Qty", "Total", "Profit", "User"]).to_csv(DB_FILES["sales"], index=False)
    if not os.path.exists(DB_FILES["users"]):
        pd.DataFrame([{"username": "admin", "password": "pharma2026", "role": "Owner", "created_at": str(datetime.date.today())}]).to_csv(DB_FILES["users"], index=False)

    inv = pd.read_csv(DB_FILES["inv"])
    sales = pd.read_csv(DB_FILES["sales"])
    
    for col in ["Unit Price (₹)", "Cost Price (₹)", "Stock"]:
        if col in inv.columns: inv[col] = pd.to_numeric(inv[col], errors='coerce').fillna(0)
    for col in ["Total", "Profit", "Qty"]:
        if col in sales.columns: sales[col] = pd.to_numeric(sales[col], errors='coerce').fillna(0)
    
    return inv, sales

inv, sales = load_enterprise_data()

# ==========================================
# 3. MASTER AUTH & SIGNUP SYSTEM
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3209/3209101.png", width=80)
        st.title("🛡️ Pharma Portal")
        st.markdown('</div>', unsafe_allow_html=True)
        
        auth_mode = st.radio("Choose Action", ["Login", "Sign Up"], horizontal=True)
        
        with st.container(border=True):
            if auth_mode == "Login":
                u_input = st.text_input("Username", key="login_u")
                p_input = st.text_input("Password", type="password", key="login_p")
                
                if st.button("🚀 Access Dashboard", use_container_width=True):
                    if u_input == "admin" and p_input == "pharma2026":
                        st.session_state.logged_in = True
                        st.session_state.username = "Nivesh (Admin)"
                        st.rerun()
                    elif os.path.exists(DB_FILES["users"]):
                        users_db = pd.read_csv(DB_FILES["users"])
                        match = users_db[(users_db['username'] == u_input) & (users_db['password'].astype(str) == str(p_input))]
                        if not match.empty:
                            st.session_state.logged_in = True
                            st.session_state.username = u_input
                            st.rerun()
                        else:
                            st.error("Invalid Credentials!")
            else:
                new_u = st.text_input("Choose Username", key="signup_u")
                new_p = st.text_input("Choose Password", type="password", key="signup_p")
                new_r = st.selectbox("Your Role", ["Staff", "Manager", "Intern"], key="signup_r")
                
                if st.button("📝 Create My Account", use_container_width=True):
                    if new_u and new_p:
                        users_db = pd.read_csv(DB_FILES["users"])
                        if new_u in users_db['username'].values:
                            st.error("Username already taken!")
                        else:
                            new_data = pd.DataFrame([{"username": new_u, "password": str(new_p), "role": new_r, "created_at": str(datetime.date.today())}])
                            new_data.to_csv(DB_FILES["users"], mode='a', header=False, index=False)
                            st.success("Account Created! Please switch to Login.")
                    else:
                        st.error("Please fill all details.")
    st.stop()

# --- DASHBOARD STARTS HERE ---
st.title(f"🚀 Nivesh Pharma Ultra (User: {st.session_state.username})")
t1, t2, t3, t4 = st.tabs(["🛒 Super POS", "📦 Inventory Pro", "🌿 AI Herbal Lab", "📈 Analytics"])

# ==========================================
# 4. MODULE: ADVANCED POS SYSTEM
# ==========================================
def generate_pdf_bill(customer_name, cart_items, total_amount):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(35, 134, 54) 
        pdf.cell(190, 15, "NIVESH PHARMA ULTRA v3.0", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 5, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, f"Customer: {str(customer_name)}", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(65, 10, " Medicine", 1, 0, 'L', True)
        pdf.cell(20, 10, "Qty", 1, 0, 'C', True)
        pdf.cell(30, 10, "Base (Rs)", 1, 0, 'C', True)
        pdf.cell(35, 10, "GST (12%)", 1, 0, 'C', True)
        pdf.cell(40, 10, "Total (Rs)", 1, 1, 'C', True)
        pdf.set_font("Arial", '', 9)
        total_gst = 0
        for item in cart_items:
            qty = int(item['Qty'])
            base_price = float(item['Price']) / 1.12
            gst_amount = float(item['Total']) - (base_price * qty)
            name = str(item['Item']).encode('ascii', 'ignore').decode('ascii')
            pdf.cell(65, 10, f" {name}", 1)
            pdf.cell(20, 10, str(qty), 1, 0, 'C')
            pdf.cell(30, 10, f"{(base_price * qty):.2f}", 1, 0, 'C')
            pdf.cell(35, 10, f"{gst_amount:.2f}", 1, 0, 'C')
            pdf.cell(40, 10, f"{float(item['Total']):.2f}", 1, 1, 'C')
            total_gst += gst_amount
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(150, 8, "Total GST (12%):", 0, 0, 'R')
        pdf.cell(40, 8, f"Rs. {total_gst:.2f}", 1, 1, 'C')
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(150, 10, "NET PAYABLE:", 0, 0, 'R')
        pdf.cell(40, 10, f"Rs. {float(total_amount):.2f}", 1, 1, 'C')
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return None

with t1:
    if 'cart' not in st.session_state: st.session_state.cart = []
    pos_l, pos_r = st.columns([1, 1.2])
    with pos_l:
        if not inv.empty:
            med_list = inv["Medicine"].unique()
            selected_med = st.selectbox("Search Medicine", med_list)
            m_data = inv[inv["Medicine"] == selected_med].iloc[0]
            stock_left = int(m_data["Stock"])
            c1, c2 = st.columns(2)
            u_price = c1.number_input("Unit Price (₹)", value=float(m_data["Unit Price (₹)"]), disabled=True)
            sel_qty = c2.number_input("Quantity", 1, max(1, stock_left), step=1)
            if st.button("➕ Add to Invoice"):
                st.session_state.cart.append({"Item": selected_med, "Qty": int(sel_qty), "Price": float(u_price), "Cost": float(m_data["Cost Price (₹)"]), "Total": float(sel_qty * u_price)})
                st.rerun()
    with pos_r:
        if st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.table(cart_df[["Item", "Qty", "Price", "Total"]])
            final_total = cart_df["Total"].sum()
            st.markdown(f"## **Payable: ₹{final_total:,.2f}**")
            c_name = st.text_input("Billing Name", "Walking Customer")
            pdf_data = generate_pdf_bill(c_name, st.session_state.cart, final_total)
            col_pdf1, col_pdf2 = st.columns(2)
            if pdf_data: col_pdf1.download_button("📥 Download PDF Bill", pdf_data, f"Bill_{int(time.time())}.pdf", "application/pdf")
            if col_pdf2.button("🚀 Finalize Sale"):
                for item in st.session_state.cart:
                    inv.loc[inv["Medicine"] == item["Item"], "Stock"] -= item["Qty"]
                    new_sale = {"Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": item["Item"], "Qty": item["Qty"], "Total": item["Total"], "Profit": item["Total"] - (item["Qty"] * item["Cost"]), "User": st.session_state.username}
                    sales = pd.concat([sales, pd.DataFrame([new_sale])], ignore_index=True)
                inv.to_csv(DB_FILES["inv"], index=False); sales.to_csv(DB_FILES["sales"], index=False)
                st.session_state.cart = []; st.success("Sale Recorded!"); time.sleep(1); st.rerun()

# ==========================================
# 5. MODULE: INVENTORY PRO
# ==========================================
with t2:
    tab_a, tab_b = st.tabs(["➕ Add Stock", "📊 Inventory"])
    with tab_a:
        with st.form("inv_form", clear_on_submit=True):
            n = st.text_input("Medicine Name")
            c = st.selectbox("Category", ["Tablet", "Syrup", "Herbal", "Cosmetic"])
            ex = st.date_input("Expiry")
            s = st.number_input("Stock", min_value=1)
            cp = st.number_input("Cost Price", min_value=0.0)
            sp = st.number_input("Selling Price", min_value=0.0)
            if st.form_submit_button("Save"):
                new_e = {"Medicine": n.upper(), "Stock": s, "Expiry Date": str(ex), "Unit Price (₹)": sp, "Cost Price (₹)": cp, "Category": c}
                inv = pd.concat([inv, pd.DataFrame([new_e])], ignore_index=True)
                inv.to_csv(DB_FILES["inv"], index=False); st.success("Added!"); st.rerun()
    with tab_b:
        st.dataframe(inv, use_container_width=True)

# ==========================================
# 6. MODULE: AI HERBAL LAB
# ==========================================
with t3:
    st.subheader("🌿 AI Botanical Analysis")
    h_query = st.text_input("Enter Herb Name")
    if st.button("🔬 Analyze"):
        if "GEMINI_API_KEY" in st.secrets:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            resp = client.models.generate_content(model="gemini-1.5-flash", contents=f"Clinical analysis of {h_query} for B.Pharm in Hinglish.")
            st.markdown(resp.text)
        else: st.error("API Key Missing in Secrets!")

# ==========================================
# 7. MODULE: ANALYTICS
# ==========================================
with t4:
    if not sales.empty:
        k1, k2 = st.columns(2)
        k1.metric("Total Revenue", f"₹{sales['Total'].sum():,.2f}")
        k2.metric("Total Profit", f"₹{sales['Profit'].sum():,.2f}")
        st.plotly_chart(px.line(sales, x='Date', y='Total', title="Sales Trend"))
    else: st.info("No sales data yet.")

# ==========================================
# 9. SYSTEM LOGS & HEARTBEAT
# ==========================================
with st.sidebar:
    st.markdown("---")
    if st.button("📁 View Logs"): st.session_state.show_logs = not st.session_state.get('show_logs', False)
    if st.button("🔴 Logout"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if st.session_state.get('show_logs', False):
    if os.path.exists("system_logs.csv"): st.dataframe(pd.read_csv("system_logs.csv"), use_container_width=True)
