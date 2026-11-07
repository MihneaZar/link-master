from ConsoleListInterface import ConsoleListInterface, MenuInterface, autocomplete
from send2trash import send2trash
from readchar import readkey, key
from termcolor import colored
from time import sleep
import subprocess
import requests
import shutil
import json
import yaml
import sys
import os
import re

try:
    gkeepapi_imported = True
    import gkeepapi
except:
    gkeepapi_imported = False

HOMEPATH   = os.path.dirname(os.path.realpath(__file__)) 
DATAPATH   = f"{HOMEPATH}/data"
JSONFOLDER = f"{HOMEPATH}/json_data"

sys.stderr = open(f'{DATAPATH}/errors.txt', "a")

FILENAME     = "Filename"
DATA         = "Data"
DESCRIPTIONS = "Description List"
DESC         = "Description"
INCOGNITO    = "Incognito"
LINKS        = "Links"

KEEP_EMAIL = ""


# for custom input in the link, such as show season and episode
LINK_INPUT_START    = '{'
LINK_INPUT_END      = '}'
LINK_VALIDATE_START = '<'
LINK_VALIDATE_END   = '>'

# these look horrible, i know
# also i didnt use the constants above as it would have looked that much worse 
VAR_RE  = "^\\{[^{}<>]*(<[^{}<>]*>)?\\}$"
LINK_RE = "^[^{}]*(\\{[^{}<>]*(<[^{}<>]*>)?\\}[^{}]*)*$"

YES = "Yes"
NO  = "No"

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

    
def gkeep_upload():
    if not gkeepapi_imported:
        raise ModuleNotFoundError

    paths = [line.replace('\n', '') for line in open(f'{DATAPATH}/.paths', encoding='utf-8').readlines()]
    paths += [""] * (2 - len(paths)) # adding empty strings so that the following commands wont raise an error PUHLEASE

    KEEP_TOKEN = paths[0]
    KEEP_PATH  = paths[1] if paths[1] else f'{DATAPATH}/.keep.json'

    if not KEEP_TOKEN or KEEP_TOKEN.isspace():
        raise gkeepapi.exception.LoginException

    print(colored("Starting Google Keep upload...", "light_blue"))

    keep = gkeepapi.Keep()

    print(colored("Downloading newest versions of notes...", "light_blue"))
    if os.path.isfile(KEEP_PATH):
        try: 
            keep.authenticate(KEEP_EMAIL, KEEP_TOKEN, state=json.load(open(KEEP_PATH, encoding='utf-8')))
        except gkeepapi.exception.ResyncRequiredException:
            keep.sync(resync=True)
            keep.authenticate(KEEP_EMAIL, KEEP_TOKEN)
    else:
        keep.authenticate(KEEP_EMAIL, KEEP_TOKEN)

    label = keep.findLabel('Link Master')
    if not label:
        label = keep.createLabel('Link Master')

    print(colored("Deleting previous notes in label 'Link Master'...", "light_blue"))
    for note in keep.find(labels=[keep.findLabel('Link Master')]):
        note.delete()

    print(colored("Adding new notes locally...", "light_blue"))

    # warning note for the 'Link Master' label, since all notes in label get deleted on upload
    note = keep.createNote("DO NOT ADD THIS LABEL", "All notes with this label are deleted on upload from Link Master app.")
    note.labels.add(label)
    for json_file in os.listdir(JSONFOLDER):
        link_data = json.load(open(f'{JSONFOLDER}/{json_file}', encoding='utf-8'))

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


    print(colored("Uploading new notes...", "light_blue"))
    keep.sync()

    print(colored("Saving newest Google Keep state (for faster uploads in the future)...", "light_blue"))

    # Store Keep cache
    with open(KEEP_PATH, 'w', encoding='utf-8') as file:
        json.dump(keep.dump(), file)

    print(colored("Upload complete.\n", "light_blue"))


