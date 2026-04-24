from googledrivedownloader import download_file_from_google_drive
from validator_collection import checkers
from readchar import readkey, key
from termcolor import colored
from blessed import Terminal
from functools import reduce
from time import sleep
import subprocess
import webbrowser
import zipfile
import json
import sys
import os

term = Terminal()
cls = lambda: os.system('cls' if os.name=='nt' else 'clear')

home_folder = "C:/Users/Mihnea/Desktop/Random thoughts/Cool stuff/Link List/" if sys.platform == "win32" else ""
json_folder = f'{home_folder}json_data'
curr_file   = None 

sys.stderr = open(f'{home_folder}errors.txt', "a")

# full command list
# in order of desired matching
command_list = [
    "add", "list", "search", "fields", "open", "edit", "remove",                # entry commands
    "move", "copy", "name", "rename", "switch", "delete", "upload", "download", # file commands
    "help", "clear", "exit", "quit"                                             # app commands
]

FILENAME     = "Filename"
DATA         = "Data"
DESCRIPTIONS = "Description List"
DESC         = "Description"
INCOGNITO    = "Incognito"
LINKS        = "Links"


def move_cursor(y, x):
    sys.stdout.write("\033[%d;%dH" % (y, x))


def get_filename_from_user(filename_list, info_text, allow_empty=False, ignore_exit=False):
    print(info_text, end='')
    cursor_y_pos, cursor_x_pos = term.get_location()
    cursor_x_pos += 1

    filename_list.sort()
    
    term_width = os.get_terminal_size()[0]
    continuous_tab = False
    poss_files = []

    hit_tab = False

    filename = ""
    while (True):
        command = readkey()

        if command == key.TAB:
            if not hit_tab:
                hit_tab = True

            if not continuous_tab:
                if poss_files:
                    move_cursor(cursor_y_pos + 5, 0)
                    curr_pos = 1
                    for folder in poss_files:
                        next_print     = ' ' * len(folder + "; ") 
                        next_print_len = len(folder + "; ") 
                        if curr_pos + next_print_len <= term_width:
                            print(next_print, end = '')
                            curr_pos += next_print_len
                        else:
                            print()
                            print(next_print, end = '')
                            curr_pos = next_print_len

                else:
                    move_cursor(cursor_y_pos + 3, 0)
                    print("Possible files:\n")

                poss_files = [file for file in filename_list if file.lower().startswith(filename.lower())]
                if poss_files:
                    move_cursor(cursor_y_pos + 5, 0)
                    curr_pos = 1
                    for file in poss_files:
                        next_print     = file + "; "
                        next_print_len = len(file + "; ") 
                        if curr_pos + next_print_len <= term_width:
                            print(next_print, end = '')
                            curr_pos += next_print_len
                        else:
                            print()
                            print(next_print, end = '')
                            curr_pos = next_print_len
                
            else:
                move_cursor(cursor_y_pos + 1, cursor_x_pos)
                print(' ' * len(last_tab_found))
            
            move_cursor(cursor_y_pos + 1, cursor_x_pos)
            
            first_found = next((file for file in poss_files if file.startswith(filename) and (not continuous_tab or file > last_tab_found)), 
                next((file for file in poss_files if file.startswith(filename)), filename))
            last_tab_found = first_found
            continuous_tab = True
            print(first_found, end='', flush=True)

        else:
            if continuous_tab: 
                filename = last_tab_found
            continuous_tab = False
        
        if command.isalnum() or command in " ;\'()[]{}-_+=&^%$#@!":
            print(command, end='', flush=True)
            filename += command

        if command == key.BACKSPACE and filename:
            print("\b \b", end='', flush=True)
            filename = filename[:-1]

        if command == key.ENTER and (allow_empty or not (filename == "" or filename.isspace())):
            if hit_tab:
                # clear autocomplete results
                move_cursor(cursor_y_pos + 3, 0)
                print(' ' * len("Possible files:\n"))

                if poss_files:
                    move_cursor(cursor_y_pos + 5, 0)
                    curr_pos = 1
                    for folder in poss_files:
                        next_print     = ' ' * len(folder + "; ") 
                        next_print_len = len(folder + "; ") 
                        if curr_pos + next_print_len <= term_width:
                            print(next_print, end = '')
                            curr_pos += next_print_len
                        else:
                            print()
                            print(next_print, end = '')
                            curr_pos = next_print_len
            
            move_cursor(cursor_y_pos + 2, 0)
            break

        if not ignore_exit and command == key.ESC:
            cls()
            quit()

    return filename


