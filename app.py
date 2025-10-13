import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ------------------------------------------------------------
# DATABASE SETUP (auto-fix missing columns)
# ------------------------------------------------------------
conn = sqlite3.connect('reservations.db', check_same_thread=False)
c = conn.cursor()

# Create base table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        time TEXT,
        guests INTEGER,
        status TEXT
    )
''')
conn.commit()

# Check for missing columns and add if necessary
existing_cols = [col[1] for col in c.execute("PRAGMA table_info(reservations);").fetchall()]
if "contact" not in existing_cols:
    try:
        c.execute("ALTER TABLE reservations ADD COLUMN contact TEXT;")
        conn.commit()
    except Exception:
        pass

if "table_number" not in existing_cols:
    try:
        c.execute("ALTER TABLE reservations ADD COLUMN table_number TEXT;")
        conn.commit()
    except Exception:
        pass

# ------------------------------------------------------------
# TABLE CAPACITY MAPPING
# ------------------------------------------------------------
TABLES = {
    "Table 1": 2,
    "Table 2": 4,
    "Table 3": 4,
    "Table 4": 6,
    "Table 5": 6,
    "Table 6": 8
}

# ------------------------------------------------------------
# STREAMLIT UI
# ------------------------------------------------------------
st.set_page_config(page_title="5&2 Coffeehouse Reservation System", layout="centered")

st.sidebar.title("5&2 Coffeehouse System")
role = st.sidebar.selectbox("Login as:", ["Customer", "Admin"])

# ------------------------------------------------------------
# CUSTOMER INTERFACE
# ------------------------------------------------------------
if role == "Customer":
    st.title("☕ 5&2 Coffeehouse")

    tab1, tab2 = st.tabs(["Reserve a Table", "View My Reservations"])

    # Reserve tab
    with tab1:
        st.subheader("Reserve a Table")
        name = st.text_input("Name:")
        contact = st.text_input("Email or Phone:")
        date = st.date_input("Date:")
        time = st.time_input("Time:")
        guests = st.number_input("Guests:", min_value=1, max_value=10, step=1)

        if st.button("Submit Reservation"):
            if name.strip() == "" or contact.strip() == "":
                st.warning("⚠️ Please fill in both Name and Contact.")
            else:
                # Auto-assign table based on group size
                assigned_table = None
                for table, capacity in TABLES.items():
                    if guests <= capacity:
                        assigned_table = table
                        break

                if assigned_table is None:
                    st.error("❌ No suitable table available for that group size.")
                else:
                    formatted_time = time.strftime("%I:%M %p")
                    c.execute("""
                        INSERT INTO reservations (name, contact, date, time, guests, status, table_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (name, contact, str(date), formatted_time, guests, "Confirmed", assigned_table))
                    conn.commit()
                    st.success(f"✅ Reservation Confirmed! Assigned to {assigned_table}")

    # View reservations tab
    with tab2:
        st.subheader("View My Reservations")
        search_contact = st.text_input("Enter your Email or Phone:")
        if st.button("View Reservations"):
            if search_contact.strip() == "":
                st.warning("Please enter your contact information to search.")
            else:
                df = pd.read_sql("SELECT * FROM reservations WHERE contact=?", conn, params=(search_contact,))
                if df.empty:
                    st.info("No reservations found for this contact.")
                else:
                    df['time'] = pd.to_datetime(df['time'], errors='coerce').dt.strftime("%I:%M %p")
                    st.dataframe(df[['id', 'name', 'date', 'time', 'guests', 'status', 'table_number']])

# ------------------------------------------------------------
# ADMIN INTERFACE
# ------------------------------------------------------------
elif role == "Admin":
    st.title("🛠️ 5&2 Coffeehouse Dashboard")
    admin_pass = st.text_input("Enter Admin Password:", type="password")

    if admin_pass == "admin123":  # You can change this
        st.success("Access Granted ✅")

        tab1, tab2 = st.tabs(["View Reservations", "Manage Table"])

        # View all reservations
        with tab1:
            df = pd.read_sql("SELECT * FROM reservations", conn)
            if df.empty:
                st.info("No reservations yet.")
            else:
                df['time'] = pd.to_datetime(df['time'], errors='coerce').dt.strftime("%I:%M %p")
                st.dataframe(df[['id', 'name', 'date', 'time', 'guests', 'status', 'table_number']])

        # Manage reservations
        with tab2:
            st.subheader("Manage Reservation Status")
            res_id = st.number_input("Reservation ID:", min_value=1, step=1)
            action = st.selectbox("Select Action:", ["Cancel Reservation", "Mark as Completed"])

            if st.button("Update Status"):
                c.execute("SELECT * FROM reservations WHERE id=?", (res_id,))
                if c.fetchone():
                    new_status = "Cancelled" if action == "Cancel Reservation" else "Completed"
                    c.execute("UPDATE reservations SET status=? WHERE id=?", (new_status, res_id))
                    conn.commit()
                    st.success(f"✅ Reservation #{res_id} marked as {new_status}.")
                else:
                    st.error("❌ Reservation ID not found.")
    else:
        if admin_pass != "":
            st.error("Incorrect password. Please try again.")
