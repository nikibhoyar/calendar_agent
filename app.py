import streamlit as st
from utils import check_availability, book_meeting

st.set_page_config(page_title="Calendar Agent", page_icon="📅")
st.title("📅 AI Calendar Booking Assistant")

# initialize chat memory
if "chat" not in st.session_state:
    st.session_state.chat = []

# get user input
user_input = st.chat_input("Ask me to book or check a meeting slot...")

if user_input:
    st.session_state.chat.append(("user", user_input))

    message = user_input.lower()

    # enhanced intent detection
    if any(word in message for word in ["available", "free", "slot", "slots", "availability", "time"]):
        reply = check_availability(message)
    elif any(word in message for word in ["book", "schedule", "reserve", "confirm"]):
        reply = book_meeting(message)
    elif any(word in message for word in ["hi", "hello", "hey"]):
        reply = "👋 Hi there! I can help you check availability or book a meeting. Try saying 'slots for tomorrow' or 'book a meeting Friday at 2 PM'."
    elif "available_slots" in st.session_state:
        # user trying to confirm a slot
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
        reply = (
            "🤖 I'm not sure what you meant. "
            "You can ask me to check your calendar or book a meeting, "
            "like 'check availability tomorrow' or 'book at 4 PM next Friday'."
        )

    st.session_state.chat.append(("bot", reply))

# render chat
for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)
