"""
Google Calendar operations tool for the personal assistant.
"""
import os
from datetime import datetime, timezone, timedelta
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
        """Initialize with OAuth2 credentials."""
        self.credentials = None
        self._setup_credentials()

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
        now = datetime.now(timezone.utc).isoformat()
        
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
                'summary': event.get('summary', 'No title'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date'))
            }
            for event in events
        ]

    def _get_past_events(self, max_results: int, days: Optional[int]) -> List[dict]:
        """Sync implementation for getting past events."""
        from datetime import datetime, timedelta, timezone
        
        service = self._get_service()
        now = datetime.now(timezone.utc).isoformat()
        
        # Calculate timeMin if days parameter is provided
        time_min = None
        if days is not None:
            time_min = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
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

    def _parse_datetime(self, date_str: str, time_str: str = None) -> datetime:
        """
        Parse date and time strings into a datetime object.
        Handles various formats and ensures timezone awareness.
        """
        try:
            now = datetime.now().replace(microsecond=0)
            parsed_date = None
            
            # Handle relative dates
            if date_str.lower() == 'today':
                parsed_date = now
            elif date_str.lower() == 'tomorrow':
                parsed_date = now + timedelta(days=1)
            elif date_str.lower() == 'yesterday':
                parsed_date = now - timedelta(days=1)
            else:
                # Try different date formats
                for fmt in self._get_date_formats():
                    try:
                        date_part = self._try_parse_date(date_str, fmt, now)
                        if date_part:
                            parsed_date = date_part
                            break
                    except ValueError:
                        continue
                
            if parsed_date is None:
                raise ValueError(f"Could not parse date: {date_str}")
                
            # Parse time if provided
            if time_str:
                parsed_date = self._parse_time(time_str, parsed_date)
            else:
                parsed_date = parsed_date.replace(hour=0, minute=0, second=0)
                
            # Ensure timezone awareness
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.astimezone(timezone.utc)
                
            return parsed_date
            
        except Exception as e:
            logger.error(f"Error parsing datetime: {str(e)}")
            raise ValueError(f"Could not understand the date/time: {date_str} {time_str}")
    
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
        
    def _parse_event_time(self, date_str: str, start_time: str, end_time: str = None, duration_minutes: int = None) -> Tuple[datetime, datetime]:
        """
        Parse event start and end times.
        
        Args:
            date_str: Date string
            start_time: Start time string
            end_time: End time string (optional if duration_minutes is provided)
            duration_minutes: Duration in minutes (optional if end_time is provided)
            
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        start_dt = self._parse_datetime(date_str, start_time)
        
        # If end_time provided, use it
        if end_time:
            end_dt = self._parse_datetime(date_str, end_time)
            # If end time is before start time, assume it's the next day
            if end_dt < start_dt:
                end_dt = end_dt + timedelta(days=1)
        # Otherwise use duration
        elif duration_minutes:
            end_dt = start_dt + timedelta(minutes=duration_minutes)
        # Default to 1 hour
        else:
            end_dt = start_dt + timedelta(hours=1)
            
        return start_dt, end_dt

    def create_event(self, calendar_id: str, summary: str, start: Union[datetime, str], end: Union[datetime, str] = None, 
                       description: str = None, date: str = None, start_time: str = None, end_time: str = None, 
                       duration_minutes: int = None) -> dict:
        """
        Create a new calendar event.
        
        Args:
            calendar_id: Calendar ID (use 'primary' for primary calendar)
            summary: Event title/summary
            start: Start datetime (if datetime object)
            end: End datetime (if datetime object)
            description: Event description
            date: Date string (if start is not a datetime)
            start_time: Start time string (if start is not a datetime)
            end_time: End time string (if end is not a datetime)
            duration_minutes: Duration in minutes (alternative to end_time)
            
        Returns:
            Created event details
        """
        # Parse datetime inputs if needed
        if isinstance(start, datetime):
            start_dt = start
            end_dt = end if isinstance(end, datetime) else start + timedelta(hours=1)
        else:
            # Use provided date or start as date
            event_date = date or start
            event_start_time = start_time or start
            start_dt, end_dt = self._parse_event_time(event_date, event_start_time, end_time, duration_minutes)
            
        # Ensure timezone awareness
        if start_dt.tzinfo is None:
            start_dt = start_dt.astimezone(timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.astimezone(timezone.utc)
            
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC'
            }
        }

        return self._get_service().events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

    def create_event_with_conflict_check(self, calendar_id: str, summary: str, start: Union[datetime, str], end: Union[datetime, str] = None, 
                       description: str = None, date: str = None, start_time: str = None, end_time: str = None, 
                       duration_minutes: int = None) -> dict:
        """
        Create event with conflict checking. Returns created event or conflict details.
        
        Args:
            calendar_id: Calendar ID (use 'primary' for primary calendar)
            summary: Event title/summary
            start: Start datetime (if datetime object)
            end: End datetime (if datetime object)
            description: Event description
            date: Date string (if start is not a datetime)
            start_time: Start time string (if start is not a datetime)
            end_time: End time string (if end is not a datetime)
            duration_minutes: Duration in minutes (alternative to end_time)
            
        Returns:
            Created event details or conflict information
        """
        try:
            # Parse datetime inputs if needed
            if isinstance(start, datetime):
                start_dt = start
                end_dt = end if isinstance(end, datetime) else start + timedelta(hours=1)
            else:
                # Use provided date or start as date
                event_date = date or start
                event_start_time = start_time or start
                start_dt, end_dt = self._parse_event_time(event_date, event_start_time, end_time, duration_minutes)
                
            # Get detailed conflict information
            conflicting_events = self.get_conflicting_event_details(calendar_id, start_dt, end_dt)
            
            if conflicting_events:
                return {
                    'status': 'conflict',
                    'message': f'Time conflict with {len(conflicting_events)} existing events',
                    'conflicts': conflicting_events,
                    'proposed_event': {
                        'summary': summary,
                        'start': start_dt.isoformat(),
                        'end': end_dt.isoformat()
                    }
                }
            
            # No conflicts - create event
            return self.create_event(calendar_id, summary, start_dt, end_dt, description)
            
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'suggestion': 'Please provide dates/times in formats like "tomorrow 2PM" or "2025-04-16 14:00"'
            }

    def update_event(self, calendar_id: str, event_id: str, summary: str = None, 
                   start: Union[datetime, str] = None, end: Union[datetime, str] = None,
                   description: str = None, date: str = None, start_time: str = None, 
                   end_time: str = None, duration_minutes: int = None) -> dict:
        """
        Update an existing calendar event.
        
        Args:
            calendar_id: Calendar ID (use 'primary' for primary calendar)
            event_id: Event ID to update
            summary: New event title/summary (optional)
            start: New start datetime (if datetime object) (optional)
            end: New end datetime (if datetime object) (optional)
            description: New event description (optional)
            date: New date string (if start is not a datetime) (optional)
            start_time: New start time string (if start is not a datetime) (optional)
            end_time: New end time string (if end is not a datetime) (optional)
            duration_minutes: New duration in minutes (alternative to end_time) (optional)
            
        Returns:
            Updated event details
        """
        # Get current event to update only provided fields
        current_event = self._get_service().events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Create updated event dict, starting with the current event
        updated_event = {}
        
        # Update summary if provided
        if summary:
            updated_event['summary'] = summary
        elif 'summary' in current_event:
            updated_event['summary'] = current_event['summary']
            
        # Update description if provided
        if description:
            updated_event['description'] = description
        elif 'description' in current_event:
            updated_event['description'] = current_event['description']
            
        # Update start/end times if provided
        start_dt = None
        end_dt = None
        
        # Parse datetime inputs if needed
        if isinstance(start, datetime):
            start_dt = start
        elif date and start_time:
            start_dt = self._parse_datetime(date, start_time)
            
        if isinstance(end, datetime):
            end_dt = end
        elif date and end_time:
            end_dt = self._parse_datetime(date, end_time)
        elif start_dt and duration_minutes:
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            
        # Only update start/end if new values provided
        if start_dt:
            updated_event['start'] = {
                'dateTime': start_dt.astimezone(timezone.utc).isoformat(),
                'timeZone': 'UTC'
            }
        elif 'start' in current_event:
            updated_event['start'] = current_event['start']
            
        if end_dt:
            updated_event['end'] = {
                'dateTime': end_dt.astimezone(timezone.utc).isoformat(),
                'timeZone': 'UTC'
            }
        elif 'end' in current_event:
            updated_event['end'] = current_event['end']
            
        # Update other properties from current event
        for key, value in current_event.items():
            if key not in updated_event and key not in ['etag', 'kind', 'status', 'htmlLink', 'created', 'updated', 'iCalUID', 'sequence']:
                updated_event[key] = value
                
        # Perform the update
        return self._get_service().events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=updated_event
        ).execute()

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
            start = start.astimezone(timezone.utc)
        if end.tzinfo is None:
            end = end.astimezone(timezone.utc)
            
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
        """
        Get today's date in YYYY-MM-DD format.
        Useful for the AI to know the current date reference point.
        """
        return datetime.now(timezone.utc).date().isoformat()

    def create_event_simple(self, calendar_id: str, summary: str, 
                          start_hour: int, start_minute: int,
                          end_hour: int, end_minute: int,
                          days_from_today: int = 0,
                          description: str = None) -> dict:
        """
        Simplified event creation with conflict checking.
        
        Args:
            calendar_id: Calendar ID ('primary' for main calendar)
            summary: Event title
            start_hour: Start hour (24-hour format)
            start_minute: Start minute (0-59)
            end_hour: End hour (24-hour format)
            end_minute: End minute (0-59)
            days_from_today: Days from today (0=today, 1=tomorrow)
            description: Optional event description
            
        Returns:
            Created event details or conflict information
        """
        try:
            # Calculate start and end datetimes
            today = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            event_date = today + timedelta(days=days_from_today)
            
            start_dt = event_date.replace(hour=start_hour, minute=start_minute)
            end_dt = event_date.replace(hour=end_hour, minute=end_minute)
            
            # Handle overnight events
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            # Check for conflicts
            freebusy = self._get_service().freebusy().query(body={
                'timeMin': start_dt.isoformat(),
                'timeMax': end_dt.isoformat(),
                'items': [{'id': calendar_id}]
            }).execute()
            
            conflicts = freebusy['calendars'][calendar_id].get('busy', [])
            if conflicts:
                return {
                    'status': 'conflict',
                    'message': f'Time conflict with {len(conflicts)} existing events',
                    'proposed_event': {
                        'summary': summary,
                        'start': start_dt.isoformat(),
                        'end': end_dt.isoformat()
                    }
                }
            
            # Create the event if no conflicts
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC'
                }
            }
            
            return self._get_service().events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
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
            calendar_client.create_event_simple,
            name="calendar_create_event",
            description="Create event with conflict checking. Args: calendar_id, summary, start_hour (24h), start_minute, end_hour (24h), end_minute, days_from_today (0=today), description"
        )
    ]