def print_entry_details(entry, removed_links=[]):
    print_entry  = f'{colored("Description", "light_blue")}: {entry[DESC]}\n'
    print_entry += f'{colored("Open in incognito mode", "light_blue")}: {entry[INCOGNITO]}\n'
    print_entry += f'{colored("Links", "light_blue")}:'
    
    for pos in range(len(entry[LINKS])):
        # extra space for links 1-9 if there are 10 links or more (so that all links are aligned)
        padding = ' ' if pos <= 8 and 10 <= len(entry[LINKS]) else ''
        name = entry[LINKS][pos]
        print_entry += f'\n{colored(str(pos + 1) + ". " + padding, "light_blue")}'
        if (pos + 1) in removed_links:
            print_entry += f'{colored("(set to be removed) ", "light_blue")}'
            index_length = len("xx. (set to be removed) ")
        else:
            index_length = len("xx. ")

        if shutil.get_terminal_size()[0] < index_length + len(name) - 1:
            name = name[:shutil.get_terminal_size()[0] - index_length - 2] + '-'

        print_entry += name

    if not entry[LINKS]:
        print_entry += "\n(None)"

    return print_entry


def get_links():
    links = []
    print(f"{colored('Links', 'light_blue')} (type '?' for custom commands info):")

    check_var  = re.compile(VAR_RE)
    check_link = re.compile(LINK_RE)
    
    while True:

        curr_link = input()
        if curr_link == "" or curr_link.isspace():
            break

        if curr_link == '?':
            print(f"For custom input, use the format '{LINK_INPUT_START}input_prompt{LINK_INPUT_END}' within the link (the text will be prompted on every link open).")
            print(f"For custom input to be reused, add variable as 'var var_name={LINK_INPUT_START}input_prompt{LINK_INPUT_END}'. Spaces are not allowed in var_name.")
            print(f"The prompt will be provided only once for every variable, and '{LINK_INPUT_START}var_name{LINK_INPUT_END}' from links will be replaced by its value.")
            print(f"Additionally, add {LINK_VALIDATE_START}option1|option2|...{LINK_VALIDATE_END} after prompt to validate input. Options can be:")
            print("    - 'x-y', which accepts any integer value between x an y;")
            print("    - case-sensitive text without spaces.")
                
            continue


        if curr_link.startswith("var "): 
            # checking that var has an input prompt and that it matches the variable regex
            if LINK_INPUT_START not in curr_link or not check_var.fullmatch(curr_link[curr_link.find(LINK_INPUT_START):]):
                print("Variable format is wrong, entry ignored.")
                continue

        else:
            # checking that link matches regex
            if not check_link.fullmatch(curr_link):
                print("Custom input format is wrong, entry ignored.")
                continue

        links.append(curr_link)

    return links

# if the entry exists, it will accept empty description
# otherwise it will cancel when it is empty
def create_entry():
    description = input(f'{colored("Description", "light_blue")}: ')

    # if the description is empty, cancels adding this entry
    if (not description or description.isspace()):
        return None, None, None

    incognito = yes_or_no(colored("Open in incognito mode", "light_blue"), default_answer=NO, newline=False)

    links = get_links()

    return description, incognito, links


