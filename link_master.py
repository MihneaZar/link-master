from ConsoleListInterface import ConsoleListInterface, MenuInterface, waitForEnter, cls
from send2trash import send2trash
from readchar import readkey, key
from functools import reduce
import subprocess
import requests
import shutil
import json
import yaml
import sys
import os

try:
    gkeepapi_imported = True
    import gkeepapi
except:
    gkeepapi_imported = False

HOMEPATH   = os.path.dirname(os.path.realpath(__file__)) 
DATAPATH   = f"{HOMEPATH}/metadata"
JSONFOLDER = f"{HOMEPATH}/json_data"

sys.stderr = open(f'{DATAPATH}/errors.txt', "a")

FILENAME     = "Filename"
DATA         = "Data"
DESCRIPTIONS = "Description List"
DESC         = "Description"
INCOGNITO    = "Incognito"
LINKS        = "Links"

KEEP_EMAIL = ""


sys.stderr = open(f'{DATAPATH}/errors.txt', "a")

# for custom input in the link, such as show season and episode
LINK_INPUT_START = '\\{'
LINK_INPUT_END   = '\\}'

YES = YES
NO = NO

# creating json_data folder
if not os.path.isdir(JSONFOLDER):
    os.mkdir(JSONFOLDER)
    shutil.copy(f'{DATAPATH}/Examples.json', f'{JSONFOLDER}/Examples.json')

def yes_or_no(question, default_answer=YES, newline=True):
    if newline:
        print(f'{question}\nY/N', flush=True)
    else: 
        print(f'{question} (Y/N): ', end='', flush=True)
   default_answer = default_answer.capitalize()
    answer = readkey().lower()
    while not answer in ['y', 'n']:
        if answer == key.ENTER:
            print(default_answer)
            if newline:
                print()
            return default_answer
        
        answer = readkey().lower()

    
    answer = YES if answer == 'y' else NO
    print(answer)
    if newline:
        print()
        
    return answer

    

def gkeep_upload(press_enter=True):
    if not gkeepapi_imported:
        raise ModuleNotFoundError

    paths = [line.replace('\n', '') for line in open(f'{DATAPATH}/.paths').readlines()]
    paths += [""] * (2 - len(paths)) # adding empty strings so that the following commands wont raise an error

    KEEP_TOKEN = paths[0]
    KEEP_PATH  = paths[1] if paths[1] else f'{DATAPATH}/.keep.json'

    import gkeepapi

    print("Starting Google Keep upload...")

    keep = gkeepapi.Keep()

    print("Downloading newest versions of notes...")
    if os.path.isfile(KEEP_PATH):
        keep.authenticate(KEEP_EMAIL, KEEP_TOKEN, state=json.load(open(KEEP_PATH)))
    else:
        keep.authenticate(KEEP_EMAIL, KEEP_TOKEN)

    label = keep.findLabel('Link Master')
    if not label:
        label = keep.createLabel('Link Master')

    print("Deleting previous notes in label 'Link Master'...")
    for note in keep.find(labels=[keep.findLabel('Link Master')]):
        note.delete()

    print("Adding new notes locally...")

    # warning note for the 'Link Master' label, since all notes in label get deleted on upload
    note = keep.createNote("DO NOT ADD THIS LABEL", "All notes with this label are deleted on upload from Link Master app.")
    note.labels.add(label)
    for json_file in os.listdir(JSONFOLDER):
        link_data = json.load(open(f'{JSONFOLDER}/{json_file}'))

        # checking if link list has data
        if link_data[DATA]:
            note_text = ""
            for entry in link_data[DATA]:
                entry_text = entry[DESC] + ":"

                pos = 1
                for link in entry[LINKS]:
                    counting = f'{pos}.\n' if 2 <= len(entry[LINKS]) else "- " # numbered links if multiple
                    entry_text += f'\n{counting}{link}'  

                    pos += 1
            
                note_text += entry_text + "\n\n"

            note_text = note_text[:-2] # removing trailing newlines

            note = keep.createNote(json_file[:json_file.rfind('.')], note_text)
            note.labels.add(label)
            note.archived = True

        # if link list has no data, create empty keep note
        else:
            note = keep.createNote(json_file[:json_file.rfind('.')])
            note.labels.add(label)
            note.archived = True


    print("Uploading new notes...")
    keep.sync()

    print("Saving newest Google Keep state (for faster uploads in the future)...")

    # Store Keep cache
    with open(KEEP_PATH, 'w') as file:
        json.dump(keep.dump(), file)

    print("Upload complete.\n")

    if press_enter:
        print("Press enter to continue.")
        waitForEnter()    


