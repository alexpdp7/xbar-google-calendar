from __future__ import print_function

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        from_ = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
        events_result = service.events().list(calendarId='primary', timeMin=from_.isoformat() + 'Z',
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        for i, event in enumerate(events):
            if event["start"].get("dateTime"):
                start = datetime.datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
                if start.date() == datetime.date.today():
                    start_str = start.strftime("%H:%M")
                else:
                    start_str = start.strftime("%Y-%m-%d %H:%M")
            else:
                start = datetime.datetime.strptime(event["start"]["date"], "%Y-%m-%d")
                if start.date() == datetime.date.today():
                    start_str = "Today"
                else:
                    start_str = start.strftime("%Y-%m-%d")

            google_meet_urls = [ep["uri"] for ep in event.get("conferenceData", {}).get("entryPoints", []) if ep["uri"].startswith("https://meet.google.com")]
            google_meet_url = google_meet_urls[0] if len(google_meet_urls) == 1 else None
            actions = f"| href={google_meet_url}" if google_meet_url else ""
            print(start_str, event['summary'], actions)
            if i == 0:
                print("---")
        print("Refresh | refresh=true")

    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    main()