def edit_entry(entry):
    menu_structure = yaml.safe_load(open(f"{DATAPATH}/link_list_edit.yaml"))
    menu_structure["Edit"]["Remove links"] = {f'{i}.': None for i in range(1, len(entry[LINKS]) + 1)}
    
    menu = MenuInterface(menu_structure, submenuColor="light_blue", optionColor="light_blue", supressColorWarning=True, 
                         dontPrintMenu=True, columnNo=shutil.get_terminal_size()[0] // 23) # 23 is the minimum column width so that the column don't overwrite each other

    description   = None
    incognito     = None
    added_links   = []
    removed_links = [] # they will be saved by the index

    while True:
        menu.changeMainMenuTitle(print_entry_details({DESC: description if description else entry[DESC], INCOGNITO: incognito if incognito else entry[INCOGNITO], LINKS: entry[LINKS] + added_links}, removed_links))
        path = menu.interactWithMenu()
        
        # backspace from 'Remove links' option
        if not path:
            menu.updatePos(4) # forcing position back where it's supposed to be, unclear why it backspaces to 'Cancel changes' 
            continue

        option = path[-1]
        option = option[:option.find(' ')] if ' ' in option else option

        if option == "Save":
            changed = (description or incognito or added_links or removed_links)
            if not changed or menu.separateInteraction(function=lambda: yes_or_no(colored("Are you sure you want to save changes?", "light_blue"), NO)) == YES:
                all_links = entry[LINKS] + added_links
                return description, incognito, [all_links[pos] for pos in range(len(all_links)) if (pos + 1) not in removed_links] 
            
            continue


        if option == "Change":
            new_description = menu.separateInteraction(function=lambda: autocomplete([entry[DESC], description], f'{colored("New description", "light_blue")}: ', exitOnEsc=True), showCursor=True)
            if new_description and not new_description.isspace() and new_description != entry[DESC]: # ignoring unchanged description
                description = new_description
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

        if option == "Remove" and (entry[LINKS] + added_links): 
            menu.setTopText(print_entry_details({DESC: description if description else entry[DESC], INCOGNITO: incognito if incognito else entry[INCOGNITO], LINKS: entry[LINKS] + added_links}, removed_links) \
                            + f'\n\n{colored("Set links to be removed:", "light_blue")}\n')
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
                            + f'\n\n{colored("Set links to be removed:", "light_blue")}\n')
            continue


        # backspace and esc are treated as choosing the 'Cancel changes' option
        if option in ["Cancel", key.ESC, key.BACKSPACE]: 
            changed = (description or incognito or added_links or removed_links)
            if not changed or menu.separateInteraction(function=lambda: yes_or_no(colored("Are you sure you want to cancel changes?", "light_blue"), NO)) == YES:
                return None, None, entry[LINKS]


def parse_link(link, vars):
    if LINK_INPUT_START in link:
        while LINK_INPUT_START in link:
            pos = link.find(LINK_INPUT_START) + len(LINK_INPUT_START)
            if link[pos:link.find(LINK_INPUT_END)] in vars:
                value = vars[link[pos:link.find(LINK_INPUT_END)]]
            else:
                if LINK_VALIDATE_START in link:
                    link_prompt = link[pos:link.find(LINK_VALIDATE_START)]
                    validate_string = link[link.find(LINK_VALIDATE_START) + 1:link.find(LINK_VALIDATE_END)]
                    validation = []
                    for group in validate_string.split('|'):
                        if '-' in group and group[:group.find('-')].isdigit() and group[group.find('-') + 1:].isdigit():
                            validation += [str(no) for no in range(int(group[:group.find('-')]), int(group[group.find('-') + 1:]) + 1)]
                        else:
                            validation += [group]
                    value = autocomplete(validation, f'{link_prompt}: ' if link_prompt else '')
                    if value not in validation:
                        return None
                else:
                    link_prompt = link[pos:link.find(LINK_INPUT_END)]
                    value = input(f'{link_prompt}: ' if link_prompt else '')

            if value is None or value.isspace():
                return None

            link = link[:link.find(LINK_INPUT_START)] + value + link[link.find(LINK_INPUT_END)+len(LINK_INPUT_END):]
    
    return link

                                                                               # overwriting internal rename command
LINK_COMMANDS_LIST = [key.ENTER, key.CTRL_O, key.CTRL_N, key.CTRL_D, key.CTRL_E, key.CTRL_R, key.CTRL_X, key.CTRL_C, key.DELETE, 
                      key.CTRL_K, key.BACKSPACE, key.CTRL_U, '?', key.ESC]

