"""
Google Calendar operations tool for the personal assistant.
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional
import anyio
import functools
import logging
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

    def update_event(self, calendar_id: str, event_id: str, 
                   new_start_hour: int = None, new_start_minute: int = None,
                   new_end_hour: int = None, new_end_minute: int = None,
                   days_from_today: int = None, 
                   new_summary: str = None, new_description: str = None) -> dict:
        """
        Flexible event updater that handles partial updates.
        Only updates specified fields while preserving others.
        """
        try:
            # Get current event
            current_event = self._get_service().events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Parse current times
            current_start = datetime.fromisoformat(current_event['start']['dateTime'])
            current_end = datetime.fromisoformat(current_event['end']['dateTime'])
            duration = current_end - current_start
            
            # Calculate new times
            new_start = current_start
            new_end = current_end
            
            # Handle date change if specified
            if days_from_today is not None:
                today = datetime.now(self.local_tz).replace(hour=0, minute=0, second=0)
                new_date = today + timedelta(days=days_from_today)
                new_start = new_date.replace(hour=new_start.hour, minute=new_start.minute)
                new_end = new_date.replace(hour=new_end.hour, minute=new_end.minute)
            
            # Apply partial time updates
            if new_start_hour is not None or new_start_minute is not None:
                new_start = new_start.replace(
                    hour=new_start_hour if new_start_hour is not None else new_start.hour,
                    minute=new_start_minute if new_start_minute is not None else new_start.minute
                )
                # Preserve duration if only start time changed
                if new_end_hour is None and new_end_minute is None:
                    new_end = new_start + duration
            
            if new_end_hour is not None or new_end_minute is not None:
                new_end = new_end.replace(
                    hour=new_end_hour if new_end_hour is not None else new_end.hour,
                    minute=new_end_minute if new_end_minute is not None else new_end.minute
                )
            
            # Verify end time is after start time
            if new_end <= new_start:
                return {
                    'status': 'error',
                    'message': 'End time must be after start time',
                    'proposed_times': {
                        'start': new_start.strftime('%I:%M %p'),
                        'end': new_end.strftime('%I:%M %p')
                    }
                }
            
            # Prepare update with all fields (preserving existing ones)
            updated_event = {
                'summary': new_summary if new_summary is not None else current_event.get('summary', ''),
                'description': new_description if new_description is not None else current_event.get('description', ''),
                'location': current_event.get('location', '')
            }
            
            # Only include time fields if they changed
            if new_start != current_start or new_end != current_end:
                updated_event.update({
                    'start': {
                        'dateTime': new_start.astimezone(self.local_tz).isoformat(),
                        'timeZone': 'UTC'
                    },
                    'end': {
                        'dateTime': new_end.astimezone(self.local_tz).isoformat(),
                        'timeZone': 'UTC'
                    }
                })
            
            # Skip update if nothing changed
            if not updated_event:
                return {
                    'status': 'no_change',
                    'message': 'No updates were specified',
                    'current_event': current_event
                }
            
            # Perform update
            updated_event = self._get_service().events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=updated_event
            ).execute()
            
            return {
                'status': 'success',
                'message': 'Event updated successfully',
                'changes': {
                    'summary': 'updated' if new_summary else 'not modified',
                    'description': 'updated' if new_description else 'not modified',
                    'start': new_start.strftime('%I:%M %p') if new_start != current_start else 'not modified',
                    'end': new_end.strftime('%I:%M %p') if new_end != current_end else 'not modified',
                    'date': new_start.strftime('%A, %B %d') if days_from_today is not None else 'not modified'
                },
                'event': updated_event
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to update event: {str(e)}'
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
            description="Update an existing calendar event with simple time parameters. Args: calendar_id, event_id, new_start_hour=None, new_start_minute=None, new_end_hour=None, new_end_minute=None, days_from_today=None, new_summary=None, new_description=None"
        )
    ]
