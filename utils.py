from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import dateparser

# Setup Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)
calendar_id = 'primary'

# Parse time from natural language
def parse_time(text):
    # Handle vague phrases manually
    now = datetime.datetime.now()
    text = text.lower()

    if "tomorrow afternoon" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=15, minute=0)  # 3 PM
    elif "tomorrow morning" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=10, minute=0)
    elif "tomorrow evening" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=18, minute=0)
    else:
        # Fallback to dateparser
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


# ✅ Function 1: Check availability
def check_availability(text):
    dt = parse_time(text)
    if not dt:
        return "Couldn't understand the time."

    start = dt.isoformat()
    end = (dt + datetime.timedelta(hours=1)).isoformat()

    events = service.events().list(
        calendarId=calendar_id,
        timeMin=start,
        timeMax=end,
        singleEvents=True
    ).execute()

    if not events.get('items'):
        return "Available!"
    else:
        return "Not available at that time."

# ✅ Function 2: Book meeting
def book_meeting(text):
    dt = parse_time(text)
    if not dt:
        return "Invalid time."

    start = dt.isoformat()
    end = (dt + datetime.timedelta(hours=1)).isoformat()

    event = {
        'summary': 'Meeting via AI Agent',
        'start': {'dateTime': start, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end, 'timeZone': 'Asia/Kolkata'},
    }

    service.events().insert(calendarId=calendar_id, body=event).execute()
    return f"Meeting booked for {dt.strftime('%A, %d %B %Y %I:%M %p')}"
