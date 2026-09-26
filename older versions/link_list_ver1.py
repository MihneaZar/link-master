from validator_collection import checkers
from send2trash import send2trash
from readchar import readkey, key
from math import ceil as roundup
from functools import reduce
from blessed import Terminal
import subprocess
import cursor
import json
import sys
import os


home_folder = "C:/Users/Mihnea/Desktop/Random thoughts/Cool stuff/Link List/"
json_folder = f'{home_folder}json_data/'

sys.stderr = open(f'{home_folder}errors.txt', "a")

TERM_WIDTH       = os.get_terminal_size()[0] # 120 characters per terminal line
ITEMS_PER_COLUMN = os.get_terminal_size()[1] - 2
INFO_POS         = ITEMS_PER_COLUMN / 2 - 4

SPACE_BEFORE    = 4   # ( -> ) / (    )
MAX_NAME_WIDTH  = 36  # (max allocated space for names)

MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))

NEXT_DIR = '\\'
cls = lambda: os.system('cls' if os.name=='nt' else 'clear')

FILENAME     = "Filename"
DATA         = "Data"
DESCRIPTIONS = "Description List"
DESC         = "Description"
INCOGNITO    = "Incognito"
LINKS        = "Links"


def move_cursor(y, x):
    sys.stdout.write("\033[%d;%dH" % (y, x))


def print_list(names):
    global TERM_WIDTH
    global ITEMS_PER_COLUMN
    global INFO_POS
    global MAX_COLUMNS

    TERM_WIDTH       = os.get_terminal_size()[0] # 120 characters per terminal line
    ITEMS_PER_COLUMN = os.get_terminal_size()[1] - 2
    INFO_POS         = ITEMS_PER_COLUMN / 2 - 4
    MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))

    cls()
    column = 1
    line   = 1

    for name in names:
        # move_cursor(counter % ITEMS_PER_COLUMN + 1, int(counter / ITEMS_PER_COLUMN) * (2 + SPACE_BEFORE + MAX_NAME_WIDTH))
        if MAX_COLUMNS < column:
            break
       
        move_cursor(line, (column - 1) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))

        if MAX_NAME_WIDTH < len(name):
            if '.' in name:
                extension = name[name.rfind('.'):]
            else: 
                extension = ""
            name = name[0:max(MAX_NAME_WIDTH - 1 - len(extension), 0)] + '-' + extension 

        print(f'    {name}')
        
        line += 1
        if line > ITEMS_PER_COLUMN:
            line    = 1
            column += 1
    
    move_cursor(ITEMS_PER_COLUMN + 2, 0)
    print("Type '?' for help page.", end='')


def yes_or_no(question, default_answer="yes", other_options=[], newline=True):
    options = ["yes", "no"] + list(map(lambda opt: opt.lower(), other_options))
    list_other_options = list(filter(lambda opt: opt != "", other_options))
    list_other_options = '/' + reduce(lambda o1, o2: o1+'/'+o2, list_other_options) if list_other_options else ""
    if newline:
        print(f'{question}\nY/N{list_other_options}', flush=True)
    else: 
        print(f'{question} (Y/N{list_other_options}): ', end='', flush=True)

    answer = readkey().lower()
    while not any(option.startswith(answer) for option in options):
        if answer == key.ENTER:
            if "" in options:
                print()
                return ""
            else:
                print(default_answer.capitalize())
                return default_answer
        
        answer = readkey().lower()

    for option in options:
        if option.startswith(answer):
            print(option.capitalize())
            if newline:
                print()
            return option

    return None


def get_columns(descriptions):
    total_columns     = roundup(len(descriptions) / ITEMS_PER_COLUMN)
    lines_last_column = len(descriptions) % ITEMS_PER_COLUMN

    if lines_last_column == 0:
        lines_last_column = ITEMS_PER_COLUMN
                        
    if not descriptions:
        total_columns = 1
        lines_last_column = 1

    return total_columns, lines_last_column


LINK_COMMANDS_LIST = [key.UP, key.DOWN, key.LEFT, key.RIGHT, key.CTRL_F, '\\', key.ENTER, key.CTRL_N, key.CTRL_R, 
                      key.CTRL_X, key.CTRL_C, key.DELETE, key.CTRL_B, key.CTRL_G, key.CTRL_U, '?', '=', '-', key.ESC]
