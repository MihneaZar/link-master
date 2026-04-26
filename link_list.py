import sys
import os

HOMEPATH = os.path.dirname(os.path.realpath(__file__))

if ".paths" not in os.listdir(HOMEPATH):
    console_path = input("Please type path to directory of ConsoleListInterface.py (or leave empty to cancel):\n")
    if console_path[0] == '"':
        console_path = console_path[1:]
    if console_path[-1] == '"':
        console_path = console_path[:-1]
    
    while console_path and not console_path.isspace() and not os.path.exists(f'{console_path}/ConsoleListInterface.py'):
        console_path = input("\nConsoleListInterface.py not found, please download and type path to directory:\n") 
        if console_path[0] == '"':
            console_path = console_path[1:]
        if console_path[-1] == '"':
            console_path = console_path[:-1]
    
    if not console_path or console_path.isspace():
        quit()

    open(f'{HOMEPATH}/.paths', 'w').write(console_path)

sys.path.append(open(f'{HOMEPATH}/.paths').read())


from ConsoleListInterface import ConsoleListInterface, waitForEnter # pyright: ignore[reportMissingImports]
from keep import KEEP_FILE, KEEP_TOKEN
from readchar import readkey, key
from send2trash import send2trash
from blessed import Terminal
from functools import reduce
import subprocess
import requests
import json

term = Terminal()

JSONFOLDER = f'{HOMEPATH}/json_data/'

sys.stderr = open(f'{HOMEPATH}/errors.txt', "a")

# for custom input in the link, such as show season and episode
LINK_INPUT_START = '\\{'
LINK_INPUT_END   = '\\}'

FILENAME     = "Filename"
DATA         = "Data"
DESCRIPTIONS = "Description List"
DESC         = "Description"
INCOGNITO    = "Incognito"
LINKS        = "Links"


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


def gkeep_upload(press_enter=True):
    print("Starting Google Keep upload...")
    
    import gkeepapi

    keep = gkeepapi.Keep()

    print("Downloading newest versions of notes...")
    if os.path.exists(KEEP_FILE):
        keep.authenticate('mihneabogzar@gmail.com', KEEP_TOKEN, state=json.load(open(KEEP_FILE)))
    else:
        keep.authenticate('mihneabogzar@gmail.com', KEEP_TOKEN)

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
        link_data = json.load(open(f'{JSONFOLDER}{json_file}'))

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
    with open(KEEP_FILE, 'w') as file:
        json.dump(keep.dump(), file)

    print("Upload complete.\n")

    if press_enter:
        print("Press enter to continue.")
        waitForEnter()


def print_entry_details(entry):
    print_entry  = f'Description: {entry[DESC]}\n'
    print_entry += f'Open in incognito mode: {entry[INCOGNITO]}\n'
    print_entry += f'Links:\n'
    
    for pos in range(len(entry[LINKS])):
        print_entry += f'{pos + 1}. {entry[LINKS][pos]}\n'

    return print_entry


# if the entry exists, it will accept empty description
# otherwise it will cancel when it is empty
def create_or_edit_entry(editing=False, prev_links=[]):
    description = input("Description: ")

    # if a new entry is being added and the description is empty, cancels action
    if not editing and (not description or description.isspace()):
        return None, None, None

    incognito = yes_or_no("Open in incognito mode", default_answer="no", other_options=[""] if editing else [], newline=False).capitalize()

    links = []
    print("Links (type '?' for custom commands info):")
    
    remaining_links = list(range(len(prev_links)))
    curr_link = input()
    while (not (curr_link == "" or curr_link.isspace())):

        if curr_link == '?':
            print(f"For custom input, use the format '{LINK_INPUT_START}input_prompt{LINK_INPUT_END}' within the link (the text will be prompted on every link open).")
            print(f"For custom input to be reused, add variable as 'var var_name={LINK_INPUT_START}input_prompt{LINK_INPUT_END}'. Spaces are not allowed in var_name.")
            print(f"The prompt will be provided only once for every variable, and '{LINK_INPUT_START}var_name{LINK_INPUT_END}' from links will be replaced by its value.")
            if editing:
                print("Links will be added to the existing list, do '-{pos}' or '-{link}' to remove an existing link. \
                    \nDo '-all' (case-sensitive) to remove all existing links, or '-undo' (case-sensitive) to undo all confirmed removals.")
                
            curr_link = input()
            continue

        # special commands for link editting (removing previous links)
        if editing and curr_link[0] == '-':
            curr_pos = -1
            if curr_link[1:] in prev_links:
                curr_pos = prev_links.index(curr_link[1:]) 

            if curr_link[1:].isdigit():
                curr_pos = int(curr_link[1:]) - 1


            solved = False
            if 0 <= curr_pos and curr_pos < len(prev_links):
                if curr_pos in remaining_links:
                    print(f"Entry {curr_pos + 1} - '{prev_links[curr_pos]}' will be removed.")
                    remaining_links.remove(curr_pos)
                
                solved = True
            
            if curr_link[1:] == 'all':
                remaining_links = []
                print("All current links will be removed.")

                solved = True

            if curr_link[1:] == 'undo':
                remaining_links = list(range(len(prev_links)))
                print("Previous removals will be ignored.")

                solved = True
                

            if not solved: 
                print("Unknown remove option.")

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

    links = [prev_links[pos] for pos in remaining_links] + links

    return description, incognito, links


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


