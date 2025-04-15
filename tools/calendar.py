"""
Google Calendar operations tool for the personal assistant.
"""
import os
from datetime import datetime, timezone, time, timedelta
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
        # Tool(
        #     calendar_client.create_event,
        #     name="calendar_create_event",
        #     description="Create a new calendar event"
        # ),
        # Tool(
        #     calendar_client.update_event,
        #     name="calendar_update_event",
        #     description="Update an existing calendar event"
        # )
    ]
