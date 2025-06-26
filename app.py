# app.py
import streamlit as st
import requests

st.set_page_config(page_title="Calendar Agent", page_icon="📅")
st.title("📅 AI Calendar Booking Assistant")

# Session state to store conversation
# Corrected typo here: "not not" -> "not in"
if "chat" not in st.session_state:
    st.session_state.chat = []

# Input from user
user_input = st.chat_input("Ask me to book or check a meeting slot...")

if user_input:
    # Add user message
    st.session_state.chat.append(("user", user_input))

    # Call FastAPI backend
    # This URL depends on how you deploy. For local development, localhost:8000 is common.
    # For Streamlit Cloud with FastAPI in the same repo, it often works.
    try:
        response = requests.post("http://localhost:8000/chat", json={"message": user_input})
        response.raise_for_status() # Raise an exception for HTTP errors
        reply = response.json()["response"]
    except requests.exceptions.ConnectionError:
        reply = "I'm having trouble connecting to the booking service. Please ensure the backend server is running."
    except requests.exceptions.RequestException as e:
        reply = f"An error occurred with the booking service: {e}"


    # Add bot reply
    st.session_state.chat.append(("bot", reply))

# Display chat history
for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)
