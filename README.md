# KCL-Timetable-To-ICS
 
## What does this do
1) Logs into King's College London timetable website with your credentials (must be provided)
2) Scrapes timetable for "Sem 1 reading week (11) revision (17)", "All Days", "08:00 - 22:00 (Day and Evening)"
3) Saves timetable information into an ICS file

#### External modules required:
* requests
* beautifulsoup4
* icalendar
* pytz

##### pip install requests beautifulsoup4 icalendar pytz

### Known Issues:
* Problem: Login failed even though credentials are correct.
* Cause: CTRL-V doesn't work for pasting password on Windows 10.
* Solution: You can right click to paste instead, which does work, or type manually.