LINK_HELP_PAGE    = """
Link list page.

Controls:
    - arrow keys -> moving between existing entries in list.
    - character  -> moves cursor to the next entry that starts with character, if it exists.
    - ctrl+f     -> searches for the next entry that contains string, if it exists (not case sensitive).
    - '\\'        -> finds next entry that contains last searched string.
    - enter      -> opens entry links, in the selected mode (normal or incognito).
    - ctrl+n     -> creates new entry.
    - ctrl+d     -> see details of selected entry.
    - ctrl+r     -> replaces info for selected entry.
    - ctrl+x     -> move selected entry into another link list.
    - ctrl+c     -> copy selected entry into a chosen link list (including the same one).
    - delete     -> removes entry (warning: data is lost forever).
    - ctrl+g     -> upload all new changes (in this list and all others) to Google Drive.
    - ctrl+u     -> update printed list (for terminal size change).
    - '='/'-'    -> increases/decreases number of characters in entry names before they are cut off.
    - '?'        -> displays current help page.
    - escape     -> quits application.
""" 

def link_list_loop(json_file_path):
    if not json_file_path:
        return
    
    os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]} - Link Master')

    json_data = json.load(open(json_file_path))
    descriptions = json_data[DESCRIPTIONS]

    total_columns, lines_last_column = get_columns(descriptions)

    column = 1
    line   = 1

    leftwise_column = 1
                
    print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

    # saving it outside the while, for repeated searches
    search_str = '\\'
    
    global MAX_NAME_WIDTH
    global MAX_COLUMNS

    while (True):
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))
        print(" -> ")
        # print(column, end='')
        # print(line)
        # print((column - 1) * ITEMS_PER_COLUMN + line - 1)
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))

        try:
            command = readkey()
        
        except KeyboardInterrupt:
            command = key.CTRL_C

        # arrowkeys for moving between entries
        if command == key.UP:
            print("   ")

            line -= 1
            if line < 1:
                line = ITEMS_PER_COLUMN

        if command == key.DOWN:
            print("   ")

            line += 1
            if ITEMS_PER_COLUMN < line or (column == total_columns and lines_last_column < line):
                line = 1
            
        if command == key.LEFT:
            print("   ")

            column -= 1

            if column < leftwise_column and 1 <= column:
                leftwise_column -= 1
                print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

            if column < 1:
                column = total_columns
                if MAX_COLUMNS < total_columns:
                    leftwise_column = total_columns - MAX_COLUMNS + 1
                    print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
            
        if command == key.RIGHT:
            print("   ")

            column += 1

            if total_columns < column:
                column = 1
                if 1 < leftwise_column:
                    leftwise_column = 1
                    print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

            if MAX_COLUMNS <= (column - leftwise_column):
                leftwise_column += 1
                print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # searching by first character in filename
        if command not in LINK_COMMANDS_LIST:
            first_letter = command.lower()
            current_position = (column - 1) * ITEMS_PER_COLUMN + line - 1
            new_position = next((i for i in range(len(descriptions)) if descriptions[i][0].lower() == first_letter and i > current_position), 
                            next((i for i in range(len(descriptions)) if descriptions[i][0].lower() == first_letter), current_position))


            if new_position != current_position:
                print("   ")

                column = int((new_position) / ITEMS_PER_COLUMN) + 1
                line   = (new_position) % ITEMS_PER_COLUMN + 1

                if column < leftwise_column:
                    leftwise_column = column
                    print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

                if MAX_COLUMNS <= (column - leftwise_column):
                    leftwise_column = column
                    print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # searching by string in filename
        if command in [key.CTRL_F, '\\']:
            reprint = False
            if command == key.CTRL_F:
                cls()
                move_cursor(INFO_POS, 0)
                cursor.show()
                search_str = input("String to search by:\n").lower()
                cursor.hide()
                cls()
                reprint = True

            if search_str and not search_str.isspace():
                current_position = (column - 1) * ITEMS_PER_COLUMN + line - 1
                new_position = next((i for i in range(len(descriptions)) if search_str in descriptions[i].lower() and i > current_position), 
                                next((i for i in range(len(descriptions)) if search_str in descriptions[i].lower()), current_position))

                if new_position != current_position:
                    print("   ")

                    column = int((new_position) / ITEMS_PER_COLUMN) + 1
                    line   = (new_position) % ITEMS_PER_COLUMN + 1

                    if column < leftwise_column:
                        leftwise_column = column
                        reprint = True

                    if MAX_COLUMNS <= (column - leftwise_column):
                        leftwise_column = column
                        reprint = True
                
            else:
                reprint = True
                
            if reprint:
                print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
                

        # went left to the last column from lower 
        if column == total_columns and lines_last_column < line:
            line = lines_last_column


        # open links from selected list
        if command == key.ENTER:
            curr_pos = (column - 1) * ITEMS_PER_COLUMN + line - 1
            entry    = json_data[DATA][curr_pos]
            answer   = entry[INCOGNITO].lower()

            chrome_arg = "" if answer == "no" else "-incognito"
            
            for link in entry[LINKS]:
                subprocess.Popen(f'start chrome {chrome_arg} /new-tab \"{link}\"',shell = True)
                # sleep(0.1)


        # creating new entry
        if command == key.CTRL_N:
            cls()
            move_cursor(INFO_POS, 0)
            cursor.show()
            print("Add new entry:")

            description = input("Description: ")
            while not description or description.isspace():
                move_cursor(INFO_POS + 1, 0)
                description = input("Description: ")

            incognito = yes_or_no("Open in incognito mode", default_answer="no", newline=False).capitalize()

            links = []
            print("Links: ")

            curr_link = input()
            while (not (curr_link == "" or curr_link.isspace())):
                https_link = curr_link[curr_link.find('h'):]
                if checkers.is_url(https_link):
                    links.append(https_link)
                else:
                    print(f"\'{curr_link}\' is not a valid URL, so it was ignored.")
                curr_link = input()
            
            cursor.hide()
                
            json_data[DATA].append({DESC: description, INCOGNITO: incognito, LINKS: links})
            json_data[DESCRIPTIONS].append(description)

            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)

            total_columns     = roundup(len(descriptions) / ITEMS_PER_COLUMN)
            lines_last_column = len(descriptions) % ITEMS_PER_COLUMN
            
            new_position = descriptions.index(description)
            column = int((new_position) / ITEMS_PER_COLUMN) + 1
            line   = (new_position) % ITEMS_PER_COLUMN + 1
            leftwise_column = 1 if column <= MAX_COLUMNS else (column - MAX_COLUMNS + 1)

            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
            
        # showing details of selected entry
        if command == key.CTRL_D:
            cls()
            entry = json_data[DATA][(column - 1) * ITEMS_PER_COLUMN + line - 1]
            link_list = reduce(lambda l1, l2: l1 + "\n" + l2, entry[LINKS]) if entry[LINKS] else ""
            move_cursor(max(INFO_POS - len(entry[LINKS]) + 1, 0), 0)
            print(f'Description: {entry[DESC]}')
            print(f'Open in incognito mode: {entry[INCOGNITO]}')
            print(f'Links:\n{link_list}\n')

            input("Press enter to continue.")

            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # replacing info in selected entry
        if command == key.CTRL_R:
            cls()
            move_cursor(0, 0)
            cursor.show()

            entry_position = (column - 1) * ITEMS_PER_COLUMN + line - 1
            link_list = reduce(lambda l1, l2: l1 + "\n" + l2, json_data[DATA][entry_position][LINKS]) if json_data[DATA][entry_position][LINKS] else ""

            print("\nCurrent fields:\n")
            print(f'Description: {json_data[DATA][entry_position][DESC]}')
            print(f'Open in incognito mode: {json_data[DATA][entry_position][INCOGNITO]}')
            print(f'Links:\n{link_list}\n\n')

            print("Input new information or leave empty to keep it the same.")
            print("Warning: Overwritten data will be lost.\n\n")

            print("New fields:\n")
            description = input("Description: ")    
            incognito = yes_or_no("Open in incognito mode", other_options=[""], newline=False).capitalize()

            links = []
            print("Links: ")

            curr_link = input()
            while (not (curr_link == "" or curr_link.isspace())):
                https_link = curr_link[curr_link.find('h'):]
                if checkers.is_url(https_link):
                    links.append(https_link)
                else:
                    print(f"\'{curr_link}\' is not a valid URL, so it was ignored.")
                curr_link = input()
                
            if description != "":
                json_data[DESCRIPTIONS][entry_position] = description
                json_data[DATA][entry_position][DESC] = description
                
            if incognito != "":
                json_data[DATA][entry_position][INCOGNITO] = incognito
                
            if links:
                json_data[DATA][entry_position][LINKS] = links

            # at least one field was changed, updating file
            if description != "" or incognito != "" or links:
                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)
            
            cursor.hide()

            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # moves selected entry to another link list:
        if command == key.CTRL_X:
            entry = json_data[DATA][(column - 1) * ITEMS_PER_COLUMN + line - 1]

            os.system(f'title Copying \'{entry[DESC]}\'')
            move_file_path, _ = json_file_loop()
            if not move_file_path or json_file_path == move_file_path:
                os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]}')
                print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
                continue

            # adding entry to other json file
            move_data = json.load(open(move_file_path))

            move_data[DATA].append(entry)
            move_data[DESCRIPTIONS].append(entry[DESC])

            with open(move_file_path, 'w', encoding='utf-8') as file:
                json.dump(move_data, file, ensure_ascii=False, indent=4)

            # removing entry from current json file
            curr_pos = (column - 1) * ITEMS_PER_COLUMN + line - 1
            json_data[DATA].pop(curr_pos)
            json_data[DESCRIPTIONS].pop(curr_pos)

            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)

            total_columns, lines_last_column = get_columns(descriptions)

            current_position  = (column - 1) * ITEMS_PER_COLUMN + line - 1
            current_position -= 1
                
            column = int((current_position) / ITEMS_PER_COLUMN) + 1
            line   = (current_position) % ITEMS_PER_COLUMN + 1
            if column < leftwise_column:
                leftwise_column = column

            os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]}')

            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # copies selected entry to link list
        if command == key.CTRL_C:
            entry = json_data[DATA][(column - 1) * ITEMS_PER_COLUMN + line - 1]

            os.system(f'title Copying \'{entry[DESC]}\'')
            copy_file_path, _ = json_file_loop()
            if not copy_file_path:
                os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]}')
                print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
                continue

            if json_file_path == copy_file_path:
                # adding entry to the same json file
                json_data[DATA].append(entry)
                json_data[DESCRIPTIONS].append(entry[DESC])

                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)

                total_columns     = roundup(len(descriptions) / ITEMS_PER_COLUMN)
                lines_last_column = len(descriptions) % ITEMS_PER_COLUMN
                
                os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]}')
                print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
                continue

            # adding entry to other json file
            copy_data = json.load(open(copy_file_path))

            copy_data[DATA].append(entry)
            copy_data[DESCRIPTIONS].append(entry[DESC])

            with open(copy_file_path, 'w', encoding='utf-8') as file:
                json.dump(copy_data, file, ensure_ascii=False, indent=4)

            os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]}')
            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # remove entry from link list
        if command == key.DELETE:
            curr_pos = (column - 1) * ITEMS_PER_COLUMN + line - 1

            cls()
            move_cursor(INFO_POS, 0)
            if yes_or_no(f'Are you sure you want to remove \'{descriptions[curr_pos]}\'?\nData will be lost forever.') == "no":
                print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
                continue

            json_data[DATA].pop(curr_pos)
            json_data[DESCRIPTIONS].pop(curr_pos)

            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)

            total_columns, lines_last_column = get_columns(descriptions)

            current_position  = (column - 1) * ITEMS_PER_COLUMN + line - 1
            current_position -= 1

            if current_position == -1:
                current_position = 0
                
            column = int(current_position / ITEMS_PER_COLUMN) + 1
            line   = max(current_position % ITEMS_PER_COLUMN + 1, 1)

            if column < leftwise_column:
                leftwise_column = column
                
            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # making filenames longer
        if command == "=" and 1 < MAX_COLUMNS:
            # changing the width of filenames to maximum possible if we have one less column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS - 1)) - SPACE_BEFORE
            # MAX_NAME_WIDTH += 1 # increasing size of filenames
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
            if (column - leftwise_column) >= MAX_COLUMNS:
                column -= 1

        # making filenames shorter
        if command == "-" and 8 < MAX_NAME_WIDTH:
            # changing the width of filenames to leave space for an additional column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS + 1)) - SPACE_BEFORE
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # update for resize
        if command == key.CTRL_U:
            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # help page
        if command == '?':
            cls()
            move_cursor(0, 0)
            print(LINK_HELP_PAGE)
            input("Press enter to continue.\n")
            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # uploading to drive
        if command == key.CTRL_G:
            cls()
            move_cursor(INFO_POS, 0)
            print("\nUploading to drive...")

            from googleapiclient.http import MediaFileUpload
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            import zipfile

            with zipfile.ZipFile(f'{json_folder}/link_list.zip', mode="w") as archive:
                for file in os.listdir(json_folder):
                    if file != "link_list.zip":
                        archive.write(f'{json_folder}/{file}', arcname=file)
            
            scope = ['https://www.googleapis.com/auth/drive']
            service_account_json_key = f'{home_folder}credentials.json'
            credentials = service_account.Credentials.from_service_account_file(filename=service_account_json_key,scopes=scope)
            service = build('drive', 'v3', credentials=credentials)
                
            media = MediaFileUpload(f'{json_folder}link_list.zip')

            service.files().update(fileId='1CzyOhyemL-Mj3ZhW8WZXg9FWVNXHCaSq', media_body=media).execute()
            print("Upload complete.\n")
                
            print_list(descriptions[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # return to file selection
        if command == key.BACKSPACE:
            break


        # quit application
        if command == key.ESC:
            cls()
            move_cursor(0, 0)
            cursor.show()
            quit()


FILE_COMMANDS_LIST = [key.UP, key.DOWN, key.LEFT, key.RIGHT, key.CTRL_F, '\\', key.ENTER, key.CTRL_N, 
                      key.CTRL_R, key.DELETE, key.CTRL_B, key.CTRL_U, '?', '=', '-', key.ESC]
FILE_HELP_PAGE    = """
Link list main menu.

Controls:
    - arrow keys -> moving between existing link lists.
    - character  -> moves cursor to the next link list that starts with character, if it exists.
    - ctrl+f     -> searches for the next link list that contains string, if it exists (not case sensitive).
    - '\\'        -> finds next link list that contains last searched string.
    - enter      -> opens selected link list / moves or copies entry to selected link list.
    - ctrl+n     -> creates new link list.
    - ctrl+r     -> renames selected link list.
    - delete     -> move link list to recycle bin.
    - ctrl+b     -> open recycle bin in Windows File Explorer (to restore link lists).
    - ctrl+u     -> update available link lists (if one or more have been restored from bin).
    - '='/'-'    -> increases/decreases number of characters in link list names before they are cut off.
    - '?'        -> displays current help page.
    - backspace  -> if currently moving or copying entry, cancels action
    - escape     -> quits application.
""" 


# returns json file list
def get_files():
    files = [file[:file.find('.')] for file in os.listdir(json_folder) if 'zip' not in file]
        
    total_columns     = roundup(len(files) / ITEMS_PER_COLUMN)
    lines_last_column = len(files) % ITEMS_PER_COLUMN

    if lines_last_column == 0:
        lines_last_column = ITEMS_PER_COLUMN
                        
    if not files:
        total_columns = 1
        lines_last_column = 1

    return files, total_columns, lines_last_column


# returns selected json file
def json_file_loop(saved_pos=0):
    files, total_columns, lines_last_column = get_files()

    column = int((saved_pos) / ITEMS_PER_COLUMN) + 1
    line   = (saved_pos) % ITEMS_PER_COLUMN + 1

    leftwise_column = column

    print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

    # saving it outside the while, for repeated searches
    search_str = '\\'
    
    global MAX_NAME_WIDTH
    global MAX_COLUMNS

    while (True):
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))
        print(" -> ")
        # print(column, end='')
        # print(line)
        # print((column - 1) * ITEMS_PER_COLUMN + line - 1)
        move_cursor(line, (column - leftwise_column) * (SPACE_BEFORE + MAX_NAME_WIDTH) + (column != 1))

        try:
            command = readkey()
            
        except KeyboardInterrupt:
            command = key.CTRL_C

        # arrowkeys for moving between link lists
        if command == key.UP:
            print("   ")

            line -= 1
            if line < 1:
                line = ITEMS_PER_COLUMN

        if command == key.DOWN:
            print("   ")

            line += 1
            if ITEMS_PER_COLUMN < line or (column == total_columns and lines_last_column < line):
                line = 1
            
        if command == key.LEFT:
            print("   ")

            column -= 1

            if column < leftwise_column and 1 <= column:
                leftwise_column -= 1
                print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

            if column < 1:
                column = total_columns
                if MAX_COLUMNS < total_columns:
                    leftwise_column = total_columns - MAX_COLUMNS + 1
                    print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
            
        if command == key.RIGHT:
            print("   ")

            column += 1

            if total_columns < column:
                column = 1
                if 1 < leftwise_column:
                    leftwise_column = 1
                    print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

            if MAX_COLUMNS <= (column - leftwise_column):
                leftwise_column += 1
                print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # searching by first character in filename
        if command not in FILE_COMMANDS_LIST:
            first_letter = command.lower()
            current_position = (column - 1) * ITEMS_PER_COLUMN + line - 1
            new_position = next((i for i in range(len(files)) if files[i][0].lower() == first_letter and i > current_position), 
                            next((i for i in range(len(files)) if files[i][0].lower() == first_letter), current_position))


            if new_position != current_position:
                print("   ")

                column = int((new_position) / ITEMS_PER_COLUMN) + 1
                line   = (new_position) % ITEMS_PER_COLUMN + 1

                if column < leftwise_column:
                    leftwise_column = column
                    print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

                if MAX_COLUMNS <= (column - leftwise_column):
                    leftwise_column = column
                    print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # searching by string in filename
        if command in [key.CTRL_F, '\\']:
            reprint = False
            if command == key.CTRL_F:
                cls()
                move_cursor(INFO_POS, 0)
                cursor.show()
                search_str = input("String to search by:\n").lower()
                cursor.hide()
                cls()
                reprint = True

            if search_str and not search_str.isspace():
                current_position = (column - 1) * ITEMS_PER_COLUMN + line - 1
                new_position = next((i for i in range(len(files)) if search_str in files[i].lower() and i > current_position), 
                                next((i for i in range(len(files)) if search_str in files[i].lower()), current_position))

                if new_position != current_position:
                    print("   ")

                    column = int((new_position) / ITEMS_PER_COLUMN) + 1
                    line   = (new_position) % ITEMS_PER_COLUMN + 1

                    if column < leftwise_column:
                        leftwise_column = column
                        reprint = True

                    if MAX_COLUMNS <= (column - leftwise_column):
                        leftwise_column = column
                        reprint = True
                
            else:
                reprint = True
                
            if reprint:
                print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # went left to the last column from lower 
        if column == total_columns and lines_last_column < line:
            line = lines_last_column


        # open selected link list
        if command == key.ENTER:
            curr_pos = (column - 1) * ITEMS_PER_COLUMN + line - 1
            return f'{json_folder}{files[curr_pos]}.json', curr_pos


        # creating new link list
        if command == key.CTRL_N:
            cls()
            move_cursor(INFO_POS, 0)
            cursor.show()
            filename = input("Type name for new link list:\n")
            filename = filename[:filename.find('.')] if '.' in filename else filename
            cursor.hide()
            if filename and not filename.isspace():
                try:
                    # ignoring command if file already exists
                    if os.path.exists(f'{json_folder}{filename}.json'):
                        print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
                        continue

                    with open(f'{json_folder}{filename}.json', 'w', encoding='utf-8') as file:
                        json.dump({FILENAME: filename, DESCRIPTIONS: [], DATA: []}, file, ensure_ascii=False, indent=4)
                    
                    files, total_columns, lines_last_column = get_files()

                    new_position = files.index(filename)
                    
                    column = int((new_position) / ITEMS_PER_COLUMN) + 1
                    line   = (new_position) % ITEMS_PER_COLUMN + 1
                    
                    leftwise_column = 1 if column <= MAX_COLUMNS else (column - MAX_COLUMNS + 1)

                except Exception as e:
                    e = str(e)
                    input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')
            
            print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # rename link list
        if command == key.CTRL_R:
            cls()
            file = files[(column - 1) * ITEMS_PER_COLUMN + line - 1]
            move_cursor(INFO_POS, 0)
            cursor.show()
            filename = input(f'Rename {file} to:\n')
            filename = filename[:filename.find('.')] if '.' in filename else filename
            cursor.hide()

            if filename and not filename.isspace():
                try:
                    os.rename(f'{json_folder}{file}.json', f'{json_folder}{filename}.json')

                    files, total_columns, lines_last_column = get_files()
                    
                    new_position = files.index(filename)
                    column = int((new_position) / ITEMS_PER_COLUMN) + 1
                    line   = (new_position) % ITEMS_PER_COLUMN + 1
                    
                    leftwise_column = 1 if column <= MAX_COLUMNS else (column - MAX_COLUMNS + 1)
                
                except Exception as e:
                    e = str(e)
                    input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')
            
            print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # move link list to recycle bin
        if command == key.DELETE:
            try:
                file = files[(column - 1) * ITEMS_PER_COLUMN + line - 1]
                send2trash(f'{json_folder}{file}.json'.replace('/', '\\')) # this function requires backslashes
                files.remove(file)
                total_columns     = roundup(len(files) / ITEMS_PER_COLUMN)
                lines_last_column = len(files) % ITEMS_PER_COLUMN

                if lines_last_column == 0:
                    lines_last_column = ITEMS_PER_COLUMN
                                
                if not files:
                    total_columns = 1
                    lines_last_column = 1

                current_position  = (column - 1) * ITEMS_PER_COLUMN + line - 1
                current_position -= 1

                if current_position == -1:
                    current_position = 0
                
                column = int((current_position) / ITEMS_PER_COLUMN) + 1
                line   = (current_position) % ITEMS_PER_COLUMN + 1
                
                if column < leftwise_column:
                    leftwise_column = column


            except Exception as e:
                e = str(e)
                cls()
                move_cursor(INFO_POS, 0)
                print(f'{json_folder}{file}.json')
                input(f'\n{e[e.find("]")+2:e.find(":")]}.\nPress enter to continue.\n')

            print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])

        # open recycle bin in windows file explorer
        if command == key.CTRL_B:
            subprocess.run("explorer shell:RecycleBinFolder")

        # update current directory (if link file has been restored)
        if command == key.CTRL_U:
            files, total_columns, lines_last_column = get_files()

            print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # making filenames longer
        if command == "=" and 1 < MAX_COLUMNS:
            # changing the width of filenames to maximum possible if we have one less column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS - 1)) - SPACE_BEFORE
            # MAX_NAME_WIDTH += 1 # increasing size of filenames
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])
            if (column - leftwise_column) >= MAX_COLUMNS:
                column -= 1

        # making filenames shorter
        if command == "-" and 8 < MAX_NAME_WIDTH:
            # changing the width of filenames to leave space for an additional column
            MAX_NAME_WIDTH = int(TERM_WIDTH / (MAX_COLUMNS + 1)) - SPACE_BEFORE
            MAX_COLUMNS = int(TERM_WIDTH / (SPACE_BEFORE + MAX_NAME_WIDTH))
            print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # help page
        if command == '?':
            cls()
            move_cursor(0, 0)
            print(FILE_HELP_PAGE)
            input("Press enter to continue.\n")
            print_list(files[(leftwise_column - 1) * ITEMS_PER_COLUMN:])


        # cancel move/copy
        if command == key.BACKSPACE:
            return None, (column - 1) * ITEMS_PER_COLUMN + line - 1


        # quit application
        if command == key.ESC:
            cls()
            move_cursor(0, 0)
            cursor.show()
            break


def main():
    cursor.hide()

    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print("\nConsole application for keeping track of important links.\n")

    else:
        saved_pos = 0
        while (True):
            os.system("title Link Master Menu")
            json_file_path, saved_pos = json_file_loop(saved_pos)
            link_list_loop(json_file_path)


if __name__ == '__main__':
    main()