def link_list_loop(console: ConsoleListInterface, json_file_path, saved_pos):
    if not json_file_path:
        return
    
    console.setTopText(f"{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}\n")
    
    json_data = json.load(open(json_file_path, encoding="utf-8"))

    console.configure(specialCommands=LINK_COMMANDS_LIST, topTextColor="light_blue", itemColor="cyan", helpSearchColor="light_blue")
    console.updateList(json_data[DESCRIPTIONS])
    console.updatePos(0)

    while (True):
        command, curr_pos = console.interact()

        # open links from selected list
        if command == key.ENTER:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message=colored("Link list is empty.\n", "light_blue"))
                continue

            entry  = json_data[DATA][curr_pos]
            answer = entry[INCOGNITO]

            chrome_arg = "" if answer == NO else "-incognito"

            # resolving link variables
            vars = {}
            for var in entry[LINKS]:
                if var.startswith("var "):
                    var_name   = var[len("var "):var.find('=')].replace(' ', '')
                    if LINK_VALIDATE_START in var:
                        var_prompt = var[var.find(LINK_INPUT_START)+len(LINK_INPUT_START):var.find(LINK_VALIDATE_START)]
                        validate_string = var[var.find(LINK_VALIDATE_START) + 1:var.find(LINK_VALIDATE_END)]
                        validation = []
                        for group in validate_string.split('|'):
                            if '-' in group and group[:group.find('-')].isdigit() and group[group.find('-') + 1:].isdigit():
                                validation += [str(no) for no in range(int(group[:group.find('-')]), int(group[group.find('-') + 1:]) + 1)]
                            else:
                                validation += [group]
                                vars[var_name] = console.separateInteraction(function=lambda: autocomplete(validation, f'{var_prompt}: ' if var_prompt else ''), showCursor=True)
                    else:
                        var_prompt = var[var.find(LINK_INPUT_START)+len(LINK_INPUT_START):var.find(LINK_INPUT_END)]
                        vars[var_name] = console.separateInteraction(function=lambda: input(f'{var_prompt}: ' if var_prompt else ''), showCursor=True)
            
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
                sleep(0.1) # wait a moment between links to avoid potential ip ban or sth from google
            
            continue

        # download webpage info to file
        if command == key.CTRL_O:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message="Link list is empty.\n")
                continue

            entry  = json_data[DATA][curr_pos]
            
            # resolving link variables
            vars = {}
            for var in entry[LINKS]:
                if var.startswith("var "):
                    var_name   = var[len("var "):var.find('=')].replace(' ', '')
                    if LINK_VALIDATE_START in var:
                        var_prompt = var[var.find(LINK_INPUT_START)+len(LINK_INPUT_START):var.find(LINK_VALIDATE_START)]
                        validate_string = var[var.find(LINK_VALIDATE_START) + 1:var.find(LINK_VALIDATE_END)]
                        validation = []
                        for group in validate_string.split('|'):
                            if '-' in group and group[:group.find('-')].isdigit() and group[group.find('-') + 1:].isdigit():
                                validation += [str(no) for no in range(int(group[:group.find('-')]), int(group[group.find('-') + 1:]) + 1)]
                            else:
                                validation += [group]
                                vars[var_name] = console.separateInteraction(function=lambda: autocomplete(validation, f'{var_prompt}: ' if var_prompt else ''), showCursor=True)
                    else:
                        var_prompt = var[var.find(LINK_INPUT_START)+len(LINK_INPUT_START):var.find(LINK_INPUT_END)]
                        vars[var_name] = console.separateInteraction(function=lambda: input(f'{var_prompt}: ' if var_prompt else ''), showCursor=True)
                
            open_links = []
            for link in entry[LINKS]:
                # ignoring vars 
                if link.startswith("var "):
                    continue

                link = console.separateInteraction(function=lambda: parse_link(link, vars), showCursor=True)

                # link is None if custom input was cancelled or it was invalidated
                if link:
                    open_links.append(link)

            for link in open_links:
                response = console.separateInteraction(message=colored("Downloading response...", "light_blue"), function=lambda: requests.get(link))

                save_dir = console.separateInteraction(function=lambda: input(f"{colored('Saving response from', 'light_blue')} {link}.\n{colored('Full path to save response at:', 'light_blue')} "), showCursor=True)
                while (save_dir and not save_dir.isspace()) and (not os.path.isabs(save_dir) or not os.path.isdir(save_dir)):
                    save_dir = console.separateInteraction(function=lambda: input(f"{colored('Saving response from', 'light_blue')} {link}.\n{colored('Directory not found, try again (leave empty to skip):', 'light_blue')} "), showCursor=True)

                if not save_dir or save_dir.isspace():
                    continue

                save_file = console.separateInteraction(function=lambda: input(f"{colored('Saving response from', 'light_blue')} {link}.\n{colored('Name of file (without extension) - it WILL overwrite:', 'light_blue')} "), showCursor=True)
                saved = False
                while not saved and (save_file and not save_file.isspace()):
                    try:
                        with open(f'{save_dir}/{save_file}.txt', 'w', encoding='utf-8') as file:
                            # save_dict = {"Link": link, "Headers": response.headers, "Content": f'"""{response.text}"""'}
                            # print(save_dict)
                            # json.dump(save_dict, file, ensure_ascii=False, indent=4)
                            file.write(f'Link:\n{link}\n\n')
                            file.write(f'Headers:\n{response.headers}\n\n')
                            file.write(f'Website content:\n{response.text}')
                            saved = True
                    except Exception as e:
                        save_file = console.separateInteraction(function=lambda: input(f"{colored('Saving response from', 'light_blue')} {link}.\n{colored('Illegal character in filename, try again (leave empty to skip):', 'light_blue')} "), showCursor=True)
            
            continue


        # creating new entry
        if command == key.CTRL_N:
            description, incognito, links = console.separateInteraction(message=f'{colored("Add new entry:", "light_blue")}', function=create_entry, showCursor=True)
            
            if not description:
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
                console.separateInteraction(message=colored("Link list is empty.\n", "light_blue"))
                continue

            console.separateInteraction(message=f'{print_entry_details(json_data[DATA][curr_pos])}\n')

            continue

        # replacing info in selected entry
        if command == key.CTRL_E:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message=colored("Link list is empty.\n", "light_blue"))
                continue

            description, incognito, links = console.separateInteraction(function=lambda: edit_entry(json_data[DATA][curr_pos]))
                
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
                console.separateInteraction(message=colored("Link list is empty.\n", "light_blue"))
                continue

            entry = json_data[DATA][curr_pos]

            console.setTopText(f"Moving '{entry[DESC]}'\n")
            move_file_path, _ = json_file_loop(console, saved_pos)
            if not move_file_path or json_file_path == move_file_path:
                console.configure(specialCommands=LINK_COMMANDS_LIST, topTextColor="light_blue", itemColor="cyan", helpSearchColor="light_blue")
                console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")
                console.updateList(json_data[DESCRIPTIONS])
                console.updatePos(curr_pos)
                continue

            # adding entry to other json file
            move_data = json.load(open(move_file_path, encoding='utf-8'))

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

            console.configure(specialCommands=LINK_COMMANDS_LIST, topTextColor="light_blue", itemColor="cyan", helpSearchColor="light_blue")
            console.updateList(json_data[DESCRIPTIONS])
            console.updatePos(curr_pos)

            continue

        # copies selected entry to link list
        if command == key.CTRL_C:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message=colored("Link list is empty.\n", "light_blue"))
                continue

            entry = json_data[DATA][curr_pos]

            console.setTopText(f"Copying '{entry[DESC]}'\n")

            copy_file_path, _ = json_file_loop(console, saved_pos)
            if not copy_file_path:
                console.configure(specialCommands=LINK_COMMANDS_LIST, topTextColor="light_blue", itemColor="cyan", helpSearchColor="light_blue")
                console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")
                console.updateList(json_data[DESCRIPTIONS])
                console.updatePos(curr_pos)
                continue

            if json_file_path == copy_file_path:
                # adding entry to the same json file
                json_data[DATA].append(entry)
                json_data[DESCRIPTIONS].append(entry[DESC])

                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)
                
                console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")

                console.updateList(json_data[DESCRIPTIONS])

                continue

            # adding entry to other json file
            copy_data = json.load(open(copy_file_path, encoding='utf-8'))

            copy_data[DATA].append(entry)
            copy_data[DESCRIPTIONS].append(entry[DESC])

            with open(copy_file_path, 'w', encoding='utf-8') as file:
                json.dump(copy_data, file, ensure_ascii=False, indent=4)

            console.setTopText(f"'{json_file_path[json_file_path.rfind('/') + 1:json_file_path.rfind('.')]}'\n")

            console.configure(specialCommands=LINK_COMMANDS_LIST, topTextColor="light_blue", itemColor="cyan", helpSearchColor="light_blue")
            console.updateList(json_data[DESCRIPTIONS])
            console.updatePos(curr_pos)

            continue

        # remove entry from link list
        if command == key.DELETE:
            if not json_data[DESCRIPTIONS]:
                console.separateInteraction(message=colored("Link list is empty.\n", "light_blue"))
                continue

            remove_answer = console.separateInteraction(function=lambda: yes_or_no(f"{colored('Are you sure you want to remove', 'light_blue')} {json_data[DESCRIPTIONS][curr_pos]}{colored('?', 'light_blue')}\n{colored('Data will be lost forever.', 'light_blue')}", default_answer=NO), showCursor=True)

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
                error_message = colored("Error encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.", "light_blue")
                console.separateInteraction(message=f"{str(e)}\n{error_message}\n")
            
            console.upload = False # either the upload succeeded, so no need to upload again, or it failed, and it will fail again
            continue


        # return to file selection
        if command == key.BACKSPACE:
            return


        # update list if it was changed outside current instance
        if command == key.CTRL_U:
            json_data = json.load(open(json_file_path, encoding='utf-8'))
            console.updateList(json_data[DESCRIPTIONS])

        # help menu
        if command == '?':
            console.separateInteraction(function=lambda: MenuInterface.helpMenu(yaml.safe_load(open(f"{DATAPATH}/link_list_help_menu.yaml")), 'light_blue', 'cyan'))

        # quit application
        if command == key.ESC:
            console.exitInterface()

            # uploading to google keep if changes to links haven't been uploaded
            if console.upload:
                try:
                    gkeep_upload()
                except Exception as e:
                    # console.separateInteraction(message=f"{str(e)}\nError encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.\n")
                    pass
            quit()


