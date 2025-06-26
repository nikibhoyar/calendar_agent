from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import dateparser
import streamlit as st

# Setup Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ✅ Load credentials from Streamlit secrets
creds = service_account.Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]),
    scopes=SCOPES
)

service = build('calendar', 'v3', credentials=creds)
calendar_id = 'primary'

# ✅ Parse time from natural language
def parse_time(text):
    now = datetime.datetime.now()
    text = text.lower()

    # Handle vague phrases manually
    if "tomorrow afternoon" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=15, minute=0)
    elif "tomorrow morning" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=10, minute=0)
    elif "tomorrow evening" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=18, minute=0)
    elif "next monday" in text:
        days_ahead = (7 - now.weekday() + 0) % 7 or 7  # 0 for Monday
        dt = now + datetime.timedelta(days=days_ahead)
        dt = dt.replace(hour=15, minute=0)  # Default time
    else:
        dt = dateparser.parse(
            text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RETURN_AS_TIMEZONE_AWARE': False,
                'TIMEZONE': 'Asia/Kolkata',
                'TO_TIMEZONE': 'Asia/Kolkata',
                'RELATIVE_BASE': now
            }
        )

    print("Parsed time:", dt)
    return dt


# ✅ Check availability
def check_availability(dt):
    start = dt.isoformat()
    end = (dt + datetime.timedelta(hours=1)).isoformat()

    events = service.events().list(
        calendarId=calendar_id,
        timeMin=start,
        timeMax=end,
        singleEvents=True
    ).execute()

    return not events.get('items')  # True if free

# ✅ Book meeting
def book_meeting(dt):
    start = dt.isoformat()
    end = (dt + datetime.timedelta(hours=1)).isoformat()

    event = {
        'summary': 'Meeting via AI Agent',
        'start': {'dateTime': start, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end, 'timeZone': 'Asia/Kolkata'},
    }

    service.events().insert(calendarId=calendar_id, body=event).execute()
    return f"Meeting booked for {dt.strftime('%A, %d %B %Y %I:%M %p')}"