def list_descriptions(descriptions, filter_words=[], filter_color="green"):
    filtered_descriptions = [desc for desc in descriptions if not filter_words or any(word in desc for word in filter_words)]
    if filtered_descriptions:
        print()
        for desc in filtered_descriptions:
            print("Description: ", end='')
            for word in filter_words:
                desc = desc.replace(word, colored(word, filter_color))

            print(desc)

        print()

    else:
        print("\nNo descriptions found.\n")

    return filtered_descriptions


def print_help(help_type=None):
    if not help_type:
        print()
        print("\'h[elp]\'         -> display this help list;")
        print("\'h[elp] e[ntry]\' -> display commands for link entries;")
        print("\'h[elp] f[ile]\'  -> display commands related to the files in which the information is stored;")
        print("\'h[elp] a[pp]\'   -> display commands for the application context;")
        print()
    
    elif "entry".startswith(help_type):
        print()
        print("\'a[dd]\'    -> add new links and description;")                             # done
        print("\'l[ist]\'   -> list all existing descriptions;")                            # done
        print("\'s[earch]\' -> search existing descriptions by filter words;")              # done
        print("\'f[ields]\' -> show fields of entries that fit filter words;")              # done
        print("\'o[pen]\'   -> open links from descriptions with filter words;")            # done
        print("\'e[dit]\'   -> edit entry that fits filter words (must be unqiue);")        # done
        print("\'r[emove]\' -> remove entries which include filter words;")                 # done

    elif "file".startswith(help_type):
        print()
        print("\'m[ove]\'     -> move entries containing filter words to another file;")    # done
        print("\'c[opy]\'     -> copy entries containing filter words to another file;")    # done
        print("\'n[ame]\'     -> show current file name")                                     
        print("\'ren[ame]\'   -> change name of info file;")                                # done
        print("\'sw[itch]\'   -> switch to another info file;")                             # done
        print("\'d[elete]\'   -> delete current info file;")                                # done
        print("\'u[pload]\'   -> upload link files to gdrive")
        print("\'do[wnload]\' -> download link files from gdrive")
    
    elif "app".startswith(help_type):
        print()
        print("\'h[elp]\'  -> show main help page;")                                        # done
        print("\'cl[ear]\' -> clears terminal;")                                            # done
        print("\'ex[it]\'  -> quit application.")                                           # done
        print("\'q[uit]\'  -> quit application (same as exit.\n")                           # done
    
    if help_type and ("entry".startswith(help_type) or "file".startswith(help_type)):
        print("\nFilter words are given on the same line, separated by space.\nTo include spaces in a filter word, use \'_\' instead.\n")


# returns command type (full name) and the filter word list
def parse_command(command):
    if command == '':
        return '', []

    if ' ' in command:
        return next((command_type for command_type in command_list if command_type.startswith(command[:command.find(' ')].lower())), ""), \
            list(map(lambda word: word.replace('_', ' '), filter(lambda word: word != '', command[command.find(' '):].split(' '))))

    else:
        return next((command_type for command_type in command_list if command_type.startswith(command.lower())), ""), []


def yes_or_no(question, other_options=[], newline = True):
    options = ["yes", "no"] + list(map(lambda opt: opt.lower(), other_options))
    list_other_options = list(filter(lambda opt: opt != "", other_options))
    list_other_options = '/' + reduce(lambda o1, o2: o1+'/'+o2, list_other_options) if list_other_options else ""
    if newline:
        print(f'{question}\nY/N{list_other_options}')
    else: 
        print(f'{question} (Y/N{list_other_options}): ', end='')

    cursor_y_pos, cursor_x_pos = term.get_location()
    cursor_y_pos += 1
    cursor_x_pos += 1

    answer = readkey().lower()
    while not any(option.startswith(answer) for option in options):
        if "" in options and answer == key.ENTER:
            print()
            return ""
        
        answer = readkey().lower()

    move_cursor(cursor_y_pos, cursor_x_pos)
    for option in options:
        if option.startswith(answer):
            print(option.capitalize())
            if newline:
                print()
            return option

    return None