# IMPORTANT NOTE: CTRL_H is SAME as BACKSPACE
FILE_COMMANDS_LIST = [key.ENTER, key.CTRL_N, key.CTRL_R, key.DELETE, key.CTRL_B, key.CTRL_U, key.CTRL_T, key.CTRL_K, key.BACKSPACE, '?', key.ESC]

# returns selected json file
def json_file_loop(console: ConsoleListInterface, saved_pos=0):
    files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
    files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files

    console.configure(specialCommands=FILE_COMMANDS_LIST, topTextColor="blue", itemColor="light_blue", helpSearchColor="blue")
    console.updateList(files)
    console.updatePos(saved_pos)
    
    while (True):
        command, curr_pos = console.interact()

        # open selected link list
        if command == key.ENTER:
            return f'{JSONFOLDER}/{files[curr_pos]}.json', curr_pos


        # creating new link list
        if command == key.CTRL_N:
            filename = console.separateInteraction(function=lambda: input(f'{colored("Type name for new link list:", "blue")}\n'), showCursor=True)
            
            try:
                # ignoring command if filename is empty
                if not filename or filename.isspace():
                    continue
                
                if '/' in filename or '\\' in filename:
                    console.separateInteraction(message=colored("Illegal character used in name.\n", "blue"))
                    continue

                # ignoring command if file already exists
                if os.path.isfile(f'{JSONFOLDER}/{filename}.json'):
                    console.separateInteraction(message=colored("Link list with this name already exists.\n", "blue"))
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
                console.separateInteraction(message=colored("Illegal character used in name.\n", "blue"))

            continue

        # rename link list
        if command == key.CTRL_R:
            file = files[curr_pos]
            filename = console.separateInteraction(function=lambda: autocomplete([file], f'{colored("Rename", "blue")} {colored(file, "light_blue")} {colored("to:", "blue")}\n', exitOnEsc=True), showCursor=True)

            try:
                # ignoring command if filename is empty
                if not filename or filename.isspace():
                    continue

                if '/' in filename or '\\' in filename:
                    console.separateInteraction(message=colored("Illegal character used in name.\n", "blue"))
                    continue

                # ignoring command if file already exists
                if os.path.isfile(f'{JSONFOLDER}/{filename}.json'):
                    console.separateInteraction(message=colored("Link list with this name already exists.\n", "blue"))
                    continue
                
                os.rename(f'{JSONFOLDER}/{file}.json', f'{JSONFOLDER}/{filename}.json')

                # updating filename in json file
                json_data = json.load(open(f'{JSONFOLDER}/{filename}.json', encoding='utf-8'))
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

        # toggle hidden lists
        if command == key.CTRL_T:
            if console.hideFiles:
                console.hideFiles = (console.separateInteraction(function=lambda: yes_or_no(colored("Show hidden lists?", "light_blue"), default_answer=NO), showCursor=True) == NO)
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
                error_message = colored("Error encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.", "light_blue")
                console.separateInteraction(message=f"{str(e)}\n{error_message}\n")
            
            console.upload = False # either the upload succeeded, so no need to upload again, or it failed, and it will fail again
            continue


        # cancel move/copy
        if command == key.BACKSPACE:
            return None, curr_pos


        # help menu
        if command == '?':
            console.separateInteraction(function=lambda: MenuInterface.helpMenu(yaml.safe_load(open(f"{DATAPATH}/link_master_help_menu.yaml"))))

        # quit application
        if command == key.ESC:
            console.exitInterface()
            
            # uploading to google keep if changes to links haven't been uploaded
            if console.upload:
                try:
                    gkeep_upload()
                except Exception as e:
                    # console.separateInteraction(message=f"{str(e)}\nError encountered during Google Keep upload.\nPlease rerun setup with 'python3 setup.py' to see what the problem is.\n")
                    pass
            quit()


