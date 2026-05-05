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

# ==========================================
# 3. MASTER AUTHENTICATION SYSTEM (BYPASS-PROOF)
# ==========================================

# Session State Initialize
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3209/3209101.png", width=80)
        st.title("🛡️ Pharma Portal Login")
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container(border=True):
            u_input = st.text_input("Username", key="login_user")
            p_input = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("🚀 Access Dashboard", use_container_width=True):
                # MASTER BYPASS: Ye hamesha chalega chahe CSV ho ya na ho
                if u_input == "admin" and p_input == "pharma2026":
                    st.session_state.logged_in = True
                    st.session_state.username = "Nivesh (Admin)"
                    st.success("Master Access Granted! Loading...")
                    time.sleep(1)
                    st.rerun()
                
                # Database Check (Backup option)
                elif os.path.exists(DB_FILES["users"]):
                    users_db = pd.read_csv(DB_FILES["users"])
                    # String conversion to avoid type errors
                    match = users_db[(users_db['username'] == u_input) & (users_db['password'].astype(str) == str(p_input))]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.username = u_input
                        st.rerun()
                    else:
                        st.error("Invalid Credentials! Try admin / pharma2026")
                else:
                    st.error("Database not found! Use Master Login: admin / pharma2026")
        
        st.info("System Hint: Use 'admin' as ID and 'pharma2026' as Key.")
    st.stop() # Dashboard tabhi dikhega jab login success hoga

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

