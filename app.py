import streamlit as st
from utils import parse_time, check_availability, book_meeting

st.set_page_config(page_title="Calendar Agent", page_icon="📅")
st.title("📅 AI Calendar Booking Assistant")

# Initialize chat history
if "chat" not in st.session_state:
    st.session_state.chat = []

# Function to process message and handle booking
def handle_message(message):
    dt = parse_time(message)
    if not dt:
        return "⚠️ Invalid time. Please try something like 'Book a meeting tomorrow at 3 PM'."

    if not check_availability(dt):
        return f"❌ Sorry, you're not available at {dt.strftime('%A, %d %B %Y %I:%M %p')}."

    book_meeting(dt)
    return f"✅ Meeting booked for {dt.strftime('%A, %d %B %Y %I:%M %p')}"

# Input box for the user
user_input = st.chat_input("Ask me to book or check a meeting slot...")

# If user sends a message
if user_input:
    # Add user message to history
    st.session_state.chat.append(("user", user_input))

    # Process input and get bot reply
    with st.spinner("Checking your calendar..."):
        bot_reply = handle_message(user_input)

    # Add bot reply to history
    st.session_state.chat.append(("assistant", bot_reply))

# Display the conversation
for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)
