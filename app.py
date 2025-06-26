import streamlit as st
from utils import parse_time, check_availability, book_meeting

st.set_page_config(page_title="Calendar Agent", page_icon="📅")
st.title("📅 AI Calendar Booking Assistant")

# Session state to store conversation history
if "chat" not in st.session_state:
    st.session_state.chat = []

# Chat input from user
user_input = st.chat_input("Ask me to book or check a meeting slot...")

def handle_message(message):
    dt = parse_time(message)
    if not dt:
        return "⚠️ Invalid time. Please try something like 'Book a meeting tomorrow at 3 PM'."

    message_lower = message.lower()
    if "free" in message_lower or "available" in message_lower or "slot" in message_lower or "do i have" in message_lower:
        if check_availability(dt):
            return f"✅ You are free on {dt.strftime('%A, %d %B %Y %I:%M %p')}."
        else:
            return f"❌ You're not available at {dt.strftime('%A, %d %B %Y %I:%M %p')}."

    if check_availability(dt):
        return book_meeting(dt)
    else:
        return f"❌ You're not available at {dt.strftime('%A, %d %B %Y %I:%M %p')}."

# Process user input
if user_input:
    st.session_state.chat.append(("user", user_input))
    with st.spinner("Thinking..."):
        bot_reply = handle_message(user_input)
    st.session_state.chat.append(("assistant", bot_reply))

# Display chat history
for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)
