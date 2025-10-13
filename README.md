APPLICATION PROJECT IN ELECTIVES, SOFTWARE LEC AND LAB

Project Overview
ReserVision is an artificial intelligence (AI)-simulated small café table reservation system designed specifically for 5&2 Coffeehouse.
It provides customers with the possibility to smartly book tables through an AI-supported table assignment system, moreover the admins can control tables, supervise reservations, and check system activities— all in real-time.
The whole system is implemented in Python utilizing Streamlit as the client side framework and SQLite as the data source for storing non-volatile data on the back end.

Key Features
AI-Assisted Table Suggestion — Simulation of neural decision logic that picks the best table according to group size, date, and time.
Customer Portal — Reserve, manage, and cancel your meal table bookings.
Admin Dashboard — Secure entry for admins to monitor/control all bookings, add/remove tables, and check real-time occupancy.
Activity Logging — Monitors all system activities (bookings, cancellations, updates).

Technology Stack
Programming Language - Python 3.10+
Framework	- Streamlit
Database - SQLite
Libraries	- pandas, sqlite3, datetime, uuid
AI Logic	- Simulated heuristic neural model (Python logic)

Installation & Setup
OPEN THRU WEBSITE: https://reservision-p5yxnfxbdtqgvgk4pjhn86.streamlit.app/?fbclid=IwY2xjawNaAqhleHRuA2FlbQIxMABicmlkETFhRUVPODh3d0JHZkNLMUdBAR4-F7OGrk8xVCQcCNg17-FV2bWyM5KXLtX_4_TLDIHHojew3G9JkZGP30A45w_aem_5BUcwo4qdzmrsnqGno7wZA 
OR YOU CAN INSTALL DEPENDENCIES:
pip install streamlit pandas or pip install streamlit
AFTER THAT YOU CAN RUN IT: (USING THIS)
python -m streamlit run app.py

System Roles
Customer
Reserve a table (AI-assisted selection)
View and cancel reservations using contact info
Receive on-screen simulated notifications

Admin
Login using password: admin123
View all reservations
Add / remove tables
Monitor daily table occupancy
Manage reservations (cancel/update)
Access the activity log

Future Improvements
Real-time SMS/email notifications
Cloud-hosted database (Firebase/MySQL)
Online payment integration
Mobile app version
Advanced AI model (customer preference learning)

Developers
Team ReserVision
Caniedo Mark Nicolai M. 
Lagrimas, Melito Jr A.
Pamandanan, Karl Louise B.
COE222