# returns True if json_data has changed
# false otherwise
def entry_commands(command_type, filter_words, json_data):
    if command_type == "add":
        cls()
        print("Add new entry:\n\nDescription: ", end='')
        cursor_y_pos, cursor_x_pos = term.get_location()
        cursor_y_pos += 1
        cursor_x_pos += 1

        move_cursor(cursor_y_pos, cursor_x_pos)
        description = input()
        while len(description.replace(' ', '')) < 5 or description in json_data[DESCRIPTIONS]:
            print("Descriptions must be unique and must contain at least five non-empty characters.\n")
            move_cursor(cursor_y_pos, cursor_x_pos)
            print(' ' * len(description))
            move_cursor(cursor_y_pos, cursor_x_pos)
            description = input()
        
        print(' ' * len("Descriptions must be unique and must contain at least five non-empty characters.\n"))
        move_cursor(cursor_y_pos + 1, 0)

        incognito = yes_or_no("Open in incognito mode", ["Ask"], False).capitalize()

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

        if not links:
            print("Entries without links are ignored.\n")
            return False
            
        json_data[DATA].append({DESC: description, INCOGNITO: incognito, LINKS: links})
        json_data[DESCRIPTIONS].append(description)

        return True

    if command_type == "list":
        list_descriptions(json_data[DESCRIPTIONS])

        return False

    if command_type == "search":
        list_descriptions(json_data[DESCRIPTIONS], filter_words, "green")

        return False

    if command_type == "fields": 
        filtered_descriptions = list_descriptions(json_data[DESCRIPTIONS], filter_words, "green")

        if not filtered_descriptions or yes_or_no("Show fields for entries with these descriptions?") == "no":
            return False

        filtered_entries = [entry for entry in json_data[DATA] if entry[DESC] in filtered_descriptions]
        for entry in filtered_entries:
            link_list = reduce(lambda l1, l2: l1 + "\n" + l2, entry[LINKS])

            print(f'Description: {entry[DESC]}')
            print(f'Open in incognito mode: {entry[INCOGNITO]}')
            print(f'Links:\n{link_list}\n')

        return False

    if command_type == "open":
        filtered_descriptions = list_descriptions(json_data[DESCRIPTIONS], filter_words, "green")

        if not filtered_descriptions:
            return False

        if yes_or_no("Open links for given descriptions?") == "no":
            return False

        filtered_entries = [entry for entry in json_data[DATA] if entry[DESC] in filtered_descriptions]
                
        for entry in filtered_entries:
            if entry[INCOGNITO].lower() == "ask":
                answer = yes_or_no(f"Open \'{entry[DESC]}\' in incognito?")

            else:
                answer = entry[INCOGNITO].lower()

            chrome_arg = "" if answer == "no" else "-incognito"
            
            print(f"\'{entry[DESC]}\'")
            for link in entry[LINKS]:
                try:
                    print(link)
                    if sys.platform == "win32":
                        subprocess.Popen(f'start chrome {chrome_arg} /new-tab \"{link}\"',shell = True)
                    else:
                        webbrowser.open(link)
                except:
                    1+1
                sleep(0.1)

            print()

        return False

    if command_type == "edit":
        filtered_descriptions = list_descriptions(json_data[DESCRIPTIONS], filter_words, "green")

        if len(filtered_descriptions) != 1:
            print("Filter words must match only one entry to be edited.\n")
            return False

        if yes_or_no("Edit entry with this description?") == "no":
            return False

        entry_position = next((position for position in range(len(json_data[DATA])) 
                                if json_data[DATA][position][DESC] == filtered_descriptions[0]))
        
        link_list = reduce(lambda l1, l2: l1 + "\n" + l2, json_data[DATA][entry_position][LINKS])

        cls()

        print("Current fields:\n")
        print(f'Description: {json_data[DATA][entry_position][DESC]}')
        print(f'Open in incognito mode: {json_data[DATA][entry_position][INCOGNITO]}')
        print(f'Links:\n{link_list}')

        print()

        print("Input new information or leave empty to keep it the same.")
        print(colored("Warning: Overwritten data will be lost.\n", "red"))

        print("Description: ", end='')
        cursor_y_pos, cursor_x_pos = term.get_location()
        cursor_y_pos += 1
        cursor_x_pos += 1

        move_cursor(cursor_y_pos, cursor_x_pos)
        description = input()
        while len(description.replace(' ', '')) < 5 or description in json_data[DESCRIPTIONS]:

            # left empty, so description remains unchanged
            if (description == "" or description.isspace()):
                break

            print("Descriptions must be unique and must contain at least five non-empty characters.\n")
            move_cursor(cursor_y_pos, cursor_x_pos)
            print(' ' * len(description))
            move_cursor(cursor_y_pos, cursor_x_pos)
            description = input()
        
        print(' ' * len("Descriptions must be unique and must contain at least five non-empty characters."))
        move_cursor(cursor_y_pos + 1, 0)
            
        incognito = yes_or_no("Open in incognito mode", ["Ask", ""], False).capitalize()

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
            json_data[DESCRIPTIONS] = list(map(lambda desc: desc if desc != json_data[DATA][entry_position][DESC] else description, 
                                               json_data[DESCRIPTIONS]))
            json_data[DATA][entry_position][DESC] = description
            
        if incognito != "":
            json_data[DATA][entry_position][INCOGNITO] = incognito
            
        if links:
            json_data[DATA][entry_position][LINKS] = links

        # at least one field was changed
        if description != "" or incognito != "" or links:
            return True
        else:
            return False

    if command_type == "remove":
        filtered_descriptions = list_descriptions(json_data[DESCRIPTIONS], filter_words, "red")
            
        if not filtered_descriptions:
            return False

        warning_text = colored("Warning: This action can't be undone!", "red")

        if yes_or_no(f'Remove entries with these descriptions?\n{warning_text}') == "no":
            return False

        json_data[DATA] = [entry for entry in json_data[DATA] if entry[DESC] not in filtered_descriptions]
        json_data[DESCRIPTIONS] = [desc for desc in json_data[DESCRIPTIONS] if desc not in filtered_descriptions]

        return True

    return False