def print_entry_details(entry, removed_links=[]):
    print_entry  = f'Description: {entry[DESC]}\n'
    print_entry += f'Open in incognito mode: {entry[INCOGNITO]}\n'
    print_entry += f'Links:'
    
    for pos in range(len(entry[LINKS])):
        removed_text = "(set to be removed) " if (pos + 1) in removed_links else ""
        print_entry += f'\n{pos + 1}. {removed_text}{entry[LINKS][pos]}'

    return print_entry


def get_links():
    links = []
    print("Links (type '?' for custom commands info):")
    
    curr_link = input()
    while (not (curr_link == "" or curr_link.isspace())):

        if curr_link == '?':
            print(f"For custom input, use the format '{LINK_INPUT_START}input_prompt{LINK_INPUT_END}' within the link (the text will be prompted on every link open).")
            print(f"For custom input to be reused, add variable as 'var var_name={LINK_INPUT_START}input_prompt{LINK_INPUT_END}'. Spaces are not allowed in var_name.")
            print(f"The prompt will be provided only once for every variable, and '{LINK_INPUT_START}var_name{LINK_INPUT_END}' from links will be replaced by its value.")
                
            curr_link = input()
            continue


        # checking that var has an input prompt
        if curr_link.startswith("var ") and LINK_INPUT_START not in curr_link:
            print("Input prompt missing, variable ignored.")
            curr_link = input()
            continue


        # checking custom input
        input_level = 0
        for pos in range(len(curr_link)):
            if curr_link[pos:pos+len(LINK_INPUT_START)] == LINK_INPUT_START:
                input_level += 1

            if curr_link[pos:pos+len(LINK_INPUT_END)] == LINK_INPUT_END:
                input_level -= 1

            # if there have been two {LINK_INPUT_START}'s in a row, 
            # or a {LINK_INPUT_END} without a {LINK_INPUT_START} before it
            # the custom input format is wrong
            if input_level not in [0, 1]:
                break

        # {LINK_INPUT_START} left without a {LINK_INPUT_END} after  it
        if input_level != 0:
            print("Custom input format is wrong, entry ignored.")

        else:
            links.append(curr_link)

        curr_link = input()

    return links

# if the entry exists, it will accept empty description
# otherwise it will cancel when it is empty
def create_entry():
    description = input("Description: ")

    # if the description is empty, cancels adding this entry
    if (not description or description.isspace()):
        return None, None, None

    incognito = yes_or_no("Open in incognito mode", default_answer=NO, newline=False)

    links = get_links()

    return description, incognito, links


