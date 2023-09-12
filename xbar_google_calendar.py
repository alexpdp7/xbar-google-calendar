"""
Based on https://developers.google.com/calendar/api/quickstart/python
"""

import datetime
import pathlib
import os
import re
import sys

import appdirs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


APPNAME = "xbar-google-calendar"
APPAUTHOR = "pdp7"


def event_to_order_and_item(event):
    google_meet_urls = [ep["uri"] for ep in event.get("conferenceData", {}).get("entryPoints", []) if ep["uri"].startswith("https://meet.google.com")]
    google_meet_url = google_meet_urls[0] if len(google_meet_urls) == 1 else None

    bluejeans_matches = re.search(r"https://primetime.bluejeans.com/a2m/live-event/\w{8,}", event.get("description", ""))
    bluejeans_url = bluejeans_matches.group() if bluejeans_matches else None

    url = google_meet_url or bluejeans_url

    my_response_status = [a["responseStatus"] for a in event.get("attendees", []) if a.get("self")]
    accepted = my_response_status == ["accepted"]

    if event["start"].get("dateTime"):
        has_time = True
        start = datetime.datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
        if start.date() == datetime.date.today():
            today = True
        else:
            today = False
    else:
        has_time = False
        start = datetime.datetime.strptime(event["start"]["date"], "%Y-%m-%d")
        if start.date() == datetime.date.today():
            today = True
        else:
            today = False

    time_str = (
        start.strftime("%H:%M") if today and has_time else
        start.strftime("%Y-%m-%d %H:%M") if not today and has_time else
        "Today" if today and not has_time else
        start.strftime("%Y-%m-%d")
    )

    order_number = (
        0 if today and accepted else
        1 if today and has_time else
        2 if today else
        3
    )

    order = (order_number, abs(start.astimezone() - datetime.datetime.now().astimezone()))

    actions = f"| href={url}" if url else ""
    return order, " ".join([time_str, event['summary'], actions])


def log(s):
    if not os.environ.get("ARGOS_VERSION"):
        print(s, file=sys.stderr)


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = pathlib.Path(appdirs.user_cache_dir(APPNAME, APPAUTHOR)) / "token.json"
    log(f"Trying to load token from {token_path}")
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        log(f"Not found or invalid: {creds}")
        if creds and creds.expired and creds.refresh_token:
            log("Refreshing creds")
            creds.refresh(Request())
        else:
            credentials_path = pathlib.Path(appdirs.user_config_dir(APPNAME, APPAUTHOR)) / "credentials.json"
            log(f"Getting token from {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
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

        order_and_items = [event_to_order_and_item(e) for e in events]
        sorted_order_and_items = sorted(order_and_items)

        print(sorted_order_and_items[0][1])
        print("---")

        for _order, item in sorted_order_and_items:
            print(item)
        print("Refresh | refresh=true")

    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    main()
