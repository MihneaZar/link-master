from ConsoleListInterface.Interface import waitForEnter 
from readchar import readkey, key
from functools import reduce
import json
import sys
import os

HOMEPATH = os.path.dirname(os.path.realpath(__file__)) 

sys.stderr = open(f'{HOMEPATH}/errors.txt', "a")

JSONFOLDER = f'{HOMEPATH}/json_data/'

FILENAME     = "Filename"
DATA         = "Data"
DESCRIPTIONS = "Description List"
DESC         = "Description"
INCOGNITO    = "Incognito"
LINKS        = "Links"

KEEP_EMAIL = ""


def get_path(path, must_exist=True, check_dir=False, check_file=False, replace_quotes=True):
    if path == "":
        raise ValueError("empty")
    
    if path.isspace():
        raise ValueError("space")
    
    realpath = os.path.realpath(path)
    
    if must_exist and not os.path.exists(realpath):
        raise ValueError("not exists")
    
    if check_dir and not os.path.isdir(realpath):
        raise ValueError("not dir")
    
    if check_file and not os.path.isfile(realpath):
        raise ValueError("not file")

    if replace_quotes:
        realpath = realpath.replace('\"', '')
        realpath = realpath.replace('\'', '')
    
    return realpath


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
                if newline:
                    print()
                return ""
            else:
                print(default_answer.capitalize())
                if newline:
                    print()
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
    paths = [line.replace('\n', '') for line in open(f'{HOMEPATH}/.paths').readlines()]
    paths += [""] * (2 - len(paths)) # adding empty strings so that the following commands wont raise an error

    KEEP_TOKEN = paths[0]
    KEEP_FILE  = paths[1] if paths[1] else f'{HOMEPATH}/.keep.json'

    import gkeepapi

    print("Starting Google Keep upload...")

    keep = gkeepapi.Keep()

    print("Downloading newest versions of notes...")
    if os.path.isfile(KEEP_FILE):
        keep.authenticate(KEEP_EMAIL, KEEP_TOKEN, state=json.load(open(KEEP_FILE)))
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

