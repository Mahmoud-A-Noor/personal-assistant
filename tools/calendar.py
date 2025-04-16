"""
Google Calendar operations tool for the personal assistant.
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union
import anyio
import functools
import logging
import re
from pydantic_ai import Tool
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import tzlocal  # For detecting system timezone

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the token.json file.
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

class CalendarTool:
    """Tool for Google Calendar operations."""
    
    def __init__(self):
        load_dotenv()
        self.credentials = None
        self._setup_credentials()
        self.local_tz = tzlocal.get_localzone()  # Get system timezone
        
    def _setup_credentials(self):
        """Set up OAuth2 credentials."""
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            self.credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # Check if we need to update permissions
            if set(self.credentials.scopes) != set(SCOPES):
                print("\nUpdating calendar permissions... Please re-authenticate.")
                os.remove('token.json')
                self.credentials = None
        
        # If there are no (valid) credentials available, let the user log in
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.credentials = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.credentials.to_json())

    async def get_upcoming_events(self, max_results: int = 10) -> List[dict]:
        """Get upcoming events from the primary calendar."""
        try:
            get_fn = functools.partial(self._get_upcoming_events, max_results)
            return await anyio.to_thread.run_sync(get_fn)
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            return []

    async def get_past_events(self, max_results: int = 10, days: Optional[int] = None) -> List[dict]:
        """Get past events from the primary calendar.
        
        Args:
            max_results: Maximum number of events to return
            days: Number of past days to look back (None for all past events)
        """
        try:
            get_fn = functools.partial(self._get_past_events, max_results, days)
            return await anyio.to_thread.run_sync(get_fn)
        except Exception as e:
            logger.error(f"Failed to get past calendar events: {e}")
            return []

    # Internal sync implementations
    def _get_upcoming_events(self, max_results: int) -> List[dict]:
        """Sync implementation for getting upcoming events."""
        service = self._get_service()
        now = datetime.now(self.local_tz).isoformat()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        return [
            {
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date'))
            }
            for event in events
        ]

    def _get_past_events(self, max_results: int, days: Optional[int]) -> List[dict]:
        """Sync implementation for getting past events."""
        
        service = self._get_service()
        now = datetime.now(self.local_tz).isoformat()
        
        # Calculate timeMin if days parameter is provided
        time_min = None
        if days is not None:
            time_min = (datetime.now(self.local_tz) - timedelta(days=days)).isoformat()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return [
            {
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date'))
            }
            for event in events
        ]

    def _get_service(self):
        """Initialize and return the calendar service."""
        return build('calendar', 'v3', credentials=self.credentials)

    def _get_date_formats(self):
        """Return list of supported date formats"""
        return [
            '%Y-%m-%d',      # 2025-04-16
            '%d/%m/%Y',      # 16/04/2025
            '%m/%d/%Y',      # 04/16/2025
            '%B %d',         # April 16
            '%b %d',         # Apr 16
            '%d %B',         # 16 April
            '%d %b',         # 16 Apr
            '%B %d, %Y',     # April 16, 2025
            '%d %B %Y',      # 16 April 2025
        ]
        
    def _try_parse_date(self, date_str: str, fmt: str, now: datetime) -> Optional[datetime]:
        """Try to parse a date string with given format"""
        # Add current year if not in format
        if '%Y' not in fmt:
            date_to_parse = f"{date_str} {now.year}"
            fmt = f"{fmt} %Y"
        else:
            date_to_parse = date_str
            
        date_part = datetime.strptime(date_to_parse, fmt)
        return now.replace(
            year=date_part.year,
            month=date_part.month,
            day=date_part.day
        )
    
    def _parse_time(self, time_str: str, parsed_date: datetime) -> datetime:
        """Parse time string and apply to date"""
        try:
            # Handle formats like "2PM", "2:30PM", "14:00", "14:30"
            am_pm_pattern = re.compile(r'(\d{1,2})(?::(\d{2}))?(?:\s*([AaPp][Mm]))?')
            match = am_pm_pattern.match(time_str.strip())
            
            if match:
                hour, minute, am_pm = match.groups()
                hour = int(hour)
                minute = int(minute) if minute else 0
                
                # Adjust for 12-hour format with AM/PM
                if am_pm and am_pm.lower() == 'pm' and hour < 12:
                    hour += 12
                elif am_pm and am_pm.lower() == 'am' and hour == 12:
                    hour = 0
                    
                # Validate time
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError(f"Invalid time: {time_str}")
                    
                return parsed_date.replace(hour=hour, minute=minute, second=0)
            
            # Try with 24-hour format
            for fmt in ['%H:%M', '%H%M']:
                try:
                    time_part = datetime.strptime(time_str, fmt)
                    return parsed_date.replace(
                        hour=time_part.hour,
                        minute=time_part.minute,
                        second=0
                    )
                except ValueError:
                    continue
                    
            raise ValueError(f"Could not parse time: {time_str}")
        except Exception as e:
            logger.error(f"Error parsing time: {str(e)}")
            raise ValueError(f"Could not understand the time: {time_str}")
        
    def get_event_details(self, calendar_id: str, event_id: str) -> dict:
        """
        Get detailed information about a specific calendar event.
        
        Args:
            calendar_id: Calendar ID (use 'primary' for primary calendar)
            event_id: Event ID to retrieve
            
        Returns:
            Event details dictionary
        """
        return self._get_service().events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

    def get_conflicting_event_details(self, calendar_id: str, start: datetime, end: datetime) -> list:
        """
        Get details of events that conflict with a given time range.
        
        Args:
            calendar_id: Calendar ID (use 'primary' for primary calendar)
            start: Start datetime 
            end: End datetime
            
        Returns:
            List of conflicting event details
        """
        # Ensure timezone awareness
        if start.tzinfo is None:
            start = start.astimezone(self.local_tz)
        if end.tzinfo is None:
            end = end.astimezone(self.local_tz)
            
        # Convert to RFC3339 format
        start_rfc = start.isoformat()
        end_rfc = end.isoformat()
        
        # Check for conflicts using freebusy
        freebusy = self._get_service().freebusy().query(body={
            'timeMin': start_rfc,
            'timeMax': end_rfc,
            'items': [{'id': calendar_id}]
        }).execute()
        
        conflicts = freebusy['calendars'][calendar_id].get('busy', [])
        if not conflicts:
            return []
            
        # Get the actual events in this time range to provide more details
        events_result = self._get_service().events().list(
            calendarId=calendar_id,
            timeMin=start_rfc,
            timeMax=end_rfc,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format conflict information
        conflict_details = []
        for event in events:
            conflict_details.append({
                'id': event.get('id'),
                'summary': event.get('summary', 'Untitled Event'),
                'start': event.get('start', {}).get('dateTime'),
                'end': event.get('end', {}).get('dateTime'),
                'description': event.get('description', '')
            })
            
        return conflict_details

    def get_today(self) -> str:
        """Get today's date in local timezone."""
        return datetime.now(self.local_tz).strftime('%Y-%m-%d')
        
    def create_event(self, summary: str, 
                          start_hour: int, start_minute: int,
                          end_hour: int, end_minute: int,
                          days_from_today: int = 0,
                          description: str = None,
                          calendar_id: str = 'primary',
                          force_create: bool = False) -> dict:
        """
        Create event with enhanced conflict checking.
        Set force_create=True to schedule despite conflicts.
        """
        try:
            # Validate calendar ID exists
            try:
                self._get_service().calendars().get(calendarId=calendar_id).execute()
            except Exception:
                return {
                    'status': 'error',
                    'message': f"Calendar ID '{calendar_id}' not found. Using 'primary' calendar instead.",
                    'calendar_id': 'primary'
                }
            
            # Create in local timezone
            today = datetime.now(self.local_tz).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            event_date = today + timedelta(days=days_from_today)
            
            start_local = event_date.replace(hour=start_hour, minute=start_minute)
            end_local = event_date.replace(hour=end_hour, minute=end_minute)
            
            if end_local < start_local:
                end_local += timedelta(days=1)
                
            # Convert to UTC for Google
            start_utc = start_local.astimezone(self.local_tz)
            end_utc = end_local.astimezone(self.local_tz)
            
            # Enhanced conflict check with buffer time
            time_min = (start_utc - timedelta(minutes=15)).isoformat()
            time_max = (end_utc + timedelta(minutes=15)).isoformat()
            
            freebusy = self._get_service().freebusy().query(body={
                'timeMin': time_min,
                'timeMax': time_max,
                'items': [{'id': calendar_id}],
                'timeZone': 'UTC'
            }).execute()
            
            busy_periods = freebusy['calendars'][calendar_id].get('busy', [])
            if busy_periods and not force_create:
                # Get full event details for conflicts
                conflicts = []
                for period in busy_periods:
                    events = self._get_service().events().list(
                        calendarId=calendar_id,
                        timeMin=period['start'],
                        timeMax=period['end'],
                        singleEvents=True
                    ).execute().get('items', [])
                    
                    for event in events:
                        event_start = datetime.fromisoformat(event['start']['dateTime'])
                        event_end = datetime.fromisoformat(event['end']['dateTime'])
                        
                        # Check if events actually overlap (not just adjacent)
                        if not (event_end <= start_utc or event_start >= end_utc):
                            conflicts.append({
                                'id': event['id'],
                                'summary': event.get('summary', 'Busy'),
                                'start': event_start.astimezone(self.local_tz).strftime('%I:%M %p'),
                                'end': event_end.astimezone(self.local_tz).strftime('%I:%M %p'),
                                'date': event_start.astimezone(self.local_tz).strftime('%A, %B %d')
                            })
                
                if conflicts:
                    conflict_msg = "Found scheduling conflicts:\n"
                    for conflict in conflicts:
                        conflict_msg += f"- {conflict['summary']} on {conflict['date']} from {conflict['start']} to {conflict['end']}\n"
                    
                    conflict_msg += f"\nYour event: {summary} on {start_local.strftime('%A, %B %d')} from {start_local.strftime('%I:%M %p')} to {end_local.strftime('%I:%M %p')}"
                    if description:
                        conflict_msg += f"\nLocation: {description}"
                    
                    return {
                        'status': 'conflict',
                        'message': conflict_msg,
                        'conflicts': conflicts,
                        'proposed_event': {
                            'summary': summary,
                            'date': start_local.strftime('%A, %B %d'),
                            'start': start_local.strftime('%I:%M %p'),
                            'end': end_local.strftime('%I:%M %p'),
                            'location': description
                        },
                        'suggestion': "Would you like to schedule anyway? (yes/no)"
                    }
            
            # Create the event (stored in UTC by Google)
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_utc.isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_utc.isoformat(),
                    'timeZone': 'UTC'
                }
            }
            
            created_event = self._get_service().events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            # Convert back to local time for response
            created_event['start']['localTime'] = start_local.isoformat()
            created_event['end']['localTime'] = end_local.isoformat()
            created_event['timezone'] = str(self.local_tz)
            
            return {
                'status': 'success',
                'message': f"Event '{summary}' scheduled for {start_local.strftime('%A, %B %d at %I:%M %p')}",
                'details': created_event
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to create event: {str(e)}"
            }

def get_calendar_tools() -> List[Tool]:
    """Creates calendar management tools."""
    calendar_client = CalendarTool()
    
    return [
        Tool(
            calendar_client.get_upcoming_events,
            name="calendar_get_events",
            description="Get upcoming events from the primary calendar"
        ),
        Tool(
            calendar_client.get_past_events,
            name="calendar_get_past_events",
            description="Get past events from the primary calendar"
        ),
        Tool(
            calendar_client.get_today,
            name="calendar_get_today",
            description="Get today's date in YYYY-MM-DD format"
        ),
        Tool(
            calendar_client.create_event,
            name="calendar_create_event",
            description="Create event with conflict checking. Args: summary, start_hour (0-23), start_minute (0-59), end_hour (0-23), end_minute (0-59), days_from_today=0, description=None, calendar_id='primary', force_create=False"
        ),
        Tool(
            calendar_client.update_event,
            name="calendar_update_event",
            description="Update an existing calendar event. Args: calendar_id, event_id, summary, start, end, description"
        )
    ]
