import streamlit as st
from utils import check_availability, book_meeting

st.set_page_config(page_title="Calendar Agent", page_icon="📅")
st.title("📅 AI Calendar Booking Assistant")

if "chat" not in st.session_state:
    st.session_state.chat = []

user_input = st.chat_input("Ask me to book or check a meeting slot...")

if user_input:
    st.session_state.chat.append(("user", user_input))

    message = user_input.lower()

    if "available" in message or "free" in message:
        reply = check_availability(message)
    elif "book" in message or "schedule" in message:
        reply = book_meeting(message)
    elif "available_slots" in st.session_state:
        picked_time = None
        for slot in st.session_state.available_slots:
            if slot.strftime("%I:%M %p").lower() in message:
                picked_time = slot
                break
        if picked_time:
            reply = book_meeting(picked_time.strftime("%A %d %B %Y %I:%M %p"))
            del st.session_state.available_slots
        else:
            reply = "Please choose a time from the listed options or type another query."
    else:
        reply = "Please mention if you want to check availability or book a meeting."

    st.session_state.chat.append(("bot", reply))

for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)