def edit_entry(entry):
    menu_structure = yaml.safe_load(open(f"{DATAPATH}/link_list_edit.yaml"))
    menu_structure["Edit"]["Remove links"] = {f'{i}.': None for i in range(1, len(entry[LINKS]) + 1)}

    menu = MenuInterface(menu_structure, submenuColor="light_grey", optionColor="light_grey", supressColorWarning=True)

    cls()

    description   = None
    incognito     = None
    added_links   = []
    removed_links = [] # they will be saved by the index

    while True:
        menu.changeMainMenu(print_entry_details({DESC: description if description else entry[DESC], INCOGNITO: incognito if incognito else entry[INCOGNITO], LINKS: entry[LINKS] + added_links}, removed_links))
        path = menu.interactWithMenu()

        # ignoring backspace in main menu
        if not path:
            continue
        
        option = path[-1]
        option = option[:option.find(' ')]

        if option == "Save":
            changed = (description or incognito or added_links or removed_links)
            if not changed or menu.separateInteraction(function=lambda: yes_or_no("Are you sure you want to save changes?", NO)) == YES:
                all_links = entry[LINKS] + added_links
                return description, incognito, [all_links[pos] for pos in range(len(all_links)) if (pos + 1) not in removed_links] 
            
            continue
            


        if option == "Change":
            description = menu.separateInteraction(function=lambda: input("New description: "), showCursor=True)
            description = description if description != entry[DESC] else None # ignoring unchanged description
            continue

        if option == "Toggle":
            if not incognito:
                incognito = YES if entry[INCOGNITO] == NO else NO
            else:
                incognito = None
            continue
        
        if option == "Add":
            new_links = menu.separateInteraction(function=get_links, showCursor=True)
            menu.addOptions(['Remove links'], {f'{i}.': None for i in range(len(entry[LINKS] + added_links) + 1, len(entry[LINKS] + added_links + new_links) + 1)})
            added_links += new_links
            continue

        if option == "Remove": 
            menu.setTopText(print_entry_details({DESC: description if description else entry[DESC], INCOGNITO: incognito if incognito else entry[INCOGNITO], LINKS: entry[LINKS] + added_links}, removed_links) \
                            + "\n\nSet links to be removed:\n")
            continue
        
        # setting link to be removed/unremoved
        if 2 <= len(path) and path[-2] == "Remove links":
            link_index = int(path[-1][:path[-1].find('.')])

            changes = MenuInterface.selectMultipleOptions([f'{i}.' for i in removed_links], f'{link_index}.', [f'{i}.' for i in range(1, len(entry[LINKS] + added_links) + 1)], 'x')

            # setting link to be removed
            if link_index not in removed_links:
                removed_links.append(link_index)
            # setting link to be unremoved
            else:
                removed_links.remove(link_index)
            
            menu.changeOptionNames(path[:-1], changes)

            menu.setTopText(print_entry_details({DESC: description if description else entry[DESC], INCOGNITO: incognito if incognito else entry[INCOGNITO], LINKS: entry[LINKS] + added_links}, removed_links) \
                            + "\n\nSet links to be removed:\n")
            continue


        if option == "Cancel": 
            changed = (description or incognito or added_links or removed_links)
            if not changed or menu.separateInteraction(function=lambda: yes_or_no("Are you sure you want to cancel changes?", NO)) == YES:
                return None, None, entry[LINKS]


def parse_link(link, vars):
    if LINK_INPUT_START in link:
        while LINK_INPUT_START in link:
            pos = link.find(LINK_INPUT_START) + len(LINK_INPUT_START)
            if link[pos:link.find(LINK_INPUT_END)] in vars:
                value = vars[link[pos:link.find(LINK_INPUT_END)]]
            else:
                value = input(f'{link[pos:link.find(LINK_INPUT_END)]}: ')

            if value.isspace():
                return None

            link = link[:link.find(LINK_INPUT_START)] + value + link[link.find(LINK_INPUT_END)+len(LINK_INPUT_END):]
    
    return link

                                                                               # overwriting internal rename command
LINK_COMMANDS_LIST = [key.ENTER, key.CTRL_O, key.CTRL_N, key.CTRL_D, key.CTRL_E, key.CTRL_R, key.CTRL_X, key.CTRL_C, key.DELETE, key.CTRL_B, key.CTRL_K, key.BACKSPACE, key.ESC]
LINK_HELP_PAGE    = f"""
Link list page.

Controls:
    - arrow keys -> moving between existing entries in list.
    - character  -> move cursor to the next entry that starts with character, if it exists.
    - ctrl+f     -> search for the next entry that contains string, if it exists (not case sensitive).
    - '\\'        -> find next entry that contains last searched string.
    - enter      -> open entry links, in the selected mode (normal or incognito).
    - ctrl+o     -> download headers and webpage content from link to given folder.
    - ctrl+n     -> create new entry.
    - ctrl+d     -> see details of selected entry.
    - ctrl+e     -> edit info for selected entry.
    - ctrl+x     -> move selected entry into another link list.
    - ctrl+c     -> copy selected entry into a chosen link list (including the same one).
    - delete     -> remove entry (warning: data is lost forever).
    - ctrl+u     -> update printed list (for terminal size change).
    - ctrl+k     -> upload all new changes (in this list and all others) to Google Keep.
    - '='/'-'    -> increase/decrease number of characters in entry names before they are cut off.
    - '?'        -> display current help page.
    - backspace  -> return to main menu (list of all link lists).
    - escape     -> quit application.
""" 

