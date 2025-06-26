# app.py
import streamlit as st
import requests

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

    # Call FastAPI backend
    response = requests.post("http://localhost:8000/chat", json={"message": user_input})
    reply = response.json()["response"]

    # Add bot reply
    st.session_state.chat.append(("bot", reply))

# Display chat history
for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)
