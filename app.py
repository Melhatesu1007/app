# app.py
"""
Small Cafe Table Reservation System (STRS) - Streamlit app (single-file)
Team: ReserVision / Client: 5&2 Coffeehouse

Features:
- Customer booking (real-time availability check)
- AI-assisted table assignment (greedy minimization of wasted seats)
- View / cancel reservations
- Admin dashboard to manage tables & reservations
- SQLite backend for persistence
- Notification function placeholders (email/SMS)

Run:
pip install streamlit pandas
streamlit run app.py
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import uuid

DB_PATH = "strs.db"
ADMIN_PASSWORD = "admin123"  # change before deployment

### ---------- Database helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # tables for cafe seating
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cafe_tables (
        table_id TEXT PRIMARY KEY,
        name TEXT,
        capacity INTEGER
    )
    """)
    # reservations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id TEXT PRIMARY KEY,
        customer_name TEXT,
        contact TEXT,
        date TEXT,           -- YYYY-MM-DD
        time TEXT,           -- HH:MM (24h)
        party_size INTEGER,
        table_id TEXT,
        status TEXT,         -- pending / confirmed / cancelled
        created_at TEXT
    )
    """)
    conn.commit()
    # insert sample tables if empty
    cur.execute("SELECT COUNT(*) FROM cafe_tables")
    if cur.fetchone()[0] == 0:
        sample = [
            ("T1", "Window 2-seater", 2),
            ("T2", "Corner 2-seater", 2),
            ("T3", "Center 4-seater", 4),
            ("T4", "Booth 4-seater", 4),
            ("T5", "Community 6-seater", 6),
        ]
        for tid, name, cap in sample:
            cur.execute("INSERT INTO cafe_tables (table_id, name, capacity) VALUES (?, ?, ?)", (tid, name, cap))
        conn.commit()
    conn.close()

def fetch_tables():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM cafe_tables ORDER BY capacity, name", conn)
    conn.close()
    return df

def fetch_reservations_on(date_str, time_str=None):
    conn = get_conn()
    cur = conn.cursor()
    if time_str:
        cur.execute("SELECT * FROM reservations WHERE date=? AND time=?", (date_str, time_str))
    else:
        cur.execute("SELECT * FROM reservations WHERE date=?", (date_str,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

def insert_reservation(resv: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reservations (reservation_id, customer_name, contact, date, time, party_size, table_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        resv["reservation_id"],
        resv["customer_name"],
        resv["contact"],
        resv["date"],
        resv["time"],
        resv["party_size"],
        resv.get("table_id"),
        resv.get("status", "pending"),
        resv.get("created_at", datetime.utcnow().isoformat())
    ))
    conn.commit()
    conn.close()

def update_reservation_status(reservation_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reservations SET status=? WHERE reservation_id=?", (status, reservation_id))
    conn.commit()
    conn.close()

def assign_table_to_reservation(reservation_id, table_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reservations SET table_id=?, status='confirmed' WHERE reservation_id=?", (table_id, reservation_id))
    conn.commit()
    conn.close()

def delete_reservation(reservation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reservations SET status='cancelled' WHERE reservation_id=?", (reservation_id,))
    conn.commit()
    conn.close()

def add_table(table_id, name, capacity):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO cafe_tables (table_id, name, capacity) VALUES (?, ?, ?)", (table_id, name, capacity))
    conn.commit()
    conn.close()

def remove_table(table_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM cafe_tables WHERE table_id=?", (table_id,))
    conn.commit()
    conn.close()

### ---------- Reservation logic ----------
# Duration per reservation (minutes). This controls conflict window.
RESERVATION_DURATION_MINUTES = 90

def parse_datetime(date_str, time_str):
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

def time_conflicts(resv_dt: datetime, existing_dt: datetime):
    # conflict if overlapping within +/- duration window
    delta = timedelta(minutes=RESERVATION_DURATION_MINUTES)
    return not (resv_dt + delta <= existing_dt or existing_dt + delta <= resv_dt)

def available_tables_for_slot(date_str, time_str, party_size):
    # returns list of candidate tables (table rows) that are free at that slot
    all_tables = fetch_tables()
    reservations = fetch_reservations_on(date_str)  # all reservations for date
    requested_dt = parse_datetime(date_str, time_str)
    busy_table_ids = set()
    for _, r in reservations.iterrows():
        if r["status"] == "cancelled":
            continue
        existing_dt = parse_datetime(r["date"], r["time"])
        if time_conflicts(requested_dt, existing_dt) and r["table_id"]:
            busy_table_ids.add(r["table_id"])
    # filter tables by capacity and not busy
    candidates = all_tables[(all_tables["capacity"] >= party_size) & (~all_tables["table_id"].isin(busy_table_ids))]
    return candidates

def ai_assign_table(date_str, time_str, party_size):
    """
    'AI-assisted' assignment:
    - choose available table with capacity >= party_size
    - prefer table that minimizes wasted seats (capacity - party_size)
    - tie-breaker: smallest capacity then alphabetical table_id
    """
    candidates = available_tables_for_slot(date_str, time_str, party_size)
    if candidates.empty:
        return None
    # compute wasted seats and sort
    candidates = candidates.copy()
    candidates["waste"] = candidates["capacity"] - party_size
    candidates = candidates.sort_values(["waste", "capacity", "table_id"])
    chosen = candidates.iloc[0]
    return chosen["table_id"]

### ---------- Notification placeholders ----------
def send_notification(contact, message):
    """
    Placeholder to integrate email/SMS (e.g., SMTP or Twilio).
    Currently simulated with streamlit messages (or prints).
    Replace this function's body with real API call when deploying.
    """
    print(f"[NOTIFICATION] -> {contact}: {message}")
    # In real deployment, call Twilio or SMTP here.
    return True

### ---------- Streamlit UI ----------
st.set_page_config(page_title="STRS - 5&2 Coffeehouse", layout="centered")
init_db()

st.title("ReserVision — Small Cafe Table Reservation System (STRS)")
st.write("Client: 5&2 Coffeehouse · Demo Streamlit app. (SQLite backend)")

role = st.sidebar.radio("I'm a", ["Customer", "Admin"])

if role == "Customer":
    st.header("Book a table")
    with st.form("booking_form"):
        name = st.text_input("Your name", max_chars=80)
        contact = st.text_input("Contact (phone or email)", max_chars=80)
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Reservation date", datetime.today())
        with col2:
            time = st.time_input("Reservation time", datetime.now().time().replace(second=0, microsecond=0))
        party = st.number_input("Party size", min_value=1, max_value=20, value=2)
        special = st.text_area("Special requests (optional)", help="We won't use it in assignment but staff will see it.")
        submitted = st.form_submit_button("Check & Book")
    if submitted:
        if not name or not contact:
            st.error("Please enter name and contact.")
        else:
            date_str = date.strftime("%Y-%m-%d")
            time_str = time.strftime("%H:%M")
            # show available tables
            candidates = available_tables_for_slot(date_str, time_str, party)
            if candidates.empty:
                st.warning("No tables available for that time and party size. Try a different time or date.")
                # optionally suggest other times (simple suggestion: +/- 1 hour)
                suggestions = []
                for delta in ( -60, -30, 30, 60):
                    alt_dt = datetime.combine(date, time) + timedelta(minutes=delta)
                    alt_date = alt_dt.date().strftime("%Y-%m-%d")
                    alt_time = alt_dt.time().strftime("%H:%M")
                    if not available_tables_for_slot(alt_date, alt_time, party).empty:
                        suggestions.append(f"{alt_date} {alt_time}")
                if suggestions:
                    st.info("Try these alternatives: " + ", ".join(suggestions))
            else:
                st.success(f"{len(candidates)} table(s) available.")
                st.dataframe(candidates[["table_id","name","capacity"]])
                # AI assign suggestion
                suggested_table = ai_assign_table(date_str, time_str, party)
                if suggested_table:
                    st.info(f"Suggested table (AI): {suggested_table}")
                else:
                    st.info("No automatic suggestion available.")
                if st.button("Confirm reservation (assign suggested)"):
                    reservation_id = str(uuid.uuid4())[:8]
                    resv = {
                        "reservation_id": reservation_id,
                        "customer_name": name,
                        "contact": contact,
                        "date": date_str,
                        "time": time_str,
                        "party_size": party,
                        "table_id": suggested_table,
                        "status": "confirmed" if suggested_table else "pending",
                        "created_at": datetime.utcnow().isoformat()
                    }
                    insert_reservation(resv)
                    # send notification (simulated)
                    msg = f"Reservation {reservation_id} on {date_str} at {time_str} for {party} people."
                    if suggested_table:
                        msg += f" Table: {suggested_table}. Status: confirmed."
                    else:
                        msg += " Status: pending (we'll contact you)."
                    send_notification(contact, msg)
                    st.success("Reservation created! We sent a confirmation (simulated).")
                    st.write("Reservation ID:", reservation_id)

    st.markdown("---")
    st.header("Manage your reservations")
    contact_lookup = st.text_input("Enter your contact (phone or email) to view bookings")
    if contact_lookup:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM reservations WHERE contact=? ORDER BY date, time", conn, params=(contact_lookup,))
        conn.close()
        if df.empty:
            st.info("No reservations found for that contact.")
        else:
            df_display = df.copy()
            df_display["actions"] = df_display["reservation_id"]  # placeholder
            st.dataframe(df_display[["reservation_id","customer_name","date","time","party_size","table_id","status"]])
            # cancellation
            to_cancel = st.text_input("Enter a reservation ID to cancel (optional)")
            if st.button("Cancel reservation"):
                if to_cancel.strip() == "":
                    st.error("Enter a reservation ID.")
                else:
                    matching = df[df["reservation_id"] == to_cancel.strip()]
                    if matching.empty:
                        st.error("Reservation ID not found for this contact.")
                    else:
                        delete_reservation(to_cancel.strip())
                        send_notification(contact_lookup, f"Your reservation {to_cancel.strip()} has been cancelled.")
                        st.success("Reservation cancelled.")

elif role == "Admin":
    st.header("Admin Dashboard")
    pwd = st.text_input("Admin password", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("Enter admin password to access.")
        st.stop()
    st.success("Admin authenticated.")
    # Tabs for tables and reservations
    tabs = st.tabs(["Tables", "Reservations", "Quick Assign AI"])
    with tabs[0]:
        st.subheader("Manage Tables")
        tables_df = fetch_tables()
        st.dataframe(tables_df)
        with st.form("add_table_form"):
            new_id = st.text_input("Table ID (e.g., T6)")
            new_name = st.text_input("Table name (e.g., Patio 2-seater)")
            new_cap = st.number_input("Capacity", min_value=1, max_value=20, value=2)
            add_sub = st.form_submit_button("Add table")
        if add_sub:
            if new_id.strip() == "" or new_name.strip() == "":
                st.error("Provide ID and name.")
            else:
                add_table(new_id.strip(), new_name.strip(), new_cap)
                st.success("Table added.")
                st.experimental_rerun()
        # remove table
        rem = st.text_input("Table ID to remove (optional)")
        if st.button("Remove table"):
            if rem.strip() == "":
                st.error("Enter table ID.")
            else:
                remove_table(rem.strip())
                st.success("Table removed (if existed).")
                st.experimental_rerun()

    with tabs[1]:
        st.subheader("Reservations")
        conn = get_conn()
        rsv_df = pd.read_sql_query("SELECT * FROM reservations ORDER BY date, time", conn)
        conn.close()
        if rsv_df.empty:
            st.info("No reservations yet.")
        else:
            st.dataframe(rsv_df)
            st.markdown("**Actions**")
            sel_id = st.text_input("Reservation ID to operate on")
            col1, col2, col3 = st.columns(3)
            if col1.button("Confirm (assign suggested)"):
                # assign using AI and mark confirmed
                row = rsv_df[rsv_df["reservation_id"] == sel_id]
                if row.empty:
                    st.error("Reservation not found.")
                else:
                    r = row.iloc[0]
                    assigned = ai_assign_table(r["date"], r["time"], r["party_size"])
                    if not assigned:
                        st.warning("No table available for that slot.")
                    else:
                        assign_table_to_reservation(sel_id, assigned)
                        send_notification(r["contact"], f"Your reservation {sel_id} is confirmed (Table {assigned}).")
                        st.success(f"Assigned {assigned} and confirmed {sel_id}.")
                        st.experimental_rerun()
            if col2.button("Mark Cancelled"):
                row = rsv_df[rsv_df["reservation_id"] == sel_id]
                if row.empty:
                    st.error("Reservation not found.")
                else:
                    delete_reservation(sel_id)
                    send_notification(row.iloc[0]["contact"], f"Your reservation {sel_id} has been cancelled by staff.")
                    st.success("Marked cancelled.")
                    st.experimental_rerun()
            if col3.button("Manual assign table"):
                manual_table = st.text_input("Enter table ID to assign manually")
                if manual_table:
                    row = rsv_df[rsv_df["reservation_id"] == sel_id]
                    if row.empty:
                        st.error("Reservation not found.")
                    else:
                        assign_table_to_reservation(sel_id, manual_table)
                        send_notification(row.iloc[0]["contact"], f"Your reservation {sel_id} assigned to table {manual_table}.")
                        st.success("Manually assigned.")
                        st.experimental_rerun()

    with tabs[2]:
        st.subheader("Quick Assign AI (batch)")
        st.write("This will try to auto-assign all pending reservations for a selected date.")
        batch_date = st.date_input("Date to run batch assignment", datetime.today())
        if st.button("Run batch assign"):
            date_str = batch_date.strftime("%Y-%m-%d")
            pending = fetch_reservations_on(date_str)
            if pending.empty:
                st.info("No reservations on that date.")
            else:
                assigned_count = 0
                for _, r in pending.iterrows():
                    if r["status"] != "cancelled" and (not r["table_id"] or r["status"] != "confirmed"):
                        asg = ai_assign_table(r["date"], r["time"], r["party_size"])
                        if asg:
                            assign_table_to_reservation(r["reservation_id"], asg)
                            send_notification(r["contact"], f"Your reservation {r['reservation_id']} is confirmed (Table {asg}).")
                            assigned_count += 1
                st.success(f"Batch assignment completed. Assigned {assigned_count} reservations.")
                st.experimental_rerun()

st.markdown("---")
st.caption("Notes: This is a demo app. Replace notification placeholders with Twilio/SMTP for real notifications. For production, secure admin properly and consider multi-user auth.")