def link_list_loop(console: ConsoleListInterface, json_file_path, saved_pos):
    if not json_file_path:
        return
    
    # console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")
    console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")
    
    json_data = json.load(open(json_file_path))

    console.updateList(json_data[DESCRIPTIONS])
    console.configure(specialCommands=LINK_COMMANDS_LIST, helpPage=LINK_HELP_PAGE)
    console.updatePos(0)

    while (True):
        command, curr_pos = console.interact()

        # open links from selected list
        if command == key.ENTER:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            entry  = json_data[DATA][curr_pos]
            answer = entry[INCOGNITO].lower()

            chrome_arg = "" if answer == NO else "-incognito"

            # resolving link variables
            vars = {}
            for var in entry[LINKS]:
                if var.startswith("var "):
                    vars[var[len("var "):var.find('=')].replace(' ', '')] = console.separateInteraction(function=lambda: 
                                                                    input(f'{var[var.find(LINK_INPUT_START)+2:var.find(LINK_INPUT_END)]}: '), showCursor=True)
                 
            open_links = []
            for link in entry[LINKS]:
                # ignoring vars 
                if link.startswith("var "):
                    continue

                link = console.separateInteraction(function=lambda: parse_link(link, vars), showCursor=True)

                # link is None if custom input was cancelled
                if link:
                    open_links.append(link)

            for link in open_links:
                    subprocess.Popen(f'start chrome {chrome_arg} /new-tab \"{link}\"', shell=True)
            
            continue


        if command == key.CTRL_O:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            entry  = json_data[DATA][curr_pos]
            answer = entry[INCOGNITO].lower()
            
            # resolving link variables
            vars = {}
            for var in entry[LINKS]:
                if var.startswith("var "):
                    vars[var[len("var "):var.find('=')].replace(' ', '')] = console.separateInteraction(function=lambda: 
                                                                    input(f'{var[var.find(LINK_INPUT_START)+2:var.find(LINK_INPUT_END)]}: '), showCursor=True)
                
            open_links = []
            for link in entry[LINKS]:
                # ignoring vars 
                if link.startswith("var "):
                    continue

                link = console.separateInteraction(function=lambda: parse_link(link, vars), showCursor=True)

                # link is None if custom input was cancelled
                if link:
                    open_links.append(link)

            for link in open_links:
                response = console.separateInteraction(message="Downloading response...", function=lambda: requests.get(link))

                save_dir = console.separateInteraction(function=lambda: input(f"Saving response from '{link}'.\nFull path to save response at: "), showCursor=True)
                while (save_dir and not save_dir.isspace()) and (not os.path.isabs(save_dir) or not os.path.isdir(save_dir)):
                    save_dir = console.separateInteraction(function=lambda: input(f"Saving response from '{link}'.\nDirectory not found, try again (or leave empty to skip link): "), showCursor=True)

                if not save_dir or save_dir.isspace():
                    continue

                save_file = console.separateInteraction(function=lambda: input(f"Saving response from '{link}'.\nName of file (without extension) - it WILL overwrite: "), showCursor=True)
                saved = False
                while not saved and (save_file and not save_file.isspace()):
                    try:
                        with open(f'{save_dir}/{save_file}.txt', "w", encoding='utf-8') as file:
                            # save_dict = {"Link": link, "Headers": response.headers, "Content": f'"""{response.text}"""'}
                            # print(save_dict)
                            # json.dump(save_dict, file, ensure_ascii=False, indent=4)
                            file.write(f'Link:\n{link}\n\n')
                            file.write(f'Headers:\n{response.headers}\n\n')
                            file.write(f'Website content:\n{response.text}')
                            saved = True
                    except Exception as e:
                        save_file = console.separateInteraction(function=lambda: input(f"Saving response from '{link}'.\nFilename contains illegal character, try again (or leave empty to skip link): "), showCursor=True)
            
            continue


        # creating new entry
        if command == key.CTRL_N:
            description, incognito, links = console.separateInteraction(message="Add new entry:", function=create_entry, showCursor=True)
            
            if not description:
                console.separateInteraction(message="Description must not be empty.\n")
                continue

            json_data[DATA].append({DESC: description, INCOGNITO: incognito, LINKS: links})
            json_data[DESCRIPTIONS].append(description)
            
            if links: # only setting upload to True if at least one link has been added
                console.upload = True

            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)

            console.updateList(json_data[DESCRIPTIONS])
            console.updatePos(json_data[DESCRIPTIONS].index(description))

            continue
            
        # showing details of selected entry
        if command == key.CTRL_D:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            console.separateInteraction(message=f'{print_entry_details(json_data[DATA][curr_pos])}\n')

            continue

        # replacing info in selected entry
        if command == key.CTRL_E:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            description, incognito, links = console.separateInteraction(function=lambda: edit_entry(json_data[DATA][curr_pos]))

            print(description)
            print(incognito)
            print(links)
            input()
                
            if description:
                json_data[DESCRIPTIONS][curr_pos] = description
                json_data[DATA][curr_pos][DESC] = description
                console.updateList(json_data[DESCRIPTIONS])
                
            if incognito:
                json_data[DATA][curr_pos][INCOGNITO] = incognito
                
            if json_data[DATA][curr_pos][LINKS] != links: # in edit, we only care about potentially added links for auto-upload
                console.upload = True

            json_data[DATA][curr_pos][LINKS] = links

            # at least one field was changed, updating file
            if description or incognito or links:
                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)

            continue


        # moves selected entry to another link list:
        if command == key.CTRL_X:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            entry = json_data[DATA][curr_pos]

            console.setTopText(f"Moving '{entry[DESC]}'\n")
            move_file_path, _ = json_file_loop(console, saved_pos)
            if not move_file_path or json_file_path == move_file_path:
                console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")
                console.updateList(json_data[DESCRIPTIONS])
                console.configure(specialCommands=LINK_COMMANDS_LIST, helpPage=LINK_HELP_PAGE)
                console.updatePos(curr_pos)
                continue

            # adding entry to other json file
            move_data = json.load(open(move_file_path))

            move_data[DATA].append(entry)
            move_data[DESCRIPTIONS].append(entry[DESC])

            with open(move_file_path, 'w', encoding='utf-8') as file:
                json.dump(move_data, file, ensure_ascii=False, indent=4)

            # removing entry from current json file
            json_data[DATA].pop(curr_pos)
            json_data[DESCRIPTIONS].pop(curr_pos)

            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)

            console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")

            console.updateList(json_data[DESCRIPTIONS])
            console.configure(specialCommands=LINK_COMMANDS_LIST, helpPage=LINK_HELP_PAGE)
            console.updatePos(curr_pos)

            continue

        # copies selected entry to link list
        if command == key.CTRL_C:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            entry = json_data[DATA][curr_pos]

            console.setTopText(f"Copying '{entry[DESC]}'\n")

            copy_file_path, _ = json_file_loop(console, saved_pos)
            if not copy_file_path:
                console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")
                console.updateList(json_data[DESCRIPTIONS])
                console.configure(specialCommands=LINK_COMMANDS_LIST, helpPage=LINK_HELP_PAGE)
                console.updatePos(curr_pos)
                continue

            if json_file_path == copy_file_path:
                # adding entry to the same json file
                json_data[DATA].append(entry)
                json_data[DESCRIPTIONS].append(entry[DESC])

                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)
                
                console.setTopText('json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]\n')

                console.updateList(json_data[DESCRIPTIONS])

                continue

            # adding entry to other json file
            copy_data = json.load(open(copy_file_path))

            copy_data[DATA].append(entry)
            copy_data[DESCRIPTIONS].append(entry[DESC])

            with open(copy_file_path, 'w', encoding='utf-8') as file:
                json.dump(copy_data, file, ensure_ascii=False, indent=4)

            console.setTopText(f'json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]\n')
            
            console.updateList(json_data[DESCRIPTIONS])
            console.configure(specialCommands=LINK_COMMANDS_LIST, helpPage=LINK_HELP_PAGE)
            console.updatePos(curr_pos)

            continue

        # remove entry from link list
        if command == key.DELETE:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            remove_answer = console.separateInteraction(function=lambda: yes_or_no(f'Are you sure you want to remove \'{json_data[DESCRIPTIONS][curr_pos]}\'?\nData will be lost forever.', default_answer=NO), showCursor=True)

            if remove_answer == NO:
                continue

            json_data[DATA].pop(curr_pos)
            json_data[DESCRIPTIONS].pop(curr_pos)

            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
                
            console.updateList(json_data[DESCRIPTIONS])

            curr_pos -= 1

            if curr_pos == -1:
                curr_pos = 0

            console.updatePos(curr_pos)

            continue


        # uploading to drive
        if command == key.CTRL_K:
            try:    
                console.separateInteraction(function=gkeep_upload)

            except Exception as e:
                console.separateInteraction(message=f"{str(e)}\nError encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.\n")
            
            console.upload = False # either the upload succeeded, so no need to upload again, or it failed, and it will fail again
            continue


        # return to file selection
        if command == key.BACKSPACE:
            return


        # quit application
        if command == key.ESC:
            # console.upload = False
            console.exitInterface()

            # uploading to google keep if changes to links haven't been uploaded
            if console.upload:
                try:
                    gkeep_upload(False)
                except Exception as e:
                    # console.separateInteraction(message=f"{str(e)}\nError encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.\n")
                    pass
            quit()