LINK_COMMANDS_LIST = [key.ENTER, key.CTRL_O, key.CTRL_N, key.CTRL_D, key.CTRL_E, key.CTRL_X, key.CTRL_C, key.DELETE, key.CTRL_B, key.CTRL_K, key.BACKSPACE, key.ESC]
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

def link_list_loop(console, json_file_path, saved_pos):
    if not json_file_path:
        return
    
    os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]} - Link Master')

    json_data = json.load(open(json_file_path))

    console.updateList(json_data[DESCRIPTIONS])
    console.updateSpecialCommands(LINK_COMMANDS_LIST)
    console.updateHelpPage(LINK_HELP_PAGE)
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

            chrome_arg = "" if answer == "no" else "-incognito"

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
            description, incognito, links = console.separateInteraction(message="Add new entry:", function=create_or_edit_entry, showCursor=True)
            
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

            console.separateInteraction(message=print_entry_details(json_data[DATA][curr_pos]))

            continue

        # replacing info in selected entry
        if command == key.CTRL_E:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            print_edit_entry = print_entry_details(json_data[DATA][curr_pos])

            print_edit_entry = print_edit_entry + "\n"

            print_edit_entry += "Input new information or leave empty to keep it the same.\n"
            print_edit_entry += "Warning: Overwritten data will be lost.\n\n"

            print_edit_entry += "New fields:\n"

            prev_links = json_data[DATA][curr_pos][LINKS]

            description, incognito, links = console.separateInteraction(message=print_edit_entry, function=lambda: 
                                                        create_or_edit_entry(editing=True, prev_links=prev_links), startAtTop=True, showCursor=True)
                
            if description != "":
                json_data[DESCRIPTIONS][curr_pos] = description
                json_data[DATA][curr_pos][DESC] = description
                console.updateList(json_data[DESCRIPTIONS])
                
            if incognito != "":
                json_data[DATA][curr_pos][INCOGNITO] = incognito
                
            if json_data[DATA][curr_pos][LINKS] != links: # on edit, we only care about potentially added links for auto-upload
                console.upload = True

            json_data[DATA][curr_pos][LINKS] = links

            # at least one field was changed, updating file
            if description != "" or incognito != "" or links:
                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)

            continue


        # moves selected entry to another link list:
        if command == key.CTRL_X:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            entry = json_data[DATA][curr_pos]

            os.system(f'title Moving \'{entry[DESC]}\'')
            move_file_path, _ = json_file_loop(console, saved_pos)
            if not move_file_path or json_file_path == move_file_path:
                os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]} - Link Master')
                console.updateList(json_data[DESCRIPTIONS])
                console.updateSpecialCommands(LINK_COMMANDS_LIST)
                console.updateHelpPage(LINK_HELP_PAGE)
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

            os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]} - Link Master')

            console.updateList(json_data[DESCRIPTIONS])
            console.updateSpecialCommands(LINK_COMMANDS_LIST)
            console.updateHelpPage(LINK_HELP_PAGE)
            console.updatePos(curr_pos)

            continue

        # copies selected entry to link list
        if command == key.CTRL_C:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            entry = json_data[DATA][curr_pos]

            os.system(f'title Copying \'{entry[DESC]}\'')
            copy_file_path, _ = json_file_loop(console, saved_pos)
            if not copy_file_path:
                os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]} - Link Master')
                console.updateList(json_data[DESCRIPTIONS])
                console.updateSpecialCommands(LINK_COMMANDS_LIST)
                console.updateHelpPage(LINK_HELP_PAGE)
                console.updatePos(curr_pos)
                continue

            if json_file_path == copy_file_path:
                # adding entry to the same json file
                json_data[DATA].append(entry)
                json_data[DESCRIPTIONS].append(entry[DESC])

                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)
                
                os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]} - Link Master')

                console.updateList(json_data[DESCRIPTIONS])

                continue

            # adding entry to other json file
            copy_data = json.load(open(copy_file_path))

            copy_data[DATA].append(entry)
            copy_data[DESCRIPTIONS].append(entry[DESC])

            with open(copy_file_path, 'w', encoding='utf-8') as file:
                json.dump(copy_data, file, ensure_ascii=False, indent=4)

            os.system(f'title {json_file_path[json_file_path.rfind("/") + 1:json_file_path.rfind(".")]} - Link Master')
            
            console.updateList(json_data[DESCRIPTIONS])
            console.updateSpecialCommands(LINK_COMMANDS_LIST)
            console.updateHelpPage(LINK_HELP_PAGE)
            console.updatePos(curr_pos)

            continue

        # remove entry from link list
        if command == key.DELETE:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            remove_answer = console.separateInteraction(function=lambda: yes_or_no(f'Are you sure you want to remove \'{json_data[DESCRIPTIONS][curr_pos]}\'?\nData will be lost forever.'), showCursor=True)

            if remove_answer == "no":
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
            console.separateInteraction(function=gkeep_upload)
            
            console.upload = False # app just uploaded to google keep, so no reason to do it again
            continue


        # return to file selection
        if command == key.BACKSPACE:
            return


        # quit application
        if command == key.ESC:
            console.exitInterface()

            # uploading to google keep if changes to links haven't been uploaded
            if console.upload:
                gkeep_upload(False)
            quit()


