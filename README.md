## Description
Console application for keeping track of important links, in separate lists, containing entries that can have one or more links. <br>
The main page contains the list of Link Lists (e.g. one list could be with entries for different online dictionaries, another could be for frequently used websites). <br>
A Link List page contains multiple entries. An entry has a description (e.g. 'Dictionaries'), a Yes/No value for opening in Google Incognito, and a list of links.

## Requirements
- The [ConsoleListInterface class](https://github.com/MihneaZar/ConsoleListInterface/).
- The [python-readchar](https://pypi.org/project/readchar/) library.

## Additional Information
The program opens the links in Google Chrome / Google Incognito. <br>
On first use, it will prompt user to give the path to the ConsoleInterfaceList.py file (containing the respective Class). <br>
Typing '?' while in the app will print the help page (for the Link Master Menu page, or the Link List page). <br>
Only tested on Windows 11.

## Google Keep
As an additional functionality, the program can save the Link Lists to Google Keep. <br>
For this, it requires a Google API Master Token. <br>
The explanation of how to acquire it is [here](https://github.com/rukins/gpsoauth-java/blob/b74ebca999d0f5bd38a2eafe3c0d50be552f6385/README.md#receiving-an-authentication-token). <br>
For this to work, paste the Master Token into the KEEP_TOKEN variable in the 'keep.py' file. <br>
!! Important Notes:
- as the name suggests, the Master Token grants access to your **entire Google account**. Therefore, protect it with your life, and never share it/publish it online;
- the program saves the link lists as separate Keep Notes under the label 'Link Master'. Do not add this label to any other notes, since the program deletes all previous notes labeled 'Link Master' before uploading the new Link Lists.<br>

Additionally, if KEEP_FILE in 'keep.py' is provided and is an existing file, the program will save the Google Keep cache there (can be useful as a cache shared between programs). 

## Example Entries
By default, the 'json_data' folder contains an 'Examples.json' file with the following examples for link formatting: <br>
1. The first one has links to three dictionaries: [Thesaurus](https://www.thesaurus.com/browse/), [Merriam-Webster](https://www.merriam-webster.com/thesaurus/) and [Wordhippo](https://www.wordhippo.com/what-is/another-word-for/). Pressing 'enter' on this entry simply opens all three links.
2. The second example is for a link to [Thesaurus](https://www.thesaurus.com/browse/) with an input-able word to search for: 'https://www.thesaurus.com/browse/\{Word to search for\\}'.<br>
The '\\{Word to search for\\}' section will prompt the text 'Word to search for: ' on every link open, and will concatanate the response to the end of 'https://www.thesaurus.com/browse/'. Therefore, the user can search for words on [Thesaurus](https://www.thesaurus.com/browse/) directly from the program.
3. The third example is similar to the second, but it uses a variable: 'var search_str = \\{Word to search for\\}'. That way, all appearances of \\{search_str\\} in links will be changed with the response to the 'Word to search for: ' prompt. <br>
The order does not matter, since the variables are first resolved, then the links are opened.
<br>

Additional Notes:
- entering '?' when inputting links will provide instructions for the formatting of input-able links, and useful commands for removing existing links when editting;
- the slightly confusing '\\{input_prompt\\}' format is used so it does not interfere with valid characters in links (including, potentially, '{}').