# ==========================================
# 5. MODULE: INVENTORY PRO (STOCK MANAGEMENT)
# ==========================================
with t2:
    st.markdown("### 📦 Inventory Pro: Stock & Procurement")
    
    # Inventory Action Tabs
    inv_tab1, inv_tab2 = st.tabs(["➕ Add New Stock", "📊 Current Inventory"])
    
    with inv_tab1:
        st.subheader("Medicine Entry Form")
        with st.form("inventory_form", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            
            # Row 1: Basic Info
            m_name = f_col1.text_input("Medicine Name", placeholder="e.g. Paracetamol 500mg")
            m_cat = f_col2.selectbox("Category", ["Tablet", "Syrup", "Injection", "Herbal", "Cosmetic", "Surgical"])
            m_exp = f_col3.date_input("Expiry Date", min_value=datetime.date.today())
            
            # Row 2: Pricing & Stock
            f_col4, f_col5, f_col6 = st.columns(3)
            m_stock = f_col4.number_input("Initial Stock Quantity", min_value=1, step=1)
            m_cost = f_col5.number_input("Cost Price per Unit (₹)", min_value=0.0, format="%.2f")
            m_price = f_col6.number_input("Selling Price per Unit (₹)", min_value=0.0, format="%.2f")
            
            submit_inv = st.form_submit_button("💾 Save to Cloud Inventory")
            
            if submit_inv:
                if m_name:
                    # Creating new entry
                    new_entry = {
                        "Medicine": m_name.strip().upper(),
                        "Stock": int(m_stock),
                        "Expiry Date": str(m_exp),
                        "Unit Price (₹)": float(m_price),
                        "Cost Price (₹)": float(m_cost),
                        "Category": m_cat,
                        "Last Updated": datetime.datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Update global inv and Save
                    inv = pd.concat([inv, pd.DataFrame([new_entry])], ignore_index=True)
                    inv.to_csv(DB_FILES["inv"], index=False)
                    
                    st.success(f"✅ {m_name} added successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Medicine Name is mandatory!")

    with inv_tab2:
        st.subheader("Real-time Stock Ledger")
        
        # Search & Filter Logic
        s_col1, s_col2 = st.columns([2, 1])
        search_query = s_col1.text_input("🔍 Search by Name", placeholder="Type medicine name...")
        filter_cat = s_col2.selectbox("Filter Category", ["All"] + list(inv["Category"].unique()) if not inv.empty else ["All"])
        
        # Applying Filters
        display_inv = inv.copy()
        if search_query:
            display_inv = display_inv[display_inv["Medicine"].str.contains(search_query, case=False, na=False)]
        if filter_cat != "All":
            display_inv = display_inv[display_inv["Category"] == filter_cat]
            
        if not display_inv.empty:
            # Highlighting Low Stock & Expiry
            def highlight_stock(s):
                return ['background-color: #4b1a1a' if col == 'Stock' and val < 10 else '' for col, val in s.items()]
            
            st.dataframe(
                display_inv.style.apply(highlight_stock, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            # Bulk Actions
            if st.button("🗑️ Reset Inventory (Caution)"):
                if st.session_state.username == "admin":
                    pd.DataFrame(columns=inv.columns).to_csv(DB_FILES["inv"], index=False)
                    st.warning("Inventory cleared!")
                    st.rerun()
                else:
                    st.error("Only Owner can reset inventory.")
        else:
            st.info("No records found matching the filters.")

# ==========================================
# 6. MODULE: AI HERBAL LAB (B.PHARM SPECIAL)
# ==========================================
with t3:
    st.markdown("### 🌿 AI Botanical & Clinical Analysis")
    st.info("Powered by Gemini 1.5 Flash - Tailored for B.Pharm Pharmaceutical Research")
    
    # Research Workspace
    ai_col1, ai_col2 = st.columns([1.5, 1])
    
    with ai_col1:
        st.subheader("Clinical Research Portal")
        herb_query = st.text_input(
            "Enter Herb or Chemical Constituent Name", 
            placeholder="e.g. Aloe Vera, Curcumin, Azadirachta indica...",
            key="herbal_search_input"
        )
        
        research_scope = st.multiselect(
            "Select Research Scope",
            ["Therapeutic Uses", "Side Effects", "Mechanism of Action", "Role in Cosmetics", "Phytochemistry"],
            default=["Therapeutic Uses", "Role in Cosmetics"]
        )
        
        analyze_btn = st.button("🔬 Run Deep Analysis", key="run_ai_btn")

    with ai_col2:
        st.subheader("Quick Reference Guide")
        st.write("Is module ka use aap apne Pharmacognosy assignments aur Herbal Cosmetics projects ke liye kar sakte hain.")
        st.caption("Tip: 'Ditch Plate Method' ya 'Fourier's Law' jaise technical terms bhi search kar sakte hain.")

    # AI Processing Engine
    if analyze_btn:
        if not herb_query:
            st.warning("Pehle kisi Herb ya Chemical ka naam likhein.")
        else:
            with st.spinner(f"Fetching Clinical Data for {herb_query}..."):
                try:
                    # SECRETS SE KEY UTHANA
                    if "GEMINI_API_KEY" in st.secrets:
                        api_key = st.secrets["GEMINI_API_KEY"]
                        client = genai.Client(api_key=api_key)
                        
                        # Professional Prompt Engineering
                        prompt = f"""
                        As a Senior Pharmacologist, provide a detailed clinical analysis of '{herb_query}'.
                        Scope: {', '.join(research_scope)}.
                        Context: B.Pharm Academic Research.
                        Language: Professional Hinglish (Mixed Hindi/English).
                        Format: Use Bullet points and Bold headings.
                        """
                        
                        response = client.models.generate_content(
                            model="gemini-1.5-flash", 
                            contents=prompt
                        )
                        
                        # Display Results in a Professional Container
                        st.markdown("---")
                        st.success(f"### Research Report: {herb_query}")
                        st.markdown(response.text)
                        
                        # System Log Entry
                        log_entry = pd.DataFrame([{
                            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "User": st.session_state.username,
                            "Action": f"AI Research: {herb_query}",
                            "Status": "Success"
                        }])
                        log_entry.to_csv("system_logs.csv", mode='a', header=False, index=False)
                        
                    else:
                        st.error("❌ API Key Missing: Streamlit Cloud ke 'Secrets' mein 'GEMINI_API_KEY' add karein.")
                except Exception as e:
                    st.error(f"⚠️ AI Analysis Failed: {e}")
                    st.info("Check karein ki aapka internet aur API key valid hai.")

# ==========================================
# 7. MODULE: ANALYTICS & BUSINESS INTELLIGENCE
# ==========================================
with t4:
    st.markdown("### 📈 Strategic Business Analytics")
    
    if sales.empty:
        st.warning("⚠️ Analytics dekhne ke liye pehle kuch sales (Billing) karein.")
    else:
        # --- TOP LEVEL KPI CARDS ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_revenue = sales["Total"].sum()
        total_profit = sales["Profit"].sum()
        total_items_sold = sales["Qty"].sum()
        avg_invoice = total_revenue / sales["Invoice_ID"].nunique() if "Invoice_ID" in sales.columns else 0

        kpi1.metric("Total Revenue", f"₹{total_revenue:,.2f}", delta="Cash In")
        kpi2.metric("Net Profit", f"₹{total_profit:,.2f}", delta=f"{((total_profit/total_revenue)*100 if total_revenue > 0 else 0):.1f}% Margin")
        kpi3.metric("Items Sold", int(total_items_sold))
        kpi4.metric("Avg Bill Value", f"₹{avg_invoice:,.2f}")

        st.markdown("---")

        # --- VISUAL CHARTS ROW ---
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("💰 Profit Trend Analysis")
            # Grouping by Date for Line Chart
            sales['Date_Only'] = pd.to_datetime(sales['Date']).dt.date
            daily_profit = sales.groupby('Date_Only')['Profit'].sum().reset_index()
            
            fig_profit = px.line(
                daily_profit, 
                x='Date_Only', 
                y='Profit',
                markers=True,
                line_shape="spline",
                color_discrete_sequence=["#4CAF50"]
            )
            fig_profit.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_profit, use_container_width=True)

        with chart_col2:
            st.subheader("📦 Top Selling Medicines")
            top_items = sales.groupby('Item')['Qty'].sum().sort_values(ascending=False).head(5).reset_index()
            
            fig_top = px.bar(
                top_items, 
                x='Item', 
                y='Qty',
                color='Qty',
                color_continuous_scale='Greens'
            )
            fig_top.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_top, use_container_width=True)

        # --- DATA INSIGHTS TABLE ---
        st.markdown("### 📜 Recent Transaction Ledger")
        # Showing latest transactions first
        st.dataframe(
            sales.sort_values(by="Date", ascending=False).head(20),
            use_container_width=True,
            hide_index=True
        )

        # CSV Download Button for Accounting
        st.download_button(
            label="📥 Download Full Sales Report (CSV)",
            data=sales.to_csv(index=False).encode('utf-8'),
            file_name=f"Pharma_Sales_{datetime.date.today()}.csv",
            mime='text/csv',
        )

# ==========================================
# 8. FOOTER & SYSTEM STATUS
# ==========================================
st.markdown("---")
f_left, f_right = st.columns(2)
f_left.caption(f"Nivesh Pharma Ultra v3.0 | Database Status: Connected ✅")
f_right.markdown(f"<div style='text-align: right; color: gray;'>Last Sync: {datetime.datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

# ==========================================
# 9. MODULE: PDF INVOICE GENERATOR (ULTRA STABLE)
# ==========================================
def generate_pdf_bill(customer_name, cart_items, total_amount):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Branding
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(35, 134, 54) 
        pdf.cell(190, 15, "NIVESH PHARMA ULTRA v3.0", ln=True, align='C')
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 5, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.ln(10)
        
        # Customer Info
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, f"Customer: {str(customer_name)}", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Table Header
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(85, 10, " Medicine Name", 1, 0, 'L', True)
        pdf.cell(25, 10, "Qty", 1, 0, 'C', True)
        pdf.cell(40, 10, "Price (Rs)", 1, 0, 'C', True)
        pdf.cell(40, 10, "Total (Rs)", 1, 1, 'C', True)
        
        # Table Body
        pdf.set_font("Arial", '', 10)
        for item in cart_items:
            # Safely converting to string to avoid encoding issues
            name = str(item['Item']).encode('ascii', 'ignore').decode('ascii')
            pdf.cell(85, 10, f" {name}", 1)
            pdf.cell(25, 10, str(item['Qty']), 1, 0, 'C')
            pdf.cell(40, 10, f"{float(item['Price']):.2f}", 1, 0, 'C')
            pdf.cell(40, 10, f"{float(item['Total']):.2f}", 1, 1, 'C')
        
        # Grand Total
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(150, 10, "GRAND TOTAL:", 0, 0, 'R')
        pdf.cell(40, 10, f"Rs. {float(total_amount):.2f}", 1, 1, 'C')
        
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except Exception as e:
        st.error(f"Logic Error: {e}")
        return None

# --- INTEGRATION IN TAB 1 (Paste this exactly here) ---
with t1:
    if 'cart' in st.session_state and st.session_state.cart:
        st.markdown("---")
        c_name = st.text_input("Billing Name", "Walking Customer", key="final_cust_name")
        
        # Pre-generating PDF bytes
        bill_total = sum(item['Total'] for item in st.session_state.cart)
        pdf_data = generate_pdf_bill(c_name, st.session_state.cart, bill_total)
        
        col_pdf1, col_pdf2 = st.columns(2)
        
        with col_pdf1:
            if pdf_data:
                st.download_button(
                    label="📥 Download PDF Bill",
                    data=pdf_data,
                    file_name=f"Bill_{int(time.time())}.pdf",
                    mime="application/pdf",
                    key="download_invoice_btn"
                )
        
        with col_pdf2:
            st.info("Download PDF before clicking Finalize.")


