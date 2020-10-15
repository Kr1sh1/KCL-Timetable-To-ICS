#!/usr/bin/python3
import sys
assert sys.version_info >= (3, 6, 0), "Python version too low."

import requests
import os
import pickle
import hashlib

from bs4 import BeautifulSoup as bs
from icalendar import Event, Calendar
from datetime import datetime
from pytz import timezone
from getpass import getpass

#data class for each event
class Class_Event:
    def __init__(self, columns):
        self.day = columns[0]
        self.start = columns[1]
        self.end = columns[2]
        self.activity = columns[3]
        self.description = columns[4]
        self.type = columns[5]
        self.room = columns[6]
        self.staff = columns[7]
        self.activity_date = columns[8]

print("\n")
print("##########################################################")
print("# King's College London Timetable Extractor --> ICS File #")
print("##########################################################")
print("\n")

username = input("Enter your K number (including the K): ")
password = getpass("Password: ")

login_url = "https://timetables.kcl.ac.uk/KCLSWS/SDB2021RDB/Login.aspx"
url = "https://timetables.kcl.ac.uk/kclsws/SDB2021RDB/default.aspx"
timetable_url = "https://timetables.kcl.ac.uk/kclsws/SDB2021RDB/showtimetable.aspx"

def default_args(soup):
    view_state = soup.find("input", id="__VIEWSTATE")["value"]
    view_state_generator = soup.find("input", id="__VIEWSTATEGENERATOR")["value"]
    event_validation = soup.find("input", id="__EVENTVALIDATION")["value"]

    payload = {
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation,
        "__EVENTARGUMENT": ""
    }

    return payload

def login_args(soup):
    login_payload = default_args(soup)
    login_payload["tUserName"] = username
    login_payload["tPassword"] = password
    login_payload["bLogin"] = "Login"
    login_payload["__EVENTTARGET"] = ""
    login_payload["__LASTFOCUS"] = ""

    return login_payload

#Session auto manages stuff like cookies and connection
with requests.Session() as session:
    response = session.get(login_url)
    soup = bs(response.text, features="html.parser")

    response = session.post(login_url, login_args(soup))

    if "Your King's ID (eg:- k1234567) and password must not be blank" in response.text:
        print("Your King's ID (eg:- k1234567) and password must not be blank.")
        sys.exit(1)
    elif "Login failed. Check there is no space after the K number." in response.text:
        print("Login failed. Make sure there is no space after the K number.")
        sys.exit(2)

    soup = bs(response.text, features="html.parser")

    timetable_request_payload_1 = default_args(soup)
    timetable_request_payload_1["__EVENTTARGET"] = "LinkBtn_studentMyTimetable"
    timetable_request_payload_1["tLinkType"] = "information"

    response = session.post(url, timetable_request_payload_1)
    soup = bs(response.text, features="html.parser")

    timetable_request_payload_2 = default_args(soup)
    timetable_request_payload_2["__EVENTTARGET"] = ""
    timetable_request_payload_2["__LASTFOCUS"] = ""
    timetable_request_payload_2["tLinkType"] = "studentMyTimetable"
    timetable_request_payload_2["dlObject"] = username[1:]
    timetable_request_payload_2["lbWeeks"] = "6;7;8;9;10;11;12;13;14;15;16;17"
    timetable_request_payload_2["dlPeriod"] = "0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;23;24;25;26;27;28"
    timetable_request_payload_2["RadioType"] = "textspreadsheet;swsurl;SWSCUST+Student+TextSpreadsheet"
    timetable_request_payload_2["bGetTimeTable"] = "View Timetable"

    response = session.post(url, timetable_request_payload_2)
    response = session.post(timetable_url)

soup = bs(response.text, features="html.parser")
tables = soup.find_all("table", border=1)

#all events are stored here
classes = []

for day_events in tables:
    #day_events.tr is None when there are no events in a day
    if day_events.tr is None:
        continue
    
    #decompose gets rid of the row with the column identifiers
    day_events.tr.decompose()
    events = day_events.find_all("tr")

    for event in events:
        columns = event.find_all("td")
        classes.append(Class_Event([column.text for column in columns]))

action = "created"

#If the ICS file exists already, check if the timetable has changed or not.
if os.path.isfile("KCL-Timetable.ics"):
    with open("KCL-Timetable.ics", "rb") as file_:
        calendar = Calendar.from_ical(file_.read())
        try:
            uid = calendar["uid"]
        except KeyError:
            print("Old ICS file format detected. Changes in your timetable will be detected in future runs.")
        else:
            hash_digest = hashlib.sha256(pickle.dumps(classes)).digest()
            int_digest = int.from_bytes(hash_digest, byteorder="big")

            if int_digest == int(uid):
                print("Your timetable hasn't changed.")
                sys.exit(0)

            action = "updated"

#Creating ics file format
calendar = Calendar()

hash_digest = hashlib.sha256(pickle.dumps(classes)).digest()
int_digest = int.from_bytes(hash_digest, byteorder="big")
calendar["uid"] = int_digest

for event in classes:
    dates = event.activity_date.split(";")

    for date in dates:
        lon_dt = timezone("Europe/London")

        start = lon_dt.localize(datetime.strptime(date + " " + event.start, "%d/%m/%y %H:%M"))
        end = lon_dt.localize(datetime.strptime(date + " " + event.end, "%d/%m/%y %H:%M"))

        if len(event.room) != 1:
            location = f"{event.type} | {event.room}"
        else:
            location = event.type

        e = Event()
        e.add("summary", event.activity)
        e.add("description", event.description)
        e.add("location", location)
        e.add("dtstart", start)
        e.add("dtend", end)
        e.add("dtstamp", lon_dt.localize(datetime.now()))

        calendar.add_component(e)

with open("KCL-Timetable.ics", "wb") as timetable:
    timetable.write(calendar.to_ical())

print(f"\n\"KCL-Timetable.ics\" file {action} at {os.getcwd()}")
