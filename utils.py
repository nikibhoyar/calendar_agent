# utils.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import dateparser
import streamlit as st  # NEW: Import streamlit to access st.secrets

# Setup Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar'] # Use a broad scope for read/write access

# --- CRITICAL CHANGE: Load credentials from st.secrets ---
creds = None # Initialize creds to None
service = None # Initialize service to None
try:
    # Ensure st.secrets["gcp_service_account"] is correctly configured in your Streamlit secrets
    creds = service_account.Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), # Access the secret as a dictionary
        scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=creds)
    calendar_id = 'primary' # This typically refers to the primary calendar of the service account or impersonated user
except Exception as e:
    st.error(f"Error loading Google service account credentials: {e}")
    st.info("Please ensure your `gcp_service_account` secret is correctly configured in Streamlit Cloud. Refer to previous instructions for the TOML format with triple quotes for the private_key.")
    # If credentials fail, the 'service' object will remain None, and functions will gracefully fail.


# Parse time from natural language
def parse_time(text):
    now = datetime.datetime.now()
    text = text.lower()

    # Manual overrides for specific phrases with default times
    # These ensure predictable times for common vague requests
    if "tomorrow afternoon" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=15, minute=0, second=0, microsecond=0)  # 3 PM
    elif "tomorrow morning" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)  # 10 AM
    elif "tomorrow evening" in text:
        dt = now + datetime.timedelta(days=1)
        dt = dt.replace(hour=18, minute=0, second=0, microsecond=0)  # 6 PM
    else:
        # Fallback to dateparser for general parsing
        # dateparser usually returns midnight (00:00:00) if no time is specified,
        # which we'll handle in check_availability for full-day queries.
        dt = dateparser.parse(
            text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RETURN_AS_TIMEZONE_AWARE': False, # Keep as False; ISO format with 'Asia/Kolkata' is handled by Calendar API
                'TIMEZONE': 'Asia/Kolkata',        # Input timezone
                'TO_TIMEZONE': 'Asia/Kolkata',      # Output timezone
                'RELATIVE_BASE': now                # Base for relative dates (e.g., "next Monday")
            }
        )

    print(f"DEBUG: Original text: '{text}', Parsed time: {dt}") # Debugging output
    return dt


# ✅ Function 1: Check availability
def check_availability(text):
    if service is None:
        return "Calendar service is not available due to a configuration error. Please check the app logs for details."

    dt = parse_time(text)
    if not dt:
        return "I couldn't understand the date and/or time you provided. Please try a more specific phrase like 'next Monday at 3 PM' or 'tomorrow morning'."

    # Determine if the user is asking for a specific time or a general day
    # Heuristic: If dateparser returned midnight and the original text didn't specify a time,
    # assume they mean the whole day. Also explicitly check for "all day" phrases.
    time_specified_in_text = any(keyword in text for keyword in ["am", "pm", "morning", "afternoon", "evening", "oclock", "o'clock", ":"])

    is_full_day_query = (
        (dt.hour == 0 and dt.minute == 0 and dt.second == 0 and not time_specified_in_text) or
        ("all day" in text) or ("entire day" in text) or ("whole day" in text) or ("any time" in text)
    )

    if is_full_day_query:
        # For full-day availability, check from start of day to end of day
        start_time_iso = dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_time_iso = dt.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        query_description = f"all day on {dt.strftime('%A, %d %B %Y')}"
    else:
        # For specific time queries, check a 1-hour slot
        start_time_iso = dt.isoformat()
        end_time_iso = (dt + datetime.timedelta(hours=1)).isoformat()
        query_description = f"{dt.strftime('%A, %d %B %Y at %I:%M %p')}"

    print(f"DEBUG: Checking availability for {query_description} (from {start_time_iso} to {end_time_iso})") # Debugging

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time_iso,
            timeMax=end_time_iso,
            singleEvents=True, # Important for recurring events
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return f"You appear to be free {query_description}!"
        else:
            event_summaries = []
            for event in events:
                event_start_dt = event['start'].get('dateTime')
                event_end_dt = event['end'].get('dateTime')

                if event_start_dt and event_end_dt: # Timed event
                    try:
                        start_parsed = datetime.datetime.fromisoformat(event_start_dt)
                        end_parsed = datetime.datetime.fromisoformat(event_end_dt)
                        event_summaries.append(f"'{event.get('summary', 'No Title')}' from {start_parsed.strftime('%I:%M %p')} to {end_parsed.strftime('%I:%M %p')}")
                    except ValueError: # Fallback if isoformat fails (e.g., malformed string)
                        event_summaries.append(f"'{event.get('summary', 'No Title')}' (time parsing error)")
                else: # All-day event or date-only event
                    event_summaries.append(f"All-day event: '{event.get('summary', 'No Title')}'")

            return f"You have existing event(s) {query_description}: {'; '.join(event_summaries)}. You are not entirely free during that period."

    except Exception as e:
        return f"An error occurred while checking your calendar: {e}. Please ensure the service account has the necessary Google Calendar API permissions."

# ✅ Function 2: Book meeting
def book_meeting(text):
    if service is None:
        return "Calendar service is not available due to a configuration error. Please check the app logs for details."

    dt = parse_time(text)
    if not dt:
        return "I couldn't understand the time for booking. Please try something like 'Book a meeting tomorrow at 3 PM'."

    # Booking always assumes a 1-hour meeting unless specified otherwise (not implemented here)
    start_time_iso = dt.isoformat()
    end_time_iso = (dt + datetime.timedelta(hours=1)).isoformat()

    event = {
        'summary': 'Meeting via AI Agent',
        'start': {'dateTime': start_time_iso, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time_iso, 'timeZone': 'Asia/Kolkata'},
    }

    print(f"DEBUG: Attempting to book meeting from {start_time_iso} to {end_time_iso}") # Debugging

    try:
        service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Meeting booked successfully for {dt.strftime('%A, %d %B %Y %I:%M %p')}."
    except Exception as e:
        return f"An error occurred while booking the meeting: {e}. Please ensure the service account has the necessary Google Calendar API permissions."
