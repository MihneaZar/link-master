## Description
Console application for keeping track of important links, in separate lists, containing entries that can have one or more links. <br>
The main page contains the list of Link Lists (e.g. one list could be with entries for different online dictionaries, another could be for frequently used websites). <br>
A Link List page contains multiple entries. An entry has a description (e.g. 'Dictionaries'), a Yes/No value for opening in Google Incognito, and a list of links.

## Requirements
- The [ConsoleListInterface](https://github.com/MihneaZar/ConsoleListInterface/) class for the console interface;
- The [python-readchar](https://pypi.org/project/readchar/) library for reading keystrokes;
- The [cursor](https://pypi.org/project/cursor/) library for hiding the cursor in console;
- The [Requests](https://pypi.org/project/requests/) library for downloading website reponses directly;
- The [Send2Trash](https://pypi.org/project/Send2Trash/) library for sending files to trash/recycle bin;
- (Optional) The [gpsoauth](https://github.com/simon-weber/gpsoauth) library for obtaining the Google Master Token, needed for uploading to Google Keep;
- (Optional) The [gkeepapi](https://github.com/kiwiz/gkeepapi) library for actually uploading notes to Google Keep.

## Setup
The setup() function from [setup.py](setup.py) will be run automatically on the first 'link_master.py' launch.
On top of creating the 'json_data' folder (where the app data is stored), it will prompt the user for three things:
- (required) path to the folder where 'ConsoleListInterface.py' is located;
- (optional) Gmail Address;
- (optional) Google Master Token;
- (optional) Google Keep Cache filepath.

The last three are for the functionality of saving to Google Keep, and are explained in the 'Google Keep' section. <br>
The setup function can be rerun with 'python3 setup.py' to change any of the three fields.

## Additional Information
The program opens the links in Google Chrome / Google Incognito. <br>
Typing '?' while in the app will print the help pages (for the Link Master Menu, or the Link List page). <br>
Only tested on Windows 11.

## Google Keep
As an additional functionality, the program can save the Link Lists to Google Keep. <br>
For this, it requires a Google Master Token. <br>
The setup function requires a Google Access Token to obtain the Google Master Token. <br>
The explanation of how to acquire a Google Access Token is [here](https://github.com/rukins/gpsoauth-java/blob/b74ebca999d0f5bd38a2eafe3c0d50be552f6385/README.md#receiving-an-authentication-token). <br>
!! Important Notes:
- as the name suggests, the Master Token grants access to your **entire Google account**. Therefore, protect it with your life, and never share it or publish it online;
- the app saves the Master Token in a file named '.paths' in the same folder as [link_list.py](link_list.py). The Master Token is required for Google Keep uploads, but this feature is completely optional;
- the program saves the link lists as separate Keep Notes under the label 'Link Master'. Do not add this label to any other notes, since the program deletes all previous notes labeled 'Link Master' before uploading the new Link Lists. <br>

Additionally, if the path of an existing file is provided in the 'Google Keep Cache File' part of the setup, the program will save the Google Keep cache there (can be useful for a cache shared between programs). Otherwise, it will save it in the program folder as  'keep_state.json'.

## Example Entries
By default, the 'json_data' folder contains an 'Examples.json' file with a few the following examples for link formatting (ctrl+d shows the details of link entries): <br>
1. The first one has links to three dictionaries: [Thesaurus](https://www.thesaurus.com/browse/), [Merriam-Webster](https://www.merriam-webster.com/thesaurus/) and [Wordhippo](https://www.wordhippo.com/what-is/another-word-for/). Pressing 'enter' on this entry simply opens all three links.
2. The second example is for a link to [Thesaurus](https://www.thesaurus.com/browse/) with an input-able word to search for: <br>
[https://www.thesaurus.com/browse/**\\{Word to search for\\**}]().<br>
The '\\{Word to search for\\}' section will prompt the text 'Word to search for: ' on every link open, and will concatanate the response to the end of [https://www.thesaurus.com/browse/](). Therefore, the user can search for words on [Thesaurus](https://www.thesaurus.com/browse/) directly from the program. <br>
The '\\{input_prompt\\}' section can be inserted into any part of the link, including the domain name.
4. The third example is similar to the second, but it uses a variable: 'var search_str = \\{Word to search for\\}'. That way, all appearances of '\\{search_str\\}' in links will be changed to the response to the 'Word to search for: ' prompt. <br>
The order does not matter, since the variables are first resolved, then the links are opened.
<br>

Additional Notes:
- entering '?' when inputting links will provide instructions for the formatting of input-able links, and useful commands for removing existing links whilst editting;
- the slightly confusing '\\{input_prompt\\}' format is used so it does not interfere with valid characters in links (including, potentially, '{' and '}').

-------------------------------------------------------------------------

*Copyright (c) 2026 Mihnea Bogdan Zarojanu*
