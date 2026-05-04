import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from google import genai
from fpdf import FPDF
import streamlit as st
import pandas as pd
import os

# --- CONFIG ---
st.set_page_config(page_title="Nivesh Pharma SaaS", layout="wide")

USER_DB = "users.csv"

# User database initialize karna
if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["username", "password", "email"]).to_csv(USER_DB, index=False)

def load_users():
    return pd.read_csv(USER_DB)

# --- LOGIN / SIGNUP UI ---
def auth_page():
    st.markdown("""
        <style>
        .auth-container {
            background-color: #1e1e1e;
            padding: 30px;
            border-radius: 15px;
            border: 1px solid #4CAF50;
            text-align: center;
        }
        .social-btn {
            display: inline-block;
            margin: 5px;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            color: white;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    _, col2, _ = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        mode = st.radio("Choose Action", ["Login", "Sign Up"], horizontal=True)
        
        if mode == "Sign Up":
            st.subheader("Create New Account")
            new_user = st.text_input("Username")
            new_email = st.text_input("Email (Gmail/Yahoo/etc.)")
            new_pw = st.text_input("Password", type="password")
            
            if st.button("Register"):
                users = load_users()
                if new_user in users['username'].values:
                    st.error("User pehle se hai!")
                else:
                    new_entry = pd.DataFrame([{"username": new_user, "password": new_pw, "email": new_email}])
                    new_entry.to_csv(USER_DB, mode='a', header=False, index=False)
                    st.success("Account ban gaya! Ab Login karein.")
        
        else:
            st.subheader("Welcome Back")
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            
            if st.button("Login"):
                users = load_users()
                if user in users['username'].values and str(pw) == str(users[users['username'] == user]['password'].values[0]):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Invalid credentials!")

        st.markdown("---")
        st.write("Or Continue with:")
        # Professional UI Buttons
        st.markdown("""
            <a href="#" class="social-btn" style="background-color: #db4437;">Google</a>
            <a href="#" class="social-btn" style="background-color: #720e9e;">Yahoo</a>
            <a href="#" class="social-btn" style="background-color: #0078d4;">Outlook</a>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Session management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    auth_page()
    st.stop()

# --- AGAR LOGIN HO GAYA TOH DASHBOARD ---
st.sidebar.success(f"Logged in as: {st.session_state.username}")
if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.rerun()

# Yahan aapka pura purana dashboard code paste hoga (Tabs, Billing, etc.)

# --- CONFIGURATION ---
st.set_page_config(page_title="Nivesh Pharma Ultra", layout="wide", page_icon="🚀")

DATA_FILE = "inventory.csv"
SALES_FILE = "sales_history.csv"

# --- DATABASE SETUP ---
def init_db():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        pd.DataFrame(columns=["Medicine", "Stock", "Expiry Date", "Unit Price (₹)", "Category"]).to_csv(DATA_FILE, index=False)
    if not os.path.exists(SALES_FILE) or os.stat(SALES_FILE).st_size == 0:
        pd.DataFrame(columns=["Date", "Item", "Qty", "Total", "GST"]).to_csv(SALES_FILE, index=False)

init_db()

# --- API SETUP ---
client = genai.Client(api_key="YOUR_ACTUAL_API_KEY_HERE")

# --- UTILITY FUNCTIONS ---
def load_df(file):
    return pd.read_csv(file)

def save_df(df, file):
    df.to_csv(file, index=False)

def create_pdf(items, subtotal, gst, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "NIVESH PHARMA - INVOICE", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(10)
    
    # Table Header
    pdf.cell(80, 10, "Item", border=1)
    pdf.cell(30, 10, "Qty", border=1)
    pdf.cell(40, 10, "Price", border=1)
    pdf.cell(40, 10, "Total", border=1, ln=True)
    
    for item in items:
        pdf.cell(80, 10, item['Item'], border=1)
        pdf.cell(30, 10, str(item['Qty']), border=1)
        pdf.cell(40, 10, str(item['Price']), border=1)
        pdf.cell(40, 10, str(item['Total']), border=1, ln=True)
    
    pdf.ln(10)
    pdf.cell(200, 10, f"Subtotal: Rs. {subtotal}", ln=True)
    pdf.cell(200, 10, f"GST (12%): Rs. {round(gst, 2)}", ln=True)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"Grand Total: Rs. {round(total, 2)}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- UI START ---
st.title("💊 Nivesh Pharma Pro Dashboard")

# Quick Alerts Row
inv = load_df(DATA_FILE)
if not inv.empty:
    # Purani line ko isse badlo:
    inv['Expiry Date'] = pd.to_datetime(inv['Expiry Date'], errors='coerce')
    days_left = (inv['Expiry Date'] - datetime.datetime.now()).dt.days
    low_stock = inv[inv['Stock'] < 10]
    near_expiry = inv[(days_left < 60) & (days_left > 0)]

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Items", len(inv))
    with c2: st.metric("Low Stock Alerts", len(low_stock), delta="-Action Required", delta_color="inverse")
    with c3: st.metric("Near Expiry", len(near_expiry), delta="Check Inventory", delta_color="off")

st.markdown("---")
t1, t2, t3, t4 = st.tabs(["🛒 Smart Billing", "📦 Inventory Hub", "🌿 Herbal AI Expert", "📊 Business Insights"])

# --- TAB 1: SMART BILLING ---
with t1:
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("Fast Billing")
        if not inv.empty:
            med = st.selectbox("Select Med", inv[inv["Stock"] > 0]["Medicine"])
            stock_avail = int(inv[inv["Medicine"] == med]["Stock"].values[0])
            qty = st.number_input("Qty", 1, stock_avail)
            if st.button("➕ Add to Cart"):
                if 'cart' not in st.session_state: st.session_state.cart = []
                price = inv[inv["Medicine"] == med]["Unit Price (₹)"].values[0]
                st.session_state.cart.append({"Item": med, "Qty": qty, "Price": price, "Total": qty*price})
    
    with col_b:
        st.subheader("Invoice Summary")
        if 'cart' in st.session_state and st.session_state.cart:
            bill_df = pd.DataFrame(st.session_state.cart)
            st.dataframe(bill_df, use_container_width=True)
            sub = bill_df["Total"].sum()
            gst = sub * 0.12
            total = sub + gst
            
            st.write(f"**Total Amount: ₹{round(total, 2)}**")
            
            if st.button("🚀 Finalize & Generate PDF"):
                # Stock Update
                for item in st.session_state.cart:
                    inv.loc[inv["Medicine"] == item["Item"], "Stock"] -= item["Qty"]
                save_df(inv, DATA_FILE)
                
                # PDF Download
                pdf_bytes = create_pdf(st.session_state.cart, sub, gst, total)
                st.download_button("📥 Download Invoice PDF", pdf_bytes, "bill.pdf", "application/pdf")
                st.session_state.cart = []
                st.success("Sale Recorded!")

# --- TAB 2: INVENTORY ---
with t2:
    st.subheader("Manage Stock")
    with st.expander("Add New Product"):
        with st.form("inv_form"):
            n = st.text_input("Med Name")
            s = st.number_input("Qty", 0)
            p = st.number_input("Price", 0.0)
            e = st.date_input("Expiry")
            cat = st.selectbox("Type", ["Tablet", "Syrup", "Herbal Cosmetic", "General"])
            if st.form_submit_button("Save"):
                new_data = pd.DataFrame([{"Medicine":n, "Stock":s, "Expiry Date":str(e), "Unit Price (₹)":p, "Category":cat}])
                save_df(pd.concat([inv, new_data], ignore_index=True), DATA_FILE)
                st.rerun()
    st.dataframe(inv, use_container_width=True)

# --- TAB 3: HERBAL AI (Semester Project Special) ---
with t3:
    st.subheader("🌿 Herbal & Cosmetic Ingredient AI")
    h_query = st.text_input("Enter Herb or Product Name (e.g., Aloe Vera, Niacinamide):")
    if h_query:
        with st.spinner("AI analyzing chemical/herbal properties..."):
            try:
                prompt = f"""
                Research Herb/Chemical: {h_query}
                1. Role in Cosmetics (Skin benefits/properties).
                2. Clinical Pharmacy View (Mechanism of action).
                3. Safety Rating & Toxicity (Side effects).
                4. Potential substitutes in Herbal formulations.
                Format: Professional clinical report in Hinglish.
                """
                resp = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.info(resp.text)
            except: st.error("AI Limit. Wait 1 min.")

# --- TAB 4: ANALYTICS ---
# --- TAB 4: BUSINESS INSIGHTS (UPGRADED) ---
with t4:
    st.header("📈 Business Intelligence & Sales Analytics")
    sales = load_df(SALES_FILE)
    
    if not sales.empty and len(sales) > 0:
        # Metrics Row
        total_rev = sales["Total"].sum()
        total_gst = sales["GST"].sum()
        avg_bill = total_rev / len(sales)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Revenue", f"₹{round(total_rev, 2)}", "Growth")
        m2.metric("GST Collected", f"₹{round(total_gst, 2)}")
        m3.metric("Avg Bill Value", f"₹{round(avg_bill, 2)}")
        
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Sales over time
            fig_line = px.line(sales, x="Date", y="Total", title="Daily Revenue Trend", 
                               markers=True, template="plotly_dark", color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col_g2:
            # Best selling products
            top_products = sales.groupby("Item")["Qty"].sum().reset_index()
            fig_pie = px.pie(top_products, names="Item", values="Qty", title="Product Sales Distribution",
                             hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.subheader("📋 Recent Transactions")
        st.dataframe(sales.sort_values(by="Date", ascending=False), use_container_width=True)
        
    else:
        # Jab data na ho toh ye dikhayega
        st.info("Bhai, abhi tak koi sale nahi hui hai. Pehle 'Smart Billing' tab mein jaakar ek bill generate karo!")
        st.image("https://cdn-icons-png.flaticon.com/512/4076/4076402.png", width=100) # Empty state icon
        
        # Ek sample button demo dekhne ke liye
        if st.button("Click here to see how it looks with Sample Data"):
            sample_data = pd.DataFrame([
                {"Date": "2026-05-01 10:00", "Item": "Paracetamol", "Qty": 5, "Total": 100, "GST": 12},
                {"Date": "2026-05-02 14:30", "Item": "Metformin", "Qty": 10, "Total": 240, "GST": 28.8},
                {"Date": "2026-05-04 09:15", "Item": "Aloe Vera Gel", "Qty": 2, "Total": 500, "GST": 60}
            ])
            st.plotly_chart(px.bar(sample_data, x="Date", y="Total", color="Item", title="Sample Sales Trend"))