# IMPORTANT NOTE: CTRL_H is SAME as BACKSPACE
FILE_COMMANDS_LIST = [key.ENTER, key.CTRL_N, key.CTRL_R, key.DELETE, key.CTRL_B, key.CTRL_U, key.CTRL_T, key.CTRL_K, key.BACKSPACE, key.ESC]
FILE_HELP_PAGE    = """
Link Master main menu.

Controls:
    - arrow keys -> moving between existing link lists.
    - character  -> move cursor to the next link list that starts with character, if it exists.
    - ctrl+f     -> search for the next link list that contains string, if it exists (not case sensitive).
    - '\\'        -> find next link list that contains last searched string.
    - enter      -> open selected link list / moves or copies entry to selected link list.
    - ctrl+n     -> create new link list.
    - ctrl+r     -> rename selected link list.
    - delete     -> move link list to recycle bin.
    - ctrl+b     -> open recycle bin in Windows File Explorer (to restore link lists).
    - ctrl+u     -> update available link lists (if one or more have been restored from bin).
    - ctrl+t     -> toggle showing hidden link lists (to make a list hidsden, name it starting with '.').
    - '='/'-'    -> increase/decrease number of characters in link list names before they are cut off.
    - '?'        -> display current help page.
    - ctrl+k     -> upload all new changes in all link lists to Google Keep.
    - backspace  -> if currently moving or copying entry, cancel action.
    - escape     -> quit application.
""" 


