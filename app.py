# app.py
"""
ReserVision: AI-Simulated Small Cafe Table Reservation System (STRS)
Team: ReserVision
Client: 5&2 Coffeehouse

Features:
- Customer booking with real-time availability check
- AI-assisted table assignment (minimizing wasted seats)
- View / cancel reservations
- Admin dashboard for table & reservation management
- SQLite backend for data persistence
- Simulated notifications (email/SMS placeholders)

Run:
pip install streamlit pandas
streamlit run app.py
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import uuid

# ============================================================
# CONFIGURATION
# ============================================================
DB_PATH = "strs.db"
ADMIN_PASSWORD = "admin123"
RESERVATION_DURATION_MINUTES = 90

# ============================================================
# PAGE CONFIG & THEME
# ============================================================
st.set_page_config(
    page_title="☕ ReserVision - 5&2 Coffeehouse",
    page_icon="☕",
    layout="centered",
)

page_style = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #f5ede0 0%, #fff 100%);
    color: #3e2723;
}
[data-testid="stSidebar"] {
    background-color: #d7ccc8;
}
h1, h2, h3, h4 {
    color: #4e342e;
}
.stButton > button {
    background-color: #6d4c41;
    color: white;
    border-radius: 8px;
    border: none;
}
.stButton > button:hover {
    background-color: #4e342e;
}
</style>
"""
st.markdown(page_style, unsafe_allow_html=True)

st.markdown(
    """
    <div style='text-align:center; padding:10px 0;'>
        <h1>☕ <b>ReserVision</b> — Smart Café Table Reservation System</h1>
        <h3>Client: 5&2 Coffeehouse, Quiapo Manila</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# DATABASE FUNCTIONS
# ============================================================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cafe_tables (
            table_id TEXT PRIMARY KEY,
            name TEXT,
            capacity INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id TEXT PRIMARY KEY,
            customer_name TEXT,
            contact TEXT,
            date TEXT,
            time TEXT,
            party_size INTEGER,
            table_id TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    cur.execute("SELECT COUNT(*) FROM cafe_tables")
    if cur.fetchone()[0] == 0:
        tables = [
            ("T1", "Window 2-Seater", 2),
            ("T2", "Corner 2-Seater", 2),
            ("T3", "Center 4-Seater", 4),
            ("T4", "Booth 4-Seater", 4),
            ("T5", "Community 6-Seater", 6),
        ]
        cur.executemany("INSERT INTO cafe_tables VALUES (?, ?, ?)", tables)
    conn.commit()
    conn.close()

def fetch_tables():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM cafe_tables ORDER BY capacity, name", conn)
    conn.close()
    return df

def fetch_reservations_on(date_str):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM reservations WHERE date=?", conn, params=(date_str,))
    conn.close()
    return df

def fetch_all_reservations():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM reservations ORDER BY date, time", conn)
    conn.close()
    return df

def insert_reservation(resv):
    conn = get_conn()
    conn.execute("""
        INSERT INTO reservations (reservation_id, customer_name, contact, date, time, party_size, table_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        resv["reservation_id"], resv["customer_name"], resv["contact"],
        resv["date"], resv["time"], resv["party_size"],
        resv["table_id"], resv["status"], resv["created_at"]
    ))
    conn.commit()
    conn.close()

def delete_reservation(res_id):
    conn = get_conn()
    conn.execute("UPDATE reservations SET status='cancelled' WHERE reservation_id=?", (res_id,))
    conn.commit()
    conn.close()

# ============================================================
# LOGIC FUNCTIONS
# ============================================================
def parse_datetime(date_str, time_str):
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

def time_conflicts(req_dt, existing_dt):
    delta = timedelta(minutes=RESERVATION_DURATION_MINUTES)
    return not (req_dt + delta <= existing_dt or existing_dt + delta <= req_dt)

