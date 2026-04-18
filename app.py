import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from datetime import datetime, timedelta
import os

# ─────────────────────────────────────────────
#  DB CONNECTION & SETUP
# ─────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect('o2c.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS materials (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 100
        );
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            material_id INTEGER,
            quantity    INTEGER,
            total       REAL,
            status      TEXT DEFAULT 'Created',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER UNIQUE,
            amount     REAL,
            paid_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            method     TEXT
        );
    """)
    conn.commit()

conn = get_conn()
init_db(conn)

# ─────────────────────────────────────────────
#  PAGE CONFIG & GLOBAL CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="SAP O2C System", layout="wide", page_icon="🔷")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    color: #e0e8ff;
}
.stApp {
    background: radial-gradient(ellipse at 20% 50%, #0a0e2e 0%, #050818 60%, #0a0e2e 100%);
    background-attachment: fixed;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060c2a 0%, #0d1544 100%);
    border-right: 1px solid rgba(0,200,255,0.15);
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] p {
    color: #7aaeff !important;
    font-family: 'Rajdhani', sans-serif;
    font-size: 13px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ── Headings ── */
h1 { font-family: 'Orbitron', monospace !important; color: #00c8ff !important; letter-spacing: 3px; font-size: 1.6rem !important; }
h2 { font-family: 'Orbitron', monospace !important; color: #7aaeff !important; letter-spacing: 2px; font-size: 1.1rem !important; }
h3 { font-family: 'Rajdhani', sans-serif !important; color: #a0c4ff !important; letter-spacing: 1px; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(0,200,255,0.06) 0%, rgba(100,50,255,0.08) 100%);
    border: 1px solid rgba(0,200,255,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px rgba(0,200,255,0.05), inset 0 1px 0 rgba(255,255,255,0.05);
}
[data-testid="metric-container"] label {
    color: #7aaeff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 12px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #00c8ff !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 1.5rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(0,200,255,0.15), rgba(100,50,255,0.2));
    border: 1px solid rgba(0,200,255,0.4);
    color: #00c8ff;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    border-radius: 6px;
    padding: 8px 24px;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0,200,255,0.3), rgba(100,50,255,0.35));
    border-color: #00c8ff;
    box-shadow: 0 0 20px rgba(0,200,255,0.3);
    color: #ffffff;
}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input {
    background: rgba(0,200,255,0.05) !important;
    border: 1px solid rgba(0,200,255,0.2) !important;
    border-radius: 6px !important;
    color: #e0e8ff !important;
    font-family: 'Rajdhani', sans-serif !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #00c8ff !important;
    box-shadow: 0 0 10px rgba(0,200,255,0.2) !important;
}
.stSelectbox > div > div {
    background: rgba(0,200,255,0.05) !important;
    border: 1px solid rgba(0,200,255,0.2) !important;
    border-radius: 6px !important;
    color: #e0e8ff !important;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid rgba(0,200,255,0.15);
    border-radius: 10px;
    overflow: hidden;
}

/* ── Divider ── */
hr { border-color: rgba(0,200,255,0.1) !important; }

/* ── Success / Error / Warning ── */
.stSuccess { background: rgba(0,255,150,0.08) !important; border: 1px solid rgba(0,255,150,0.3) !important; border-radius: 8px !important; }
.stError   { background: rgba(255,50,80,0.08)  !important; border: 1px solid rgba(255,50,80,0.3)  !important; border-radius: 8px !important; }
.stWarning { background: rgba(255,180,0,0.08)  !important; border: 1px solid rgba(255,180,0,0.3)  !important; border-radius: 8px !important; }

/* ── Pipeline banner ── */
.pipeline {
    display: flex; align-items: center; gap: 6px;
    margin: 12px 0 20px 0;
}
.pip-step {
    padding: 5px 16px;
    border-radius: 20px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 13px; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase;
}
.pip-active   { background: rgba(0,200,255,0.2); border: 1px solid #00c8ff; color: #00c8ff; }
.pip-done     { background: rgba(0,255,150,0.15); border: 1px solid #00ff96; color: #00ff96; }
.pip-inactive { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); color: rgba(255,255,255,0.3); }
.pip-arrow    { color: rgba(0,200,255,0.4); font-size: 16px; }

/* ── Status badge ── */
.badge-created   { background:rgba(255,180,0,0.15);  border:1px solid #ffb400; color:#ffb400;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-delivered { background:rgba(0,150,255,0.15);  border:1px solid #0096ff; color:#0096ff;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-completed { background:rgba(0,255,150,0.15);  border:1px solid #00ff96; color:#00ff96;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-paid      { background:rgba(180,0,255,0.15);  border:1px solid #b400ff; color:#b400ff;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }

/* ── Glass card ── */
.glass-card {
    background: linear-gradient(135deg, rgba(0,200,255,0.06), rgba(100,50,255,0.06));
    border: 1px solid rgba(0,200,255,0.15);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 30px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04);
}

/* ── Section label ── */
.section-label {
    font-family:'Orbitron',monospace; font-size:10px; color:#00c8ff;
    letter-spacing:3px; text-transform:uppercase; margin-bottom:4px;
    padding-bottom:4px; border-bottom:1px solid rgba(0,200,255,0.2);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h1 style='font-size:1.1rem;margin-bottom:0'>🔷 SAP O2C</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:10px;color:#3a5080;margin-top:0;letter-spacing:2px'>SIMULATION SYSTEM v2.0</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div class='section-label'>⚡ Master Data</div>", unsafe_allow_html=True)
    menu = st.selectbox("", [
        "╰› Dashboard",
        "╰› Add Customer",
        "╰› Add Material",
        "╰› Load Sample Data",
        "─────────────────",
        "╰› Create Order",
        "╰› Delivery",
        "╰› Billing",
        "╰› Record Payment",
        "─────────────────",
        "╰› View All Orders",
    ], label_visibility="collapsed")

st.markdown("<h1>🔷 SAP ORDER-TO-CASH SYSTEM</h1>", unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def pipeline_html(active):
    steps = ["Created", "Delivered", "Billed", "Paid"]
    idx   = steps.index(active) if active in steps else -1
    parts = []
    for i, s in enumerate(steps):
        if i < idx:   cls = "pip-done"
        elif i == idx: cls = "pip-active"
        else:          cls = "pip-inactive"
        parts.append(f"<span class='pip-step {cls}'>{s}</span>")
        if i < len(steps)-1:
            parts.append("<span class='pip-arrow'>›</span>")
    return "<div class='pipeline'>" + "".join(parts) + "</div>"

def badge(status):
    cls = f"badge-{status.lower()}"
    return f"<span class='{cls}'>{status}</span>"

def fmt_inr(val):
    return f"₹{val:,.0f}"

def plotly_defaults(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Rajdhani, sans-serif", color="#a0c4ff"),
        title_font=dict(family="Orbitron, monospace", color="#00c8ff", size=13),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,200,255,0.1)"),
        xaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False),
        yaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig

NEON = ["#00c8ff", "#7b5cff", "#00ff96", "#ff6b6b", "#ffd166", "#ff9f43"]

# ─────────────────────────────────────────────
#  LOAD SAMPLE DATA
# ─────────────────────────────────────────────
if menu == "╰› Load Sample Data":
    st.markdown("## ╰› Load Sample Data")
    st.info("This will wipe existing records and load fresh demo data.")
    if st.button("⚡ Load Demo Data"):
        conn.execute("DELETE FROM payments")
        conn.execute("DELETE FROM orders")
        conn.execute("DELETE FROM customers")
        conn.execute("DELETE FROM materials")
        conn.executemany("INSERT INTO customers (name,email,phone) VALUES (?,?,?)", [
            ("Rahul Sharma",  "rahul@gmail.com",  "9876543210"),
            ("Priya Mehta",   "priya@gmail.com",  "9123456789"),
            ("Amit Verma",    "amit@gmail.com",   "9988776655"),
            ("Sneha Reddy",   "sneha@gmail.com",  "9765432109"),
            ("Karan Malhotra","karan@gmail.com",  "9654321098"),
        ])
        conn.executemany("INSERT INTO materials (name,price,stock) VALUES (?,?,?)", [
            ("Laptop",     55000, 20),
            ("Smartphone", 25000, 50),
            ("Tablet",     30000, 30),
            ("Headphones",  3000, 100),
            ("Monitor",    15000, 25),
        ])
        conn.commit()
        st.success("✅ Sample data loaded successfully!")

# ─────────────────────────────────────────────
#  ADD CUSTOMER
# ─────────────────────────────────────────────
elif menu == "╰› Add Customer":
    st.markdown("## ╰› Add New Customer")
    st.markdown(pipeline_html("Created"), unsafe_allow_html=True)
    with st.form("add_customer"):
        c1, c2 = st.columns(2)
        name  = c1.text_input("Full Name")
        email = c2.text_input("Email Address")
        phone = st.text_input("Phone Number")
        submitted = st.form_submit_button("➕ Add Customer")

    if submitted:
        if not name.strip():
            st.error("❌ Name cannot be empty.")
        elif not email.strip() or "@" not in email:
            st.error("❌ Enter a valid email address.")
        elif not phone.strip() or not phone.strip().isdigit() or len(phone.strip()) != 10:
            st.error("❌ Phone must be a 10-digit number.")
        else:
            try:
                conn.execute("INSERT INTO customers (name,email,phone) VALUES (?,?,?)",
                             (name.strip(), email.strip(), phone.strip()))
                conn.commit()
                st.success(f"✅ Customer **{name}** added successfully!")
            except sqlite3.IntegrityError:
                st.error("❌ A customer with this email already exists.")

# ─────────────────────────────────────────────
#  ADD MATERIAL
# ─────────────────────────────────────────────
elif menu == "╰› Add Material":
    st.markdown("## ╰› Add New Material")
    with st.form("add_material"):
        c1, c2, c3 = st.columns(3)
        name  = c1.text_input("Material Name")
        price = c2.number_input("Unit Price (₹)", min_value=0.0, step=100.0)
        stock = c3.number_input("Initial Stock (units)", min_value=0, step=1)
        submitted = st.form_submit_button("➕ Add Material")

    if submitted:
        if not name.strip():
            st.error("❌ Material name cannot be empty.")
        elif price <= 0:
            st.error("❌ Price must be greater than ₹0.")
        elif stock < 0:
            st.error("❌ Stock cannot be negative.")
        else:
            conn.execute("INSERT INTO materials (name,price,stock) VALUES (?,?,?)",
                         (name.strip(), price, int(stock)))
            conn.commit()
            st.success(f"✅ Material **{name}** added with stock of **{int(stock)} units**.")

# ─────────────────────────────────────────────
#  CREATE ORDER
# ─────────────────────────────────────────────
elif menu == "╰› Create Order":
    st.markdown("## ╰› Create Sales Order")
    st.markdown(pipeline_html("Created"), unsafe_allow_html=True)

    customers = pd.read_sql("SELECT * FROM customers", conn)
    materials = pd.read_sql("SELECT * FROM materials", conn)

    if customers.empty:
        st.warning("⚠️ No customers found. Please add customers first.")
    elif materials.empty:
        st.warning("⚠️ No materials found. Please add materials first.")
    else:
        with st.form("create_order"):
            c1, c2, c3 = st.columns(3)
            cname = c1.selectbox("Customer", customers['name'])
            mname = c2.selectbox("Material", materials['name'])
            qty   = c3.number_input("Quantity", min_value=1, step=1)

            row_m   = materials[materials['name'] == mname].iloc[0]
            unit_p  = row_m['price']
            avail   = int(row_m['stock'])

            st.markdown(f"""
            <div class='glass-card'>
              <span style='color:#7aaeff;font-size:12px;letter-spacing:2px'>ORDER PREVIEW</span><br><br>
              <span style='color:#a0c4ff'>Unit Price:</span> <b style='color:#00c8ff'>{fmt_inr(unit_p)}</b> &nbsp;|&nbsp;
              <span style='color:#a0c4ff'>Stock Available:</span> <b style='color:{"#00ff96" if avail > 10 else "#ff6b6b"}'>{avail} units</b> &nbsp;|&nbsp;
              <span style='color:#a0c4ff'>Estimated Total:</span> <b style='color:#ffd166'>{fmt_inr(unit_p * qty)}</b>
            </div>
            """, unsafe_allow_html=True)

            submitted = st.form_submit_button("🛒 Place Order")

        if submitted:
            if qty > avail:
                st.error(f"❌ Insufficient stock. Only **{avail} units** available.")
            else:
                cid   = int(customers[customers['name'] == cname]['id'].values[0])
                mid   = int(row_m['id'])
                total = unit_p * qty
                conn.execute(
                    "INSERT INTO orders (customer_id,material_id,quantity,total,status) VALUES (?,?,?,?,?)",
                    (cid, mid, qty, total, "Created")
                )
                conn.commit()
                st.success(f"✅ Order placed! Total: **{fmt_inr(total)}**")
                st.balloons()

# ─────────────────────────────────────────────
#  DELIVERY
# ─────────────────────────────────────────────
elif menu == "╰› Delivery":
    st.markdown("## ╰› Process Delivery")
    st.markdown(pipeline_html("Delivered"), unsafe_allow_html=True)

    df = pd.read_sql("""
        SELECT o.id, c.name as customer, m.name as material, o.quantity, o.total, m.stock
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN materials m ON o.material_id = m.id
        WHERE o.status = 'Created'
    """, conn)

    if df.empty:
        st.info("ℹ️ No orders pending delivery.")
    else:
        df['label'] = df.apply(lambda r: f"Order #{int(r['id'])} — {r['customer']} | {r['material']} x{int(r['quantity'])} | {fmt_inr(r['total'])}", axis=1)
        selected = st.selectbox("Select Order to Deliver", df['label'])
        row = df[df['label'] == selected].iloc[0]

        st.markdown(f"""
        <div class='glass-card'>
          <b style='color:#00c8ff'>Order #{int(row['id'])}</b><br>
          Customer: <b>{row['customer']}</b> | Product: <b>{row['material']}</b><br>
          Qty: <b>{int(row['quantity'])}</b> | Stock Before: <b>{int(row['stock'])}</b> | Stock After: <b style='color:#00ff96'>{int(row['stock']) - int(row['quantity'])}</b>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚚 Confirm Delivery & Issue Goods"):
            oid = int(row['id'])
            mid_row = pd.read_sql(f"SELECT material_id FROM orders WHERE id={oid}", conn).iloc[0]
            mid = int(mid_row['material_id'])
            conn.execute("UPDATE orders SET status='Delivered' WHERE id=?", (oid,))
            conn.execute("UPDATE materials SET stock = stock - ? WHERE id=?", (int(row['quantity']), mid))
            conn.commit()
            st.success(f"✅ Order #{oid} delivered! Stock updated.")

