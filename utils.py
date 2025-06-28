from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import dateparser
import calendar
import pytz
import streamlit as st

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
    st.info("Check your gcp_service_account secret in Streamlit.")

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
    elif "tomorrow" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)
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

def check_availability(text):
    if service is None:
        return "Calendar service is not available due to a configuration error."

    dt = parse_time(text)
    if not dt:
        return "I couldn't understand the date you provided. Please try again."

    india_tz = pytz.timezone('Asia/Kolkata')

    day_start = india_tz.localize(dt.replace(hour=9, minute=0, second=0, microsecond=0))
    day_end   = india_tz.localize(dt.replace(hour=17, minute=0, second=0, microsecond=0))

    start_time_iso = day_start.isoformat()
    end_time_iso   = day_end.isoformat()

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time_iso,
            timeMax=end_time_iso,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        busy_periods = []
        for event in events:
            start = event['start'].get('dateTime')
            end   = event['end'].get('dateTime')
            if start and end:
                busy_periods.append((
                    datetime.datetime.fromisoformat(start).astimezone(india_tz),
                    datetime.datetime.fromisoformat(end).astimezone(india_tz)
                ))

        free_slots = []
        current = day_start
        while current + datetime.timedelta(hours=1) <= day_end:
            slot_start = current
            slot_end = current + datetime.timedelta(hours=1)
            overlaps = False
            for busy_start, busy_end in busy_periods:
                if busy_start < slot_end and busy_end > slot_start:
                    overlaps = True
                    break
            if not overlaps:
                free_slots.append(slot_start)
            current += datetime.timedelta(hours=1)

        if not free_slots:
            return f"Sorry, you have no free 1-hour slots on {dt.strftime('%A, %d %B %Y')}."

        st.session_state.available_slots = free_slots

        slot_list = "\n".join(f"- {slot.strftime('%I:%M %p')}" for slot in free_slots)
        return f"Here are your free 1-hour slots on {dt.strftime('%A, %d %B %Y')}:\n{slot_list}\nPlease tell me which one you’d like to book."

    except Exception as e:
        return f"An error occurred while checking your calendar: {e}"

def book_meeting(text):
    if service is None:
        return "Calendar service is not available due to a configuration error."

    dt = parse_time(text)
    if not dt:
        return "I couldn't understand the date/time for booking. Please try again."

    india_tz = pytz.timezone('Asia/Kolkata')
    slot_start = india_tz.localize(dt)
    slot_end   = slot_start + datetime.timedelta(hours=1)

    # check if already booked
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=slot_start.isoformat(),
            timeMax=slot_end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if events:
            return f"That slot at {dt.strftime('%I:%M %p')} is already booked. Please choose another time."

        # no conflicts → book it
        event = {
            'summary': 'Meeting via AI Agent',
            'start': {'dateTime': slot_start.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': slot_end.isoformat(), 'timeZone': 'Asia/Kolkata'},
        }
        service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Meeting booked for {dt.strftime('%A, %d %B %Y at %I:%M %p')}."
    except Exception as e:
        return f"An error occurred while booking the meeting: {e}"