def available_tables(date_str, time_str, party_size):
    all_tables = fetch_tables()
    reservations = fetch_reservations_on(date_str)
    req_dt = parse_datetime(date_str, time_str)
    busy = set()

    for _, r in reservations.iterrows():
        if r["status"] != "cancelled" and r["table_id"]:
            if time_conflicts(req_dt, parse_datetime(r["date"], r["time"])):
                busy.add(r["table_id"])

    available = all_tables[
        (all_tables["capacity"] >= party_size) &
        (~all_tables["table_id"].isin(busy))
    ]
    return available

def ai_suggest_table(date_str, time_str, party_size):
    candidates = available_tables(date_str, time_str, party_size)
    if candidates.empty:
        return None
    candidates["waste"] = candidates["capacity"] - party_size
    return candidates.sort_values(["waste", "capacity"]).iloc[0]["table_id"]

# ============================================================
# SIMULATED NOTIFICATION FUNCTION
# ============================================================
def send_notification(contact, message):
    st.toast(f"📩 Notification sent to {contact}: {message}")
    print(f"[SIMULATED NOTIFICATION] -> {contact}: {message}")

# ============================================================
# MAIN APP LOGIC
# ============================================================
init_db()
role = st.sidebar.radio("Select Role", ["Customer", "Admin"])

# -------------------- CUSTOMER --------------------
if role == "Customer":
    st.markdown("### 🧾 Step 1: Enter Booking Details")
    with st.form("booking_form"):
        name = st.text_input("Your Name")
        contact = st.text_input("Contact (phone or email)")
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Reservation Date", datetime.today())
        with col2:
            time = st.time_input("Reservation Time", datetime.now().time().replace(second=0, microsecond=0))
        party = st.number_input("Party Size", min_value=1, max_value=20, value=2)
        submit = st.form_submit_button("Check Availability")

    # CART-LIKE PREVIEW
    if submit:
        if not name or not contact:
            st.error("Please fill out all required fields.")
        else:
            date_str, time_str = date.strftime("%Y-%m-%d"), time.strftime("%H:%M")
            available = available_tables(date_str, time_str, party)
            if available.empty:
                st.warning("No tables available for that time and group size.")
            else:
                ai_table = ai_suggest_table(date_str, time_str, party)
                st.success("✅ Tables available! Review and confirm your booking below.")
                st.dataframe(available)

                st.markdown("### 🛒 Step 2: Reservation Cart (Preview)")
                st.info(f"AI suggests Table **{ai_table}** as the most suitable choice.")
                chosen = st.selectbox("Choose your preferred table:", available["table_id"].tolist(), index=0)

                st.write("You may confirm or cancel your booking:")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirm Booking"):
                        res_id = str(uuid.uuid4())[:8]
                        insert_reservation({
                            "reservation_id": res_id,
                            "customer_name": name,
                            "contact": contact,
                            "date": date_str,
                            "time": time_str,
                            "party_size": party,
                            "table_id": chosen,
                            "status": "confirmed",
                            "created_at": datetime.utcnow().isoformat()
                        })
                        send_notification(contact, f"Your reservation {res_id} on {date_str} at {time_str} is confirmed (Table {chosen}).")
                        st.success(f"🎉 Reservation Confirmed! Table {chosen} booked successfully.")
                        st.write(f"**Reservation ID:** {res_id}")
                with col2:
                    if st.button("❌ Cancel Booking"):
                        st.warning("Booking process cancelled.")

    st.markdown("---")
    st.markdown("### 🔍 Manage Your Reservations")
    lookup = st.text_input("Enter your contact to view or cancel bookings")
    if lookup:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM reservations WHERE contact=? ORDER BY date, time", conn, params=(lookup,))
        conn.close()
        if df.empty:
            st.info("No reservations found for this contact.")
        else:
            st.dataframe(df)
            cancel_id = st.text_input("Enter Reservation ID to cancel")
            if st.button("Cancel Reservation"):
                delete_reservation(cancel_id)
                send_notification(lookup, f"Your reservation {cancel_id} has been cancelled.")
                st.success("Reservation cancelled successfully.")