switch_filename = None

NO_CHANGE   = 0
SWITCH_FILE = 1
REOPEN_FILE = 2
REMOVE_ZIP  = 3 

# returns True if switching file
# returns False if the file remains the same
# quits the applications if delete then no
def file_commands(command_type, filter_words, json_data, json_file_path):
    if command_type == "move" or command_type == "copy":
        filtered_descriptions = list_descriptions(json_data[DESCRIPTIONS], filter_words, "green")

        if yes_or_no(f'{command_type.capitalize()} entries with these descriptions?') == "no":
            return NO_CHANGE
        
        existing_files = [file[:file.rfind('.')] for file in os.listdir(json_folder)]
        
        dest_filename = get_filename_from_user(existing_files, f'Type name of file to {command_type} to, or leave blank to cancel: ', allow_empty=True, ignore_exit=True)
        
        if dest_filename == "":
            print()
            return NO_CHANGE

        if dest_filename == json_data[FILENAME]:
            print("\nDestination file same as origin, command ignored.\n")
            return NO_CHANGE
        
        print()

        dest_file_path = f'{json_folder}/{dest_filename}.json'

        if dest_filename not in existing_files:
            if yes_or_no(f'\'{dest_filename}\' does not exist. Create new file?') == "no":
                return NO_CHANGE
            
            dest_json_data = {FILENAME: dest_filename, DESCRIPTIONS: [], DATA: []}
        else:
            dest_json_data = json.load(open(dest_file_path))

        entry_already_exists = False
        non_duplicates = []
        for desc in filtered_descriptions:
            if desc in dest_json_data[DESCRIPTIONS]:
                print(f'\'{desc}\' already exists in destination file.')
                entry_already_exists = True
            
            else:
                non_duplicates.append(desc)

        if entry_already_exists:
            print()
            if not non_duplicates:
                action_past = "moved" if command_type == "move" else "copied"
                print(f'Only duplicates, nothing was {action_past}.\n')
                return NO_CHANGE
            
            elif yes_or_no(f'{command_type.capitalize()} entries without duplicates?') == "no":
                return NO_CHANGE
            
            filtered_descriptions = non_duplicates

        filtered_entries = [entry for entry in json_data[DATA] if entry[DESC] in filtered_descriptions]
        dest_json_data[DESCRIPTIONS] += filtered_descriptions
        dest_json_data[DATA] += filtered_entries

        # update destination file
        with open(dest_file_path, 'w', encoding='utf-8') as file:
            json.dump(dest_json_data, file, ensure_ascii=False, indent=4)
        
        if command_type == "move":
            json_data[DESCRIPTIONS] = [desc for desc in json_data[DESCRIPTIONS] if desc not in filtered_descriptions]
            json_data[DATA]         = [entry for entry in json_data[DATA] if entry[DESC] not in filtered_descriptions]
            
            # update origin file
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)

            print(f'Entries moved to \'{dest_filename}\'.\n')

        else:
            print(f'Entries copied to \'{dest_filename}\'.\n')

        return NO_CHANGE

    if command_type == "name":
        print(f"\nCurrent open file: \'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}\'\n")
        return NO_CHANGE

    if command_type == "rename":
        if os.path.exists(json_file_path):
            curr_name = json_file_path[json_file_path.rfind('/'):json_file_path.rfind('.')]

            existing_files = [file[:file.rfind('.')] for file in os.listdir(json_folder)]

            new_name = input("\nType new name or leave empty to cancel: ")
            while (new_name in existing_files and new_name != curr_name):
                new_name = input("File with this name already exists, try again: ")

            if (new_name == '' or new_name.isspace() or new_name == curr_name):
                print("Name not changed.\n")
                return NO_CHANGE
            
            json_data[FILENAME] = new_name
            new_json_path = f'{json_folder}/{new_name}.json'
            os.rename(json_file_path, new_json_path)
            json_file_path = new_json_path
            print(f'Name of file changed to \'{new_name}\'.\n')

            # update json file
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            
            return NO_CHANGE
        
        else:
            print("\nFile not created yet (add entry to create).\n")
            return NO_CHANGE

    if command_type == "switch":
        if filter_words:
            global switch_filename
            # program knows that there were spaces between words (technically could be more than one, but that is ignored)
            # and each filter word had all '_' replaced with ' ', so it replaces them back
            switch_filename = reduce(lambda w1, w2: w1 + ' ' + w2, map(lambda word: word.replace(' ', '_'), filter_words))
        return SWITCH_FILE
    
    if command_type == "delete":
        if os.path.exists(json_file_path):
            warning_text = colored("Warning: This action will remove all data, and can't be undone!", "red")

            if yes_or_no(f'\nDelete current file?\n{warning_text}') == "no":
                print()
                return NO_CHANGE

            os.remove(json_file_path)
            answer = yes_or_no("Continue using this application?")
                    
            if answer == "yes":
                return SWITCH_FILE
                        
            else:
                cls()
                quit()

        else:
            print("\nFile not created yet (add entry to create).\n")

            return NO_CHANGE
    
    if command_type == "upload":
        print("\nUploading to drive...")

        from googleapiclient.http import MediaFileUpload
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        with zipfile.ZipFile(f'{json_folder}/link_list.zip', mode="w") as archive:
            for file in os.listdir(json_folder):
                if file != "link_list.zip":
                    archive.write(f'{json_folder}/{file}', arcname=file)
        
        scope = ['https://www.googleapis.com/auth/drive']
        service_account_json_key = f'{home_folder}credentials.json'
        credentials = service_account.Credentials.from_service_account_file(filename=service_account_json_key,scopes=scope)
        service = build('drive', 'v3', credentials=credentials)
            
        media = MediaFileUpload(f'{json_folder}/link_list.zip')

        service.files().update(fileId='1CzyOhyemL-Mj3ZhW8WZXg9FWVNXHCaSq', media_body=media).execute()
        print("Upload complete.\n")

        # os.remove(f'{json_folder}/link_list.zip')

        return REMOVE_ZIP

    if command_type == "download":
        print("\nDownloading from drive...")
        download_file_from_google_drive(file_id="1CzyOhyemL-Mj3ZhW8WZXg9FWVNXHCaSq", dest_path=f'{json_folder}/link_list.zip', unzip=True, overwrite=True)
        print("Download complete.\n")

        os.remove(f'{json_folder}/link_list.zip')

        return REOPEN_FILE

    return NO_CHANGE
    

