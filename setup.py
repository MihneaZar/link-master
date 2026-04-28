from shared import HOMEPATH, KEEP_EMAIL, yes_or_no, gkeep_upload
import sys
import os 

sys.stderr = open(f'{HOMEPATH}/errors.txt', "a")

CONSOLE_PATH_ERROR = "Path to ConsoleListInterface.py is broken."

def setup():
    if not os.path.exists(f'{HOMEPATH}/json_data'):
        os.mkdir(f'{HOMEPATH}/json_data')
        if os.path.exists(f'{HOMEPATH}/Examples.json'):
            os.rename(f'{HOMEPATH}/Examples.json', f'{HOMEPATH}/json_data/Examples.json')

    paths = []
    if os.path.exists(f'{HOMEPATH}/.paths'):
        paths = [line.replace('\n', '') for line in open(f'{HOMEPATH}/.paths').readlines()]
        
    paths += [""] * (3 - len(paths)) # adding empty strings so that the following commands wont raise an error

    CONSOLE_PATH = paths[0]
    KEEP_TOKEN   = paths[1]
    KEEP_FILE    = paths[2]

    if CONSOLE_PATH and not CONSOLE_PATH.isspace() and not os.path.exists(f'{CONSOLE_PATH}/ConsoleListInterface.py'):
        CONSOLE_PATH = CONSOLE_PATH_ERROR

    if CONSOLE_PATH and CONSOLE_PATH != CONSOLE_PATH_ERROR:
        print(f"Current saved directory for 'ConsoleListInterface.py':\n{CONSOLE_PATH}")
    if CONSOLE_PATH == CONSOLE_PATH_ERROR:
        print(CONSOLE_PATH)
        CONSOLE_PATH = ""
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

    if console_path: 
        CONSOLE_PATH = console_path

    if not CONSOLE_PATH:
        print("Path to ConsoleListInterface.py not provided, setup is aborted.\n")
        exit()

    print("\nThe following is for saving Link Lists to Google Keep. \
          \nFor this, a Master Token is required. \
          \nAdditional details are in README.md.\n")
    
    if KEEP_TOKEN:
        print("There is a saved Master Token, but you can change it now.")

    direct_token = (yes_or_no("Do you already have a Master Token?", default_answer="no") == "yes")
    # print()

    if direct_token:
        print("Please enter Google Master Token (or leave empty to ", end = '')
        if KEEP_TOKEN:
            print("keep current Master Token): ")
        else:
            print("cancel Google Keep setup): ")
        keep_token = input()
        
        if keep_token and not keep_token.isspace():
            KEEP_TOKEN = keep_token
    
    else:
        try:
            import gpsoauth
            print("To obtain a Google Access Token, follow the instructions at: \
                  \nhttps://github.com/rukins/gpsoauth-java/blob/b74ebca999d0f5bd38a2eafe3c0d50be552f6385/README.md#receiving-an-authentication-token. \
                  \nThen please enter Google Access Token (or leave empty to ", end = '')
            if KEEP_TOKEN:
                print("keep current Master Token): ")
            else:
                print("cancel Google Keep setup): ")
            
            access_token = input()
            while True:    
                if access_token and not access_token.isspace():
                    try:
                        master_response = gpsoauth.exchange_token(KEEP_EMAIL, access_token, '0123456789abcdef')
                        if master_response['Token']:
                            print("Authentification is successful, Master Token obtained.")
                            KEEP_TOKEN = master_response['Token']
                            break
                        else:
                            access_token = input("Authentification failed, try again, or leave this field empty to skip:\n")
                    except:
                        access_token = input("Authentification failed, try again, or leave this field empty to skip:\n")
                else:
                    break
        except:
            print("'gpsoauth' library missing. \
                  \nInstall library in order to obtain Google Master Token with an Access Token. \
                  \nHowever, Link Master can be used without this feature.")

    if not KEEP_TOKEN:
        print("Master Token missing.\nFinishing setup.\n")
        open(f'{HOMEPATH}/.paths', 'w').write(f'{CONSOLE_PATH}\n{KEEP_TOKEN}\n{KEEP_FILE}\n')
        return

    print()

    if KEEP_FILE:
        print(f"Current saved Google Keep cache file:\n{KEEP_FILE}") 
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
    
    while (keep_file and not keep_file.isspace() and (not os.path.exists(keep_file) or os.path.isdir(keep_file))) \
            or ('./' in keep_file or '.\\' in keep_file): 
        # avoiding relative paths, they might cause issues
        if ('./' in keep_file or '.\\' in keep_file): 
            keep_file = input("Please use the absolute path:\n") 
        elif os.path.isdir(keep_file):
            keep_file = input("That is directory, not a file:\n") 
        else: 
            keep_file = input("Keep Cache not found, please try again:\n") 
        if keep_file:
            if keep_file[0] == '"':
                keep_file = keep_file[1:]
            if keep_file[-1] == '"':
                keep_file = keep_file[:-1]

    if keep_file:
        KEEP_FILE = keep_file

    open(f'{HOMEPATH}/.paths', 'w').write(f'{CONSOLE_PATH}\n{KEEP_TOKEN}\n{KEEP_FILE}\n')

    print()
    try_upload = yes_or_no("Would you like to DO a test upload (also creates the Keep Cache, which is slower on the first upload)?") == "yes"

    if try_upload:
        try:
            gkeep_upload(press_enter=False)
        except Exception as e:
            print(f"\nError: '{type(e).__name__}'.")
            if type(e).__name__ == 'LoginException':
                print("Master Token authentification failed, check that the token is correct or retry obtaining it with an Access Token.")
            elif type(e).__name__ == 'ModuleNotFoundError':
                print("The 'gkeepapi' library is missing.\nPlease install it with 'pip3 install gkeepapi' to be able to upload the link lists to Google Keep.")
            elif type(e).__name__ == 'FileNotFoundError' or type(e).__name__ == 'OSError':
                print("The cache file path is broken.\nThis path will be removed, but you can change it back to an existing file by rerunning this setup.")
                open(f'{HOMEPATH}/.paths', 'w').write(f'{CONSOLE_PATH}\n{KEEP_TOKEN}\n\n')
            else:
                print("Unknown error type.")
            print()


if __name__ == "__main__":
    setup()