import os 

HOMEPATH = os.path.dirname(os.path.realpath(__file__))

def setup():
    if not os.path.exists(f'{HOMEPATH}/json_data'):
        os.mkdir(f'{HOMEPATH}/json_data')
        if os.path.exists(f'{HOMEPATH}/Examples.json'):
            os.rename(f'{HOMEPATH}/Examples.json', f'{HOMEPATH}/json_data/Examples.json')

    paths = []
    if os.path.exists(f'{HOMEPATH}/.paths'):
        paths  = [line.replace('\n', '') for line in open(f'{HOMEPATH}/.paths').readlines()]
    paths += [""] * (3 - len(paths)) # adding empty strings so that the following commands wont raise an error

    CONSOLE_PATH = paths[0]
    KEEP_TOKEN   = paths[1]
    KEEP_FILE    = paths[2]

    if not os.path.exists(f'{CONSOLE_PATH}/ConsoleListInterface.py'):
        CONSOLE_PATH = ""

    if not os.path.exists(KEEP_FILE):
        KEEP_FILE = ""

    if CONSOLE_PATH:
        print(f"Current saved directory for 'ConsoleListInterface.py':\n{CONSOLE_PATH}")
    print("Please type path to directory of ConsoleListInterface.py (or leave empty to ", end = '')
    if CONSOLE_PATH:
        print("keep current path): ")
    else:
        print("cancel): ")

    console_path = input()
    if console_path:
        if console_path[0] == '"':
            console_path = console_path[1:]
        if console_path[-1] == '"':
            console_path = console_path[:-1]
    
    while (console_path and not console_path.isspace() and not os.path.exists(f'{console_path}/ConsoleListInterface.py')) \
            or ('./' in console_path or '.\\' in console_path): 
        # avoiding relative paths, they might cause issues
        if ('./' in console_path or '.\\' in console_path): 
            console_path = input("Please use the absolute path:\n") 
        else: 
            console_path = input("ConsoleListInterface.py not found, please try again:\n") 
        if console_path:
            if console_path[0] == '"':
                console_path = console_path[1:]
            if console_path[-1] == '"':
                console_path = console_path[:-1]

    if not CONSOLE_PATH and not console_path:
        exit()

    print("The following is for saving Link Lists to Google Keep. \
          \nOnly the Master Token is required for this feature. \
          \nAdditional details are in README.md.\n")

    if KEEP_TOKEN:
        print(f"Current saved Google API Master Token:\n{KEEP_TOKEN}") 
    print("Please enter Google API Master Token (or leave empty to ", end = '')
    if KEEP_TOKEN:
        print("keep current token): ")
    else:
        print("skip): ")
    
    keep_token = input()

    if KEEP_FILE:
        print(f"Current saved Google Keep Cache File:\n{KEEP_FILE}") 
    print("Please enter path to cache file (or leave empty to ", end = '')
    if KEEP_FILE:
        print("keep current cache): ")
    else:
        print("skip): ")

    keep_file = input()
    if keep_file:
        if keep_file[0] == '"':
            keep_file = keep_file[1:]
        if keep_file[-1] == '"':
            keep_file = keep_file[:-1]
    
    while (keep_file and not keep_file.isspace() and not os.path.exists(keep_file)) \
            or ('./' in keep_file or '.\\' in keep_file): 
        # avoiding relative paths, they might cause issues
        if ('./' in keep_file or '.\\' in keep_file): 
            keep_file = input("Please use the absolute path:\n") 
        else: 
            keep_file = input("Keep Cache not found, please try again:\n") 
        if keep_file:
            if keep_file[0] == '"':
                keep_file = keep_file[1:]
            if keep_file[-1] == '"':
                keep_file = keep_file[:-1]

    if console_path:
        CONSOLE_PATH = console_path
    if keep_token:
        KEEP_TOKEN = keep_token
    if keep_file:
        KEEP_FILE = keep_file

    open(f'{HOMEPATH}/.paths', 'w').write(f'{CONSOLE_PATH}\n{KEEP_TOKEN}\n{KEEP_FILE}\n')


if __name__ == "__main__":
    setup()