def app_commands(command_type, filter_words):
    if command_type == "help":
        print_help(filter_words[0] if filter_words else None)
    
    if command_type == "clear":
        cls()

    if command_type in ["exit", "quit"]:
        cls()
        quit()

    
def main_loop(json_filename):
    cls()
    move_cursor(0, 0)

    json_file_path = f'{json_folder}/{json_filename}.json'

    if os.path.exists(json_file_path):
        json_data = json.load(open(json_file_path))
    else:
        json_data = {FILENAME: json_filename, DESCRIPTIONS: [], DATA: []}

    print(f'Current open file:\n\'{json_filename}\'\n')
    print("Type \'h[elp]\' to list help pages.\n")
    while (True):
        command_type, filter_words = parse_command(input(">> "))

        if entry_commands(command_type, filter_words, json_data):
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)


        file_result = file_commands(command_type, filter_words, json_data, json_file_path)

        if file_result == SWITCH_FILE:
            return
        
        if file_result == REOPEN_FILE:
            # reopening file, in case new data has been downloaded
            json_data = json.load(open(f'{json_folder}/{json_filename}.json'))

        if file_result == REMOVE_ZIP:
            os.remove(f'{json_folder}/link_list.zip')

        # check for rename of file
        if json_data[FILENAME] != json_filename:
            json_filename = json_data[FILENAME]
            json_file_path = f'{json_folder}/{json_filename}.json'
        
        app_commands(command_type, filter_words)

        if command_type in ["add", "edit", "clear"]:
            print("Type \'h[elp]\' to list help pages.\n")


