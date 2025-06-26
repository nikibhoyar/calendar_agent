# app.py
import streamlit as st
# import requests # REMOVE THIS LINE - no longer needed for calling local FastAPI
from utils import check_availability, book_meeting # Import functions directly

st.set_page_config(page_title="Calendar Agent", page_icon="📅")
st.title("📅 AI Calendar Booking Assistant")

# Session state to store conversation
if "chat" not in st.session_state:
    st.session_state.chat = []

# Input from user
user_input = st.chat_input("Ask me to book or check a meeting slot...")

if user_input:
    # Add user message
    st.session_state.chat.append(("user", user_input))

    # --- Integrated logic from main.py ---
    message = user_input.lower()
    
    if "available" in message or "free" in message:
        reply = check_availability(message)
    elif "book" in message or "schedule" in message:
        reply = book_meeting(message)
    else:
        reply = "Please mention if you want to check availability or book a meeting."
    # --- End integrated logic ---

    # Add bot reply
    st.session_state.chat.append(("bot", reply))

# Display chat history
for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)