# -------------------- ADMIN --------------------
elif role == "Admin":
    st.markdown("### 👩‍💼 Admin Dashboard")
    pwd = st.text_input("Enter Admin Password", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("Please enter the correct admin password.")
        st.stop()

    st.success("Admin authenticated successfully.")
    tabs = st.tabs(["📋 Reservations", "🪑 Tables", "⚠️ Conflict Checker"])

    # --- Reservations ---
    with tabs[0]:
        st.subheader("📅 All Reservations")
        res_df = fetch_all_reservations()
        st.dataframe(res_df)

    # --- Tables (with Occupancy Status) ---
    with tabs[1]:
        st.subheader("🪑 Table Status Overview")
        tables = fetch_tables()
        all_reservations = fetch_all_reservations()

        # Determine occupied tables
        today = datetime.today().strftime("%Y-%m-%d")
        occupied_tables = set(
            all_reservations.loc[
                (all_reservations["status"] == "confirmed") & (all_reservations["date"] == today),
                "table_id"
            ].tolist()
        )

        status_list, booked_by, booked_time = [], [], []
        for _, row in tables.iterrows():
            if row["table_id"] in occupied_tables:
                res = all_reservations[
                    (all_reservations["table_id"] == row["table_id"]) &
                    (all_reservations["status"] == "confirmed") &
                    (all_reservations["date"] == today)
                ].iloc[0]
                status_list.append("🔴 Occupied")
                booked_by.append(res["customer_name"])
                booked_time.append(res["time"])
            else:
                status_list.append("🟢 Available")
                booked_by.append("-")
                booked_time.append("-")

        tables["Status"] = status_list
        tables["Reserved By"] = booked_by
        tables["Time"] = booked_time
        st.dataframe(tables)

        st.markdown("### ➕ Manage Tables")
        with st.form("add_table"):
            new_id = st.text_input("Table ID")
            new_name = st.text_input("Table Name")
            new_cap = st.number_input("Capacity", min_value=1, max_value=10, value=2)
            add_sub = st.form_submit_button("Add Table")
        if add_sub:
            if new_id and new_name:
                conn = get_conn()
                conn.execute("INSERT INTO cafe_tables VALUES (?, ?, ?)", (new_id, new_name, new_cap))
                conn.commit()
                conn.close()
                st.success("Table added successfully.")
                st.rerun()

        rem = st.text_input("Enter Table ID to Remove")
        if st.button("Remove Table"):
            conn = get_conn()
            conn.execute("DELETE FROM cafe_tables WHERE table_id=?", (rem,))
            conn.commit()
            conn.close()
            st.success("Table removed successfully.")
            st.rerun()

    # --- Conflict Checker ---
    with tabs[2]:
        st.subheader("⚠️ Double Booking Checker")
        conn = get_conn()
        res = pd.read_sql_query("SELECT * FROM reservations WHERE status='confirmed' ORDER BY date, time", conn)
        conn.close()
        conflicts = []
        for i, r1 in res.iterrows():
            for j, r2 in res.iterrows():
                if i >= j:
                    continue
                if r1["table_id"] == r2["table_id"] and time_conflicts(
                    parse_datetime(r1["date"], r1["time"]),
                    parse_datetime(r2["date"], r2["time"])
                ):
                    conflicts.append((r1["reservation_id"], r2["reservation_id"], r1["table_id"]))
        if conflicts:
            st.warning("⚠ Double bookings detected!")
            st.table(pd.DataFrame(conflicts, columns=["Reservation 1", "Reservation 2", "Table"]))
        else:
            st.success("✅ No conflicts found. All bookings are valid.")

# ============================================================
# FOOTER / NOTES
# ============================================================
st.markdown("---")
st.caption("""
**Notes:**  
This is a demo app. Replace notification placeholders with Twilio or SMTP for real-time email/SMS notifications.  
For production deployment, secure the admin dashboard properly, implement multi-user authentication,  
and consider migrating from SQLite to a cloud database (e.g., PostgreSQL) for scalability.
""")