def main():
    if not os.path.exists(json_folder):
        os.mkdir(json_folder)
    
    existing_files = [file[:file.rfind('.')] for file in os.listdir(json_folder)]

    cls()

    # filename given as command line argument
    if len(sys.argv) > 1:
        json_filename = reduce(lambda a1, a2: a1 + ' ' + a2, sys.argv[1:])
    else:    
        # asking user for filename
        json_filename = get_filename_from_user(existing_files, "Choose file to edit and read, or press esc to quit:\n")
        print()
        
    while True:
        if json_filename not in existing_files:
            answer = yes_or_no(f'\'{json_filename}\' not in existing data. Create new file?\nFile will be created with the first addded entry.')

        if json_filename in existing_files or answer == "yes":
            break
        else:
            print()
            json_filename = get_filename_from_user(existing_files, "Choose file to edit and read, or press esc to quit:\n")

    while (True):
        if json_filename in existing_files or answer == "yes":
            cls()
            main_loop(json_filename)
            print()

        # update in case files have been created or deleted
        existing_files = [file[:file.rfind('.')] for file in os.listdir(json_folder)]

        global switch_filename
        if switch_filename in existing_files:
            # filename given to switch command as argument (can only be existing filename)
            json_filename   = switch_filename
            switch_filename = None
        else:
            if switch_filename is not None:
                print(f'\'{switch_filename}\' not an existing file.\n')
                switch_filename = None
            json_filename = get_filename_from_user(existing_files, "Choose file to edit and read, or press esc to quit: ")
            print()

        if json_filename not in existing_files:
            answer = yes_or_no(f'\'{json_filename}\' not in existing data. Create new file?\nFile will be created with the first addded entry.')
        

        
    

if __name__ == "__main__":
    main()
