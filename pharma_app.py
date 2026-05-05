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
    # Files initialize karna agar nahi hain
    if not os.path.exists(DB_FILES["inv"]):
        pd.DataFrame(columns=["Medicine", "Stock", "Expiry Date", "Unit Price (₹)", "Cost Price (₹)", "Category"]).to_csv(DB_FILES["inv"], index=False)
    
    if not os.path.exists(DB_FILES["sales"]):
        pd.DataFrame(columns=["Date", "Item", "Qty", "Total", "Profit", "User"]).to_csv(DB_FILES["sales"], index=False)

    # --- USERS FILE REPAIR LOGIC ---
    if not os.path.exists(DB_FILES["users"]):
        # Nayi file banayein agar exist nahi karti
        pd.DataFrame([{"username": "admin", "password": "pharma2026", "role": "Owner"}]).to_csv(DB_FILES["users"], index=False)
    else:
        try:
            # File check karein ki read ho rahi hai ya nahi
            pd.read_csv(DB_FILES["users"])
        except:
            # Agar file corrupt hai (ParserError), toh use overwrite karke reset kar dein
            pd.DataFrame([{"username": "admin", "password": "pharma2026", "role": "Owner"}]).to_csv(DB_FILES["users"], index=False)

    inv = pd.read_csv(DB_FILES["inv"])
    sales = pd.read_csv(DB_FILES["sales"])
    
    # Baaki numeric conversion code...
    return inv, sales

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

# ==========================================
# 4. GLOBAL PDF GENERATOR (WITH GST)
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

# --- DASHBOARD STARTS ---
st.title(f"🚀 Nivesh Pharma Ultra (User: {st.session_state.username})")
t1, t2, t3, t4 = st.tabs(["🛒 Super POS", "📦 Inventory Pro", "🌿 AI Herbal Lab", "📈 Analytics"])

# ==========================================
# 5. MODULE: ADVANCED POS SYSTEM
# ==========================================
with t1:
    if 'cart' not in st.session_state: st.session_state.cart = []
    pos_l, pos_r = st.columns([1, 1.2])
    with pos_l:
        st.subheader("Quick Billing")
        if not inv.empty:
            med_list = inv["Medicine"].unique()
            selected_med = st.selectbox("Search Medicine", med_list)
            m_data = inv[inv["Medicine"] == selected_med].iloc[0]
            stock_left = int(m_data["Stock"])
            if stock_left < 10: st.warning(f"⚠️ Low Stock: {stock_left} left!")
            c1, c2 = st.columns(2)
            u_price = c1.number_input("Unit Price (₹)", value=float(m_data["Unit Price (₹)"]), disabled=True)
            sel_qty = c2.number_input("Quantity", 1, max(1, stock_left), step=1)
            if st.button("➕ Add to Invoice"):
                st.session_state.cart.append({"Item": selected_med, "Qty": int(sel_qty), "Price": float(u_price), "Cost": float(m_data["Cost Price (₹)"]), "Total": float(sel_qty * u_price)})
                st.rerun()
    with pos_r:
        st.subheader("Invoice Summary")
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
                st.session_state.cart = []; st.success("Sale Recorded!"); st.rerun()

