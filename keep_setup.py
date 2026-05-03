from ConsoleListInterface import MenuInterface, waitForEnter, cls
from link_master import DATAPATH, KEEP_EMAIL, gkeep_upload
from termcolor import colored
import yaml
import sys
import os 


try:
    gpsoauth_import = True
    import gpsoauth
except:
    gpsoauth_import = False

sys.stderr = open(f'{DATAPATH}/errors.txt', "a")


FULL_EXPLANATION = """This is the setup for the optional feature of being able to save your links to Google Keep.
For this, the program needs your account's Master Token - which provides full access to your Google account, through the APIs.
Because of that, you need to be careful in handling it - just like you'd handle a password.

If you already have a Master Token, you can provide it to this setup app directly, in the second option.
If you don't, you can use an Access Token - the explanation is provided when you select the third option.

Additionally, if you use multiple programs that access your Google Keep through the gkeepapi library, you can set up a special file to be the cache for it, and you can provide its path here through the fourth option.

Important Note: this program saves your sensitive Master Token only on your computer, in the 'metadata/.paths' file.
"""

ACCESS_INSTRUCTIONS = """Follow the instructions at https://github.com/rukins/gpsoauth-java/blob/b74ebca999d0f5bd38a2eafe3c0d50be552f6385/README.md#receiving-an-authentication-token.
Then paste the Access Token here (or leave empty to cancel):
"""


def test_gkeep_upload():
    try:
        gkeep_upload(press_enter=False)
        print("Uploading to Google Keep is working.\nPress enter to continue.")
        waitForEnter()
    except Exception as e:
        print(f"\nError: '{type(e).__name__}'.")
        if type(e).__name__ == 'LoginException':
            print("Master Token authentification failed, check that it is correct or retry obtaining it with an Access Token.")
        elif type(e).__name__ == 'ModuleNotFoundError':
            print("The 'gkeepapi' library is missing.\nPlease install it with 'pip3 install gkeepapi' to be able to upload the link lists to Google Keep.")
        elif type(e).__name__ == 'FileNotFoundError' or type(e).__name__ == 'OSError' or type(e).__name__ == 'JSONDecodeError':
            print("The cache file path is broken, or it is not JSON-formatted.\nThis path will be removed, but you can change it back to an existing JSON file through the fourth setup option.")
            KEEP_TOKEN = open(f'{DATAPATH}/.paths', 'r').readline()
            open(f'{DATAPATH}/.paths', 'w').write(KEEP_TOKEN)
        else:
            print("Unknown error type.")
        print()
        input("Press enter to continue.")
        waitForEnter

# get absolute path of file/directory, whilst also checking for things are raising an error if check fails
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

def keep_menu():
    menu = MenuInterface(yaml.safe_load(open(f"{DATAPATH}/keep_menu.yaml")))

    while True:
        info_message = ""
        if os.path.exists(f"{DATAPATH}/.paths"):
            with open(f"{DATAPATH}/.paths", 'r') as file:
                lines = file.readlines()
                KEEP_TOKEN = lines[0].replace('\n', '') if lines else ""
                KEEP_PATH  = lines[1].replace('\n', '') if 2 <= len(lines) else ""

                if KEEP_TOKEN: 
                    info_message += "There is a saved Master Token in 'metadata\\.paths'.\n"
                
                if KEEP_PATH:
                    info_message += f"Current saved path for Keep Cache: {KEEP_PATH}.\n"

        menu.setTopText(colored("Manage your Keep Token and Cache file\n", "blue") + colored(info_message, "light_blue"))    
                
        path = menu.interactWithMenu()

        # ignoring backspace
        if not path:
            continue

        option = path[0]
        option = option[:option.find(' ')]

        if option == "What":
            menu.separateInteraction(message=FULL_EXPLANATION, startAtTop=True)
            continue

        if option == "Change":
            KEEP_TOKEN = menu.separateInteraction(function=lambda: input("Paste Master Token here or leave empty to cancel:\n"), showCursor=True)
            if KEEP_TOKEN and not KEEP_TOKEN.isspace():
                if os.path.exists(f"{DATAPATH}/.paths"):
                    with open(f"{DATAPATH}/.paths", 'r') as file:
                        lines = file.readlines()
                        KEEP_PATH = lines[1].replace('\n', '') if 2 <= len(lines) else ""

                else:
                    KEEP_PATH = ""
                
                with open(f"{DATAPATH}/.paths", 'w') as file:
                    file.write(f"{KEEP_TOKEN}\n{KEEP_PATH}")
                
                menu.separateInteraction(message="Master Token saved.\n")

        if option == "Use":
            if not gpsoauth_import:
                menu.separateInteraction(message="In order to obtain a Master Token from the Access Token, the gpsoauth library is needed.\n")
                continue

            while True:
                try:
                    ACCESS_TOKEN = menu.separateInteraction(function=lambda: input(ACCESS_INSTRUCTIONS), showCursor=True)
                    
                    if not ACCESS_TOKEN or ACCESS_TOKEN.isspace():
                        break

                    # clearing screen since token procurement takes a moment
                    cls()
                    master_response = gpsoauth.exchange_token(KEEP_EMAIL, ACCESS_TOKEN, '0123456789abcdef')
                    KEEP_TOKEN = master_response['Token']
                    
                    if os.path.exists(f"{DATAPATH}/.paths"):
                        with open(f"{DATAPATH}/.paths", 'r') as file:
                            lines = file.readlines()
                            KEEP_PATH = lines[1].replace('\n', '') if 2 <= len(lines) else ""

                    else:
                        KEEP_PATH = ""
                        
                    with open(f"{DATAPATH}/.paths", 'w') as file:
                        file.write(f"{KEEP_TOKEN}\n{KEEP_PATH}")
                    
                    menu.separateInteraction(message="Master Token saved.\n")
                    break
                    
                except:
                    menu.separateInteraction(message="Authentification failed, Master Token was not received.\n")

        if option == "Set":
            while True:
                KEEP_PATH = menu.separateInteraction(function=lambda: input("Paste path to Keep Cache file, or leave empty to cancel:\n"), showCursor=True)
                try:
                    KEEP_PATH = get_path(KEEP_PATH, check_file=True)
                    
                    if os.path.exists(f"{DATAPATH}/.paths"):
                        with open(f"{DATAPATH}/.paths", 'r') as file:
                            KEEP_TOKEN = file.readline().replace('\n', '')

                    else:
                        KEEP_TOKEN = ""
                    
                    with open(f"{DATAPATH}/.paths", 'w') as file:
                        file.write(f"{KEEP_TOKEN}\n{KEEP_PATH}")

                    menu.separateInteraction(message="Cache filepath saved.\n")

                    break

                except Exception as e:
                    error = str(e)

                    if error in ["empty", "space"]:
                        break
                    elif error == "not file":
                        error_message = "Path leads to a directory or another non-file system object.\n" 
                    elif error == "not exists":
                        error_message = "Path does not lead to any system object.\n"
                    else:
                        error_message = "Unknown error.\n"

                    menu.separateInteraction(message=error_message)


        if option == "Test":
            menu.separateInteraction(function=test_gkeep_upload)
            continue

        if option == "Exit":
            menu.exitInterface()
            return
        

if __name__ == "__main__":
    keep_menu()