# IMPORTANT NOTE: CTRL_H is SAME as BACKSPACE
FILE_COMMANDS_LIST = [key.ENTER, key.CTRL_N, key.CTRL_R, key.DELETE, key.CTRL_B, key.CTRL_U, key.CTRL_T, key.CTRL_K, key.BACKSPACE, key.ESC]
FILE_HELP_PAGE    = """
Link list main menu.

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
def json_file_loop(console, saved_pos=0):
    files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
    files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files

    console.updateList(files)
    console.updateSpecialCommands(FILE_COMMANDS_LIST)
    console.updateHelpPage(FILE_HELP_PAGE)
    console.updatePos(saved_pos)
    
    while (True):
        command, curr_pos = console.interact()

        # open selected link list
        if command == key.ENTER:
            return f'{JSONFOLDER}{files[curr_pos]}.json', curr_pos


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
                if os.path.exists(f'{JSONFOLDER}{filename}.json'):
                    console.separateInteraction(message="Link list with this name already exists.\n")
                    continue

                with open(f'{JSONFOLDER}{filename}.json', 'w', encoding='utf-8') as file:
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
                if os.path.exists(f'{JSONFOLDER}{filename}.json'):
                    console.separateInteraction(message="Link list with this name already exists.\n")
                    continue
                
                os.rename(f'{JSONFOLDER}{file}.json', f'{JSONFOLDER}{filename}.json')

                files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
                files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files
                    
                console.updateList(files)
                if filename in files:
                    console.updatePos(files.index(filename))
                
            except:
                console.separateInteraction(message="Illegal character used in name.\n")

            continue

        # move link list to recycle bin
        if command == key.DELETE:
            try:
                file = files[curr_pos]
                send2trash(f'{JSONFOLDER}{file}.json'.replace('/', '\\')) # this function requires backslashes
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
                console.hideFiles = (console.separateInteraction(function=lambda: yes_or_no("Show hidden lists?", default_answer="no"), showCursor=True) == "no")
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
            console.separateInteraction(function=gkeep_upload)
            continue


        # cancel move/copy
        if command == key.BACKSPACE:
            return None, curr_pos


        # quit application
        if command == key.ESC:
            console.exitInterface()
            
            # uploading to google keep if changes to links haven't been uploaded
            if console.upload:
                gkeep_upload(False)
            quit()


def main():
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print("\nConsole application for keeping track of important links.\n")

    else:
        saved_pos = 0
        console = ConsoleListInterface()
        console.hideFiles = True  # hidden files
        console.upload    = False # determines whether the app will automatically start gkeep_upload on quit (Esc) 
        while (True):
            os.system("title Link Master Menu")
            json_file_path, saved_pos = json_file_loop(console, saved_pos)
            link_list_loop(console, json_file_path, saved_pos)


if __name__ == '__main__':
    main()