# ==========================================
# 6. MODULE: INVENTORY PRO
# ==========================================
with t2:
    st.markdown("### 📦 Inventory Pro")
    inv_tab1, inv_tab2 = st.tabs(["➕ Add New Stock", "📊 Current Inventory"])
    with inv_tab1:
        with st.form("inventory_form", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            m_name = f_col1.text_input("Medicine Name")
            m_cat = f_col2.selectbox("Category", ["Tablet", "Syrup", "Injection", "Herbal"])
            m_exp = f_col3.date_input("Expiry Date")
            f_col4, f_col5, f_col6 = st.columns(3)
            m_stock = f_col4.number_input("Stock Quantity", min_value=1)
            m_cost = f_col5.number_input("Cost Price (₹)", min_value=0.0)
            m_price = f_col6.number_input("Selling Price (₹)", min_value=0.0)
            if st.form_submit_button("Save Stock"):
                new_entry = {"Medicine": m_name.upper(), "Stock": int(m_stock), "Expiry Date": str(m_exp), "Unit Price (₹)": float(m_price), "Cost Price (₹)": float(m_cost), "Category": m_cat}
                inv = pd.concat([inv, pd.DataFrame([new_entry])], ignore_index=True)
                inv.to_csv(DB_FILES["inv"], index=False); st.success("Stock Added!"); st.rerun()
    with inv_tab2:
        st.dataframe(inv, use_container_width=True)

# ==========================================
# 7. MODULE: AI HERBAL LAB
# ==========================================
with t3:
    st.markdown("### 🌿 AI Botanical Analysis")
    herb_query = st.text_input("Enter Herb or Chemical Name")
    if st.button("🔬 Run Analysis"):
        if "GEMINI_API_KEY" in st.secrets:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            response = client.models.generate_content(model="gemini-1.5-flash", contents=f"Detail B.Pharm report for {herb_query} in Hinglish.")
            st.markdown(response.text)
        else: st.error("GEMINI_API_KEY missing in Streamlit Secrets!")

# ==========================================
# 8. MODULE: ANALYTICS
# ==========================================
with t4:
    st.markdown("### 📈 Business Analytics")
    if not sales.empty:
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Revenue", f"₹{sales['Total'].sum():,.2f}")
        kpi2.metric("Net Profit", f"₹{sales['Profit'].sum():,.2f}")
        kpi3.metric("Sales Count", len(sales))
        st.plotly_chart(px.bar(sales.groupby('Item')['Qty'].sum().reset_index(), x='Item', y='Qty', title="Sales by Item"))
    else: st.info("No sales data recorded yet.")

# ==========================================
# 9. SIDEBAR: ADMIN TOOLS, BACKUP & LOGOUT
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3209/3209101.png", width=50)
    st.title("Control Panel")
    st.write(f"Logged in as: **{st.session_state.username}**")
    
    st.markdown("---")
    st.subheader("🛠️ Management Tools")
    
    # 1. View Logs Toggle
    if st.button("📁 View System Activity", use_container_width=True):
        st.session_state.show_logs = not st.session_state.get('show_logs', False)

    st.markdown("---")
    st.subheader("💾 Emergency Backup")
    st.caption("Download data as CSV files")
    
    # Inventory Backup Button
    st.download_button(
        "📥 Backup Inventory",
        data=inv.to_csv(index=False).encode('utf-8'),
        file_name=f"Backup_Inv_{datetime.date.today()}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Sales Backup Button
    st.download_button(
        "📥 Backup Sales",
        data=sales.to_csv(index=False).encode('utf-8'),
        file_name=f"Backup_Sales_{datetime.date.today()}.csv",
        mime="text/csv",
        use_container_width=True
    )

    # User Database Backup (Only for Admin)
    if st.session_state.username == "Nivesh (Admin)":
        if os.path.exists(DB_FILES["users"]):
            st.download_button(
                "👤 Backup Users DB",
                data=pd.read_csv(DB_FILES["users"]).to_csv(index=False).encode('utf-8'),
                file_name=f"Backup_Users_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("---")
    # 3. Secure Logout Button
    if st.button("🔴 Secure Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        
    st.caption(f"v3.0.1 Stable | Nivesh Pharma Enterprise")

# --- Logs Display Logic (Dashboard ke bilkul niche) ---
if st.session_state.get('show_logs', False):
    st.markdown("---")
    st.subheader("🕵️ Enterprise Audit Logs")
    if os.path.exists("system_logs.csv"):
        logs_df = pd.read_csv("system_logs.csv")
        st.dataframe(logs_df.sort_values(by="Timestamp", ascending=False).head(50), use_container_width=True)
    else:
        st.info("System logs are currently empty.")