# ─────────────────────────────────────────────
#  BILLING
# ─────────────────────────────────────────────
elif menu == "╰› Billing":
    st.markdown("## ╰› Generate Invoice")
    st.markdown(pipeline_html("Billed"), unsafe_allow_html=True)

    df = pd.read_sql("""
        SELECT o.id, c.name as customer, c.email, m.name as material, o.quantity, m.price as unit_price, o.total
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN materials m ON o.material_id = m.id
        WHERE o.status = 'Delivered'
    """, conn)

    if df.empty:
        st.info("ℹ️ No delivered orders pending billing.")
    else:
        df['label'] = df.apply(lambda r: f"Order #{int(r['id'])} — {r['customer']} | {r['material']} | {fmt_inr(r['total'])}", axis=1)
        selected = st.selectbox("Select Order to Bill", df['label'])
        row = df[df['label'] == selected].iloc[0]
        oid = int(row['id'])

        subtotal = float(row['total'])
        cgst     = round(subtotal * 0.09, 2)
        sgst     = round(subtotal * 0.09, 2)
        grand    = round(subtotal + cgst + sgst, 2)
        inv_date = datetime.now().strftime("%d %b %Y")
        due_date = (datetime.now() + timedelta(days=30)).strftime("%d %b %Y")

        st.markdown(f"""
        <div class='glass-card'>
          <div class='section-label'>Invoice Preview</div><br>
          <b style='color:#00c8ff'>Order #{oid}</b> — {row['customer']} ({row['email']})<br><br>
          {row['material']} × {int(row['quantity'])} @ {fmt_inr(float(row['unit_price']))} = <b>{fmt_inr(subtotal)}</b><br>
          CGST 9%: <b>{fmt_inr(cgst)}</b> &nbsp;|&nbsp; SGST 9%: <b>{fmt_inr(sgst)}</b><br>
          <span style='font-size:1.1rem'>Grand Total: <b style='color:#ffd166'>{fmt_inr(grand)}</b></span><br>
          Invoice Date: {inv_date} &nbsp;|&nbsp; Due: {due_date}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🧾 Generate & Download Invoice PDF"):
            # Build PDF
            file = f"invoice_{oid}.pdf"
            doc  = SimpleDocTemplate(file, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=20*mm, rightMargin=20*mm)
            styles = getSampleStyleSheet()

            co_header = ParagraphStyle("co", fontSize=18, fontName="Helvetica-Bold", textColor=colors.HexColor("#003580"), spaceAfter=2)
            co_sub    = ParagraphStyle("cs", fontSize=9,  fontName="Helvetica",      textColor=colors.grey,               spaceAfter=2)
            inv_title = ParagraphStyle("it", fontSize=22, fontName="Helvetica-Bold", textColor=colors.HexColor("#003580"), alignment=2, spaceAfter=4)
            inv_meta  = ParagraphStyle("im", fontSize=9,  fontName="Helvetica",      textColor=colors.grey,               alignment=2)
            section_h = ParagraphStyle("sh", fontSize=9,  fontName="Helvetica-Bold", textColor=colors.HexColor("#003580"), spaceBefore=10, spaceAfter=4)
            body_s    = ParagraphStyle("b",  fontSize=9,  fontName="Helvetica",      textColor=colors.HexColor("#333333"))
            footer_s  = ParagraphStyle("f",  fontSize=8,  fontName="Helvetica",      textColor=colors.grey, alignment=1)

            elems = []
            # Header row
            header_data = [[
                [Paragraph("KIIT ENTERPRISES PVT. LTD.", co_header),
                 Paragraph("KIIT Technology Campus, Bhubaneswar, Odisha - 751024", co_sub),
                 Paragraph("GSTIN: 21AABCK1234C1Z5 | CIN: U72200OR2020PTC001234", co_sub),
                 Paragraph("support@kiitenterprises.in | +91 674 2725 700", co_sub)],
                [Paragraph("INVOICE", inv_title),
                 Paragraph(f"Invoice No: INV-{oid:04d}", inv_meta),
                 Paragraph(f"Date: {inv_date}", inv_meta),
                 Paragraph(f"Due Date: {due_date}", inv_meta)]
            ]]
            t = Table(header_data, colWidths=[105*mm, 65*mm])
            t.setStyle(TableStyle([
                ('VALIGN',    (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND',(0,0), (-1,-1), colors.HexColor("#f0f6ff")),
                ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor("#f0f6ff")]),
                ('TOPPADDING', (0,0),(-1,-1), 10),
                ('BOTTOMPADDING',(0,0),(-1,-1),10),
                ('LEFTPADDING', (0,0),(-1,-1), 10),
                ('RIGHTPADDING',(0,0),(-1,-1), 10),
                ('BOX',       (0,0), (-1,-1), 0.5, colors.HexColor("#c0d8ff")),
            ]))
            elems.append(t)
            elems.append(Spacer(1, 10))

            # Bill To
            elems.append(Paragraph("BILL TO", section_h))
            elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#003580")))
            elems.append(Spacer(1,4))
            elems.append(Paragraph(f"<b>{row['customer']}</b>", body_s))
            elems.append(Paragraph(f"Email: {row['email']}", body_s))
            elems.append(Spacer(1, 10))

            # Items table
            elems.append(Paragraph("ITEMS", section_h))
            elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#003580")))
            elems.append(Spacer(1,4))
            item_data = [
                ["#", "Description", "Qty", "Unit Price", "Amount"],
                ["1", row['material'], str(int(row['quantity'])), f"Rs. {float(row['unit_price']):,.2f}", f"Rs. {subtotal:,.2f}"],
            ]
            ti = Table(item_data, colWidths=[8*mm, 85*mm, 20*mm, 30*mm, 27*mm])
            ti.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0),  colors.HexColor("#003580")),
                ('TEXTCOLOR',     (0,0), (-1,0),  colors.white),
                ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
                ('FONTSIZE',      (0,0), (-1,-1), 9),
                ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor("#f5f9ff")]),
                ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor("#c0d8ff")),
                ('ALIGN',         (2,0), (-1,-1), 'RIGHT'),
                ('TOPPADDING',    (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
                ('RIGHTPADDING',  (0,0), (-1,-1), 8),
            ]))
            elems.append(ti)
            elems.append(Spacer(1, 8))

            # Totals
            totals_data = [
                ["", "Subtotal",   f"Rs. {subtotal:,.2f}"],
                ["", "CGST  9%",   f"Rs. {cgst:,.2f}"],
                ["", "SGST  9%",   f"Rs. {sgst:,.2f}"],
                ["", "GRAND TOTAL",f"Rs. {grand:,.2f}"],
            ]
            tt = Table(totals_data, colWidths=[93*mm, 45*mm, 32*mm])
            tt.setStyle(TableStyle([
                ('FONTSIZE',     (0,0), (-1,-1), 9),
                ('FONTNAME',     (0,3), (-1,3),  'Helvetica-Bold'),
                ('BACKGROUND',   (1,3), (-1,3),  colors.HexColor("#003580")),
                ('TEXTCOLOR',    (1,3), (-1,3),  colors.white),
                ('ALIGN',        (1,0), (-1,-1), 'RIGHT'),
                ('TOPPADDING',   (0,0), (-1,-1), 5),
                ('BOTTOMPADDING',(0,0), (-1,-1), 5),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
                ('LINEABOVE',    (1,3), (-1,3),  0.5, colors.HexColor("#003580")),
            ]))
            elems.append(tt)
            elems.append(Spacer(1, 20))

            # Footer
            elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c0d8ff")))
            elems.append(Spacer(1,6))
            elems.append(Paragraph("Payment Terms: Net 30 Days &nbsp;|&nbsp; Bank: HDFC Bank &nbsp;|&nbsp; A/C: 5020 0123 4567 &nbsp;|&nbsp; IFSC: HDFC0001234", footer_s))
            elems.append(Spacer(1,4))
            elems.append(Paragraph("Thank you for your business! For queries, contact support@kiitenterprises.in", footer_s))

            doc.build(elems)
            conn.execute("UPDATE orders SET status='Completed' WHERE id=?", (oid,))
            conn.commit()

            with open(file, "rb") as f:
                st.download_button("⬇️ Download Invoice PDF", f, file_name=file, mime="application/pdf")
            st.success(f"✅ Invoice INV-{oid:04d} generated! Grand Total: **{fmt_inr(grand)}** (incl. GST)")

# ─────────────────────────────────────────────
#  RECORD PAYMENT
# ─────────────────────────────────────────────
elif menu == "╰› Record Payment":
    st.markdown("## ╰› Record Payment")
    st.markdown(pipeline_html("Paid"), unsafe_allow_html=True)

    df = pd.read_sql("""
        SELECT o.id, c.name as customer, o.total,
               (o.total * 1.18) as grand_total
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN payments p ON p.order_id = o.id
        WHERE o.status = 'Completed' AND p.id IS NULL
    """, conn)

    if df.empty:
        st.info("ℹ️ No billed orders pending payment.")
    else:
        df['label'] = df.apply(lambda r: f"Order #{int(r['id'])} — {r['customer']} | Due: {fmt_inr(round(r['grand_total'],2))}", axis=1)
        selected = st.selectbox("Select Order", df['label'])
        row = df[df['label'] == selected].iloc[0]
        method = st.selectbox("Payment Method", ["Bank Transfer", "UPI", "Cheque", "Cash", "NEFT/RTGS"])

        st.markdown(f"""
        <div class='glass-card'>
          Order <b style='color:#00c8ff'>#{int(row['id'])}</b> — {row['customer']}<br>
          Amount Due: <b style='color:#ffd166'>{fmt_inr(round(row['grand_total'],2))}</b> (incl. GST)
        </div>
        """, unsafe_allow_html=True)

        if st.button("💳 Confirm Payment Received"):
            oid   = int(row['id'])
            amt   = round(float(row['grand_total']), 2)
            conn.execute("INSERT INTO payments (order_id,amount,method) VALUES (?,?,?)", (oid, amt, method))
            conn.execute("UPDATE orders SET status='Paid' WHERE id=?", (oid,))
            conn.commit()
            st.success(f"✅ Payment of **{fmt_inr(amt)}** recorded via **{method}**!")

# ─────────────────────────────────────────────
#  VIEW ALL ORDERS
# ─────────────────────────────────────────────
elif menu == "╰› View All Orders":
    st.markdown("## ╰› All Orders")

    status_filter = st.multiselect("Filter by Status", ["Created","Delivered","Completed","Paid"], default=["Created","Delivered","Completed","Paid"])
    placeholders = ",".join("?" * len(status_filter))

    df = pd.read_sql(f"""
        SELECT o.id as 'Order ID', c.name as Customer, m.name as Product,
               o.quantity as Qty, o.total as Subtotal,
               ROUND(o.total * 1.18, 2) as 'Grand Total (GST)',
               o.status as Status,
               strftime('%d %b %Y', o.created_at) as Date
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN materials m ON o.material_id = m.id
        WHERE o.status IN ({placeholders})
        ORDER BY o.id DESC
    """, conn, params=status_filter)

    if df.empty:
        st.info("ℹ️ No orders found for selected filters.")
    else:
        def color_status(val):
            colors_map = {
                "Created":   "color:#ffb400; font-weight:600",
                "Delivered": "color:#0096ff; font-weight:600",
                "Completed": "color:#00ff96; font-weight:600",
                "Paid":      "color:#b400ff; font-weight:600",
            }
            return colors_map.get(val, "")

        styled = df.style.map(color_status, subset=["Status"])\
                         .format({"Subtotal": "₹{:,.0f}", "Grand Total (GST)": "₹{:,.0f}"})
        st.dataframe(styled, use_container_width=True, height=420)

        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Export as CSV", csv, "o2c_orders.csv", "text/csv")

# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────
elif menu == "╰› Dashboard":
    st.markdown("## ╰› Analytics Dashboard")

    orders    = pd.read_sql("SELECT * FROM orders", conn)
    customers = pd.read_sql("SELECT * FROM customers", conn)
    materials = pd.read_sql("SELECT * FROM materials", conn)
    payments  = pd.read_sql("SELECT * FROM payments", conn)

    if orders.empty:
        st.warning("⚠️ No data yet. Load sample data or create orders first.")
    else:
        merged = orders.merge(customers, left_on='customer_id', right_on='id', suffixes=('','_c'))
        merged = merged.merge(materials, left_on='material_id', right_on='id', suffixes=('','_m'))
        merged['grand_total'] = merged['total'] * 1.18

        total_rev   = payments['amount'].sum() if not payments.empty else 0
        pending_amt = merged[~merged['status'].isin(['Paid'])]['grand_total'].sum()
        total_ord   = len(orders)
        pending_ord = len(orders[orders['status'] == 'Created'])

        # ── KPI Row ──
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Revenue Collected", fmt_inr(total_rev))
        k2.metric("⏳ AR Outstanding",    fmt_inr(pending_amt))
        k3.metric("📦 Total Orders",      total_ord)
        k4.metric("🔴 Pending Orders",    pending_ord)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: Donut + Revenue Bar ──
        r1c1, r1c2 = st.columns(2)

        with r1c1:
            status_counts = orders['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig_donut = go.Figure(go.Pie(
                labels=status_counts['Status'],
                values=status_counts['Count'],
                hole=0.55,
                marker=dict(colors=NEON, line=dict(color='#050818', width=3)),
                textfont=dict(family="Rajdhani, sans-serif", size=13, color="#ffffff"),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
            ))
            fig_donut.update_layout(title="Order Status Breakdown", **{
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'plot_bgcolor':  'rgba(0,0,0,0)',
                'font': dict(family="Rajdhani, sans-serif", color="#a0c4ff"),
                'title_font': dict(family="Orbitron, monospace", color="#00c8ff", size=13),
                'legend': dict(bgcolor="rgba(0,0,0,0)"),
                'margin': dict(l=10,r=10,t=40,b=10),
                'annotations': [dict(text=f"<b>{total_ord}</b><br>Orders", x=0.5, y=0.5,
                                     font=dict(family="Orbitron,monospace", size=14, color="#00c8ff"),
                                     showarrow=False)]
            })
            st.plotly_chart(fig_donut, use_container_width=True)

        with r1c2:
            rev_by_prod = merged.groupby('name_m')['total'].sum().reset_index()
            rev_by_prod.columns = ['Product','Revenue']
            rev_by_prod = rev_by_prod.sort_values('Revenue', ascending=True)
            fig_bar = go.Figure(go.Bar(
                x=rev_by_prod['Revenue'], y=rev_by_prod['Product'],
                orientation='h',
                marker=dict(
                    color=rev_by_prod['Revenue'],
                    colorscale=[[0,'#7b5cff'],[0.5,'#00c8ff'],[1,'#00ff96']],
                    line=dict(color='rgba(0,0,0,0)')
                ),
                text=[fmt_inr(v) for v in rev_by_prod['Revenue']],
                textposition='outside',
                textfont=dict(color='#a0c4ff', size=11),
                hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.0f}<extra></extra>",
            ))
            fig_bar.update_layout(title="Revenue by Product", xaxis_title="", yaxis_title="",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Rajdhani, sans-serif", color="#a0c4ff"),
                title_font=dict(family="Orbitron, monospace", color="#00c8ff", size=13),
                xaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False, showticklabels=False),
                yaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False),
                margin=dict(l=10,r=60,t=40,b=10),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── Row 2: Line chart + Top Customers ──
        r2c1, r2c2 = st.columns(2)

        with r2c1:
            merged['date'] = pd.to_datetime(merged['created_at']).dt.date
            rev_time = merged.groupby('date')['total'].sum().reset_index()
            rev_time.columns = ['Date','Revenue']
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=rev_time['Date'], y=rev_time['Revenue'],
                mode='lines+markers',
                line=dict(color='#00c8ff', width=2.5),
                marker=dict(color='#00ff96', size=8, line=dict(color='#00c8ff', width=2)),
                fill='tozeroy',
                fillcolor='rgba(0,200,255,0.06)',
                hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<extra></extra>",
                name="Revenue"
            ))
            fig_line.update_layout(title="Revenue Over Time",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Rajdhani, sans-serif", color="#a0c4ff"),
                title_font=dict(family="Orbitron, monospace", color="#00c8ff", size=13),
                xaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False),
                yaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False),
                margin=dict(l=10,r=10,t=40,b=10), showlegend=False
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with r2c2:
            top_cust = merged.groupby('name')['total'].sum().sort_values(ascending=False).head(5).reset_index()
            top_cust.columns = ['Customer','Revenue']
            fig_cust = go.Figure(go.Bar(
                x=top_cust['Customer'], y=top_cust['Revenue'],
                marker=dict(color=NEON[:len(top_cust)], line=dict(color='rgba(0,0,0,0)')),
                text=[fmt_inr(v) for v in top_cust['Revenue']],
                textposition='outside',
                textfont=dict(color='#a0c4ff', size=11),
                hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<extra></extra>",
            ))
            fig_cust.update_layout(title="Top Customers by Revenue",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Rajdhani, sans-serif", color="#a0c4ff"),
                title_font=dict(family="Orbitron, monospace", color="#00c8ff", size=13),
                xaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False),
                yaxis=dict(gridcolor="rgba(0,200,255,0.07)", zeroline=False, showticklabels=False),
                margin=dict(l=10,r=10,t=40,b=40),
            )
            st.plotly_chart(fig_cust, use_container_width=True)

        # ── Recent Activity ──
        st.markdown("---")
        st.markdown("## ⚡ Recent Activity")
        recent = pd.read_sql("""
            SELECT o.id, c.name as customer, m.name as product, o.total, o.status,
                   strftime('%d %b %Y %H:%M', o.created_at) as time
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            JOIN materials m ON o.material_id = m.id
            ORDER BY o.id DESC LIMIT 5
        """, conn)

        for _, r in recent.iterrows():
            icon = {"Created":"🟡","Delivered":"🔵","Completed":"🟢","Paid":"🟣"}.get(r['status'],"⚪")
            st.markdown(f"""
            <div class='glass-card' style='padding:12px 20px;margin-bottom:8px'>
              {icon} &nbsp; <b style='color:#00c8ff'>Order #{int(r['id'])}</b>
              &nbsp;—&nbsp; {r['customer']} &nbsp;|&nbsp; {r['product']}
              &nbsp;|&nbsp; <b style='color:#ffd166'>{fmt_inr(r['total'])}</b>
              &nbsp;|&nbsp; <span style='color:#7aaeff;font-size:12px'>{r['time']}</span>
              &nbsp;&nbsp; <span style='float:right'>{badge(r['status'])}</span>
            </div>
            """, unsafe_allow_html=True)
