from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import dateparser
import calendar
import pytz
import streamlit as st

# Setup Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = None
service = None
try:
    creds = service_account.Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=creds)
    calendar_id = 'primary'
except Exception as e:
    st.error(f"Error loading Google service account credentials: {e}")
    st.info("Please check your gcp_service_account secret in Streamlit.")

# Parse time from natural language
def parse_time(text):
    now = datetime.datetime.now()
    text = text.lower()

    if "tomorrow afternoon" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=15, minute=0, second=0, microsecond=0)
    elif "tomorrow morning" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)
    elif "tomorrow evening" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=18, minute=0, second=0, microsecond=0)
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
        if dt is None:
            # fallback for weekday phrases like "this Friday"
            for weekday in list(calendar.day_name):
                if weekday.lower() in text:
                    target_weekday = list(calendar.day_name).index(weekday)
                    today_weekday = now.weekday()
                    days_ahead = (target_weekday - today_weekday + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    dt = now + datetime.timedelta(days=days_ahead)
                    dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)
                    break

    print(f"DEBUG: Original text: '{text}', Parsed time: {dt}")
    return dt

# Check availability
def check_availability(text):
    if service is None:
        return "Calendar service is not available due to a configuration error."

    dt = parse_time(text)
    if not dt:
        return "I couldn't understand the date and/or time you provided. Please try again."

    india_tz = pytz.timezone('Asia/Kolkata')

    time_specified_in_text = any(k in text for k in ["am", "pm", "morning", "afternoon", "evening", "oclock", "o'clock", ":"])

    is_full_day_query = (
        (dt.hour == 0 and dt.minute == 0 and not time_specified_in_text)
        or ("all day" in text)
        or ("entire day" in text)
        or ("whole day" in text)
        or ("any time" in text)
    )

    if is_full_day_query:
        start_time_iso = india_tz.localize(dt.replace(hour=0, minute=0, second=0)).isoformat()
        end_time_iso = india_tz.localize(dt.replace(hour=23, minute=59, second=59)).isoformat()
        query_description = f"all day on {dt.strftime('%A, %d %B %Y')}"
    else:
        start_time_iso = india_tz.localize(dt).isoformat()
        end_time_iso = india_tz.localize(dt + datetime.timedelta(hours=1)).isoformat()
        query_description = f"{dt.strftime('%A, %d %B %Y at %I:%M %p')}"

    print(f"DEBUG: Checking availability from {start_time_iso} to {end_time_iso}")

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time_iso,
            timeMax=end_time_iso,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return f"You appear to be free {query_description}!"
        else:
            summaries = []
            for event in events:
                start_dt = event['start'].get('dateTime')
                end_dt = event['end'].get('dateTime')
                if start_dt and end_dt:
                    summaries.append(f"'{event.get('summary', 'No Title')}' from {start_dt} to {end_dt}")
                else:
                    summaries.append(f"All-day event: '{event.get('summary', 'No Title')}'")
            return f"You have these events {query_description}: {', '.join(summaries)}. So you are not fully free."

    except Exception as e:
        return f"An error occurred while checking your calendar: {e}"

# Book a meeting
def book_meeting(text):
    if service is None:
        return "Calendar service is not available due to a configuration error."

    dt = parse_time(text)
    if not dt:
        return "I couldn't understand the date/time for booking. Please try again."

    india_tz = pytz.timezone('Asia/Kolkata')
    start_time_iso = india_tz.localize(dt).isoformat()
    end_time_iso = india_tz.localize(dt + datetime.timedelta(hours=1)).isoformat()

    event = {
        'summary': 'Meeting via AI Agent',
        'start': {'dateTime': start_time_iso, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time_iso, 'timeZone': 'Asia/Kolkata'},
    }

    print(f"DEBUG: Booking from {start_time_iso} to {end_time_iso}")

    try:
        service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Meeting booked for {dt.strftime('%A, %d %B %Y at %I:%M %p')}."
    except Exception as e:
        return f"An error occurred while booking the meeting: {e}"