def main():
    # command-line help
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
        print("\nConsole application for keeping track of important links.\nRun it as 'python3 link_master.py {link_list}' to open a link list directly from the command line.\n")
        return

    saved_pos = 0
    console = ConsoleListInterface(dontPrintList=True)
    console.hideFiles = True  # hidden files
    console.upload    = False # determines whether the app will automatically start gkeep_upload on quit (Esc) 
    console.setTitle("Link Master")

    # opening link list directly from the command line
    if 2 <= len(sys.argv):
        link_list = " ".join(sys.argv[1:])
        if os.path.isfile(f'{JSONFOLDER}/{link_list}.json'):
            # if it's a hidden link list, hideFiles must be set to False (otherwise it exists in the directory but not in the files list)
            if link_list.startswith('.'):
                console.hideFiles = False
            # the list vector is needed to establish position of link list
            files = sorted([file[:file.rfind('.')] for file in os.listdir(JSONFOLDER) if 'zip' not in file])
            files = list(filter(lambda file: file[0] != '.', files)) if console.hideFiles else files
            saved_pos = files.index(link_list)
            link_list_loop(console, f'{JSONFOLDER}/{link_list}.json', saved_pos)
    
    while (True):
        console.setTopText("Link Lists\n")
        json_file_path = None
        while not json_file_path:
            json_file_path, saved_pos = json_file_loop(console, saved_pos)
        link_list_loop(console, json_file_path, saved_pos)


if __name__ == '__main__':
    main()