# returns selected json file
def json_file_loop(console: ConsoleListInterface, saved_pos=0):
    files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
    files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files

    console.updateList(files)
    console.configure(specialCommands=FILE_COMMANDS_LIST, helpPage=FILE_HELP_PAGE)
    console.updatePos(saved_pos)
    
    while (True):
        command, curr_pos = console.interact()

        # open selected link list
        if command == key.ENTER:
            return f'{JSONFOLDER}/{files[curr_pos]}.json', curr_pos


        # creating new link list
        if command == key.CTRL_N:
            filename = console.separateInteraction(function=lambda: input("Type name for new link list:\n"), showCursor=True)
            
            try:
                # ignoring command if filename is empty
                if not filename or filename.isspace():
                    continue
                
                if '/' in filename or '\\' in filename:
                    console.separateInteraction(message="Illegal character used in name.\n")
                    continue

                # ignoring command if file already exists
                if os.path.isfile(f'{JSONFOLDER}/{filename}.json'):
                    console.separateInteraction(message="Link list with this name already exists.\n")
                    continue

                with open(f'{JSONFOLDER}/{filename}.json', 'w', encoding='utf-8') as file:
                    json.dump({FILENAME: filename, DESCRIPTIONS: [], DATA: []}, file, ensure_ascii=False, indent=4)

                # if a hidden file was created, automatically show hidden files
                if filename[0] == '.':
                    console.hideFiles = False
                    
                files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
                files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files

                console.updateList(files)
                console.updatePos(files.index(filename))

            except:
                console.separateInteraction(message="Illegal character used in name.\n")

            continue

        # rename link list
        if command == key.CTRL_R:
            file = files[curr_pos]
            filename = console.separateInteraction(function=lambda: input(f'Rename {file} to:\n'), showCursor=True)

            try:
                # ignoring command if filename is empty
                if not filename or filename.isspace():
                    console.separateInteraction(message="Link list name must not be empty.\n")
                    continue

                if '/' in filename or '\\' in filename:
                    console.separateInteraction(message="Illegal character used in name.\n")
                    continue

                # ignoring command if file already exists
                if os.path.isfile(f'{JSONFOLDER}/{filename}.json'):
                    console.separateInteraction(message="Link list with this name already exists.\n")
                    continue
                
                os.rename(f'{JSONFOLDER}/{file}.json', f'{JSONFOLDER}/{filename}.json')

                # updating filename in json file
                json_data = json.load(open(f'{JSONFOLDER}/{filename}.json'))
                json_data["Filename"] = filename

                with open(f'{JSONFOLDER}/{filename}.json', 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)

                files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
                files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files
                    
                console.updateList(files)
                if filename in files:
                    console.updatePos(files.index(filename))
                
            except Exception as e:
                console.separateInteraction(message=e)
                # console.separateInteraction(message="Illegal character used in name.\n")

            continue

        # move link list to recycle bin
        if command == key.DELETE:
            try:
                file = files[curr_pos]
                send2trash(f'{JSONFOLDER}/{file}.json'.replace('/', '\\')) # this function requires backslashes
                files.pop(curr_pos)

                console.updateList(files)

                curr_pos -= 1

                if curr_pos == -1:
                    curr_pos = 0

                console.updatePos(curr_pos)

            except Exception as e:
                e = str(e)

                if "WinError" in e:
                    e = e[e.find("]")+2:e.find(":")]

                console.separateInteraction(message=f'\n{e}.\n')

            continue

        # open recycle bin in windows file explorer
        if command == key.CTRL_B:
            subprocess.run("explorer shell:RecycleBinFolder")
            continue

        # update list of files (if link file has been restored)
        if command == key.CTRL_U:
            files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
            files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files

            console.updateList(files)
            continue


        if command == key.CTRL_T:
            if console.hideFiles:
                console.hideFiles = (console.separateInteraction(function=lambda: yes_or_no("Show hidden lists?", default_answer=NO), showCursor=True) == NO)
                if not console.hideFiles:
                    curr_file = files[curr_pos]
                    files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])

                    console.updateList(files)
                    console.updatePos(files.index(curr_file))
            else:
                console.hideFiles = True
                curr_file = files[curr_pos]
                files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
                files = list(filter(lambda file: file[0] != '.', files))

                console.updateList(files)
                if curr_file in files:
                    console.updatePos(files.index(curr_file))
                
            continue


        # uploading to drive
        if command == key.CTRL_K:
            try:    
                console.separateInteraction(function=gkeep_upload)

            except Exception as e:
                console.separateInteraction(message=f"{str(e)}\nError encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.\n")
            
            console.upload = False # either the upload succeeded, so no need to upload again, or it failed, and it will fail again
            continue


        # cancel move/copy
        if command == key.BACKSPACE:
            return None, curr_pos


        # quit application
        if command == key.ESC:
            # console.upload = False
            console.exitInterface()
            
            # uploading to google keep if changes to links haven't been uploaded
            if console.upload:
                try:
                    gkeep_upload(False)
                except Exception as e:
                    # console.separateInteraction(message=f"{str(e)}\nError encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.\n")
                    pass
            quit()


def main():
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print("\nConsole application for keeping track of important links.\n")

    else:
        saved_pos = 0
        console = ConsoleListInterface()
        console.hideFiles = True  # hidden files
        console.upload    = False # determines whether the app will automatically start gkeep_upload on quit (Esc) 
        console.setTitle("Link Master")
        while (True):
            console.setTopText("Main Menu\n")
            json_file_path, saved_pos = json_file_loop(console, saved_pos)
            link_list_loop(console, json_file_path, saved_pos)


if __name__ == '__main__':
    main()
