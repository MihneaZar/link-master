## Description
Console application for keeping track of important links, in separate lists, containing entries that can have one or more links. <br>
The main page contains the list of Link Lists (e.g. one list could be with entries for different online dictionaries, another could be for frequently used websites.
A Link List page contains multiple entries. An entry has a description (e.g. 'Dictionaries'), a Yes/No value for opening in Google Incognito, and a list of links.

## Requirements
- The [ConsoleListInterface class](https://github.com/MihneaZar/ConsoleListInterface/).
- The [python-readchar](https://pypi.org/project/readchar/) library.

## Additional Information
For the program to run, 'json_data_clean' and 'keep_clean.py' need to be renamed to 'json_data' and 'keep.py'
The program opens the links in Google Chrome / Google Incognito. <br>
On first use, it will prompt user to give the path to the ConsoleInterfaceList.py file (containing the respective Class). <br>
Typing '?' while in the app will print the help page (for the Link Master Menu page, or the Link List page). <br>
Only tested on Windows 11.

## Google Keep
As an additional functionality, the program can save the Link Lists to Google Keep. <br>
For this, it requires a Google API Master Token. <br>
The explanation of how to acquire it is [here](https://github.com/rukins/gpsoauth-java/blob/b74ebca999d0f5bd38a2eafe3c0d50be552f6385/README.md#receiving-an-authentication-token). <br>
To make it work in the app, change the name of 'keep_clean.py' to 'keep.py' and paste the Master Token into the KEEP_TOKEN variable. <br>
!! Important Notes:
- as the name suggests, the Master Token grants access to your **entire Google account**. Therefore, protect it with your life, and never share it/publish it online;
- the program saves the links lists as separate Keep Notes under the label 'Link Master'. Do not add this label to any other notes, since the program deletes all previous notes labeled 'Link Master' before uploading the new Link Lists.<br>

Additionally, if KEEP_FILE in 'keep.py' is provided and is an existing file, the program will save the Google Keep cache there (can be useful as a cache shared between programs). 

## Example Entries
TODO
