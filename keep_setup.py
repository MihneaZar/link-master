from shared import HOMEPATH, KEEP_EMAIL, get_path, yes_or_no, gkeep_upload, waitForEnter
import os 

try:
    gpsoauth_import = True
    import gpsoauth
except:
    gpsoauth_import = False

def keep_setup(from_link_list=True):
    paths = []
    if os.path.isfile(f'{HOMEPATH}/.paths'):
        paths = [line.replace('\n', '') for line in open(f'{HOMEPATH}/.paths').readlines()]
    elif from_link_list:
        if yes_or_no("\nAre you interested in running the setup to be able to upload link lists to Google Keep?", default_answer="no") == "no":
            # opening .paths file to ignore keep setup on future runs of link_list.py
            open(f'{HOMEPATH}/.paths', 'w').close()
            return
        
    paths += [""] * (2 - len(paths)) # adding empty strings so that the following commands wont raise an error

    KEEP_TOKEN = paths[0]
    KEEP_FILE  = paths[1]

    print("\nThe following is for saving Link Lists to Google Keep. \
          \nFor this, a Master Token is required. \
          \nAdditional details are in the README.md.\n")
    
    if KEEP_TOKEN:
        print("There is a saved Master Token, but you can change it now.")
        direct_token = (yes_or_no("Do you want to change it directly?", default_answer="no") == "yes")
    else:
        direct_token = (yes_or_no("Do you already have a Master Token?", default_answer="no") == "yes")

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
        if gpsoauth_import:
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
                            print("Authentification successful, Master Token obtained.")
                            KEEP_TOKEN = master_response['Token']
                            break
                        else:
                            access_token = input("Authentification failed, try again, or leave this field empty to skip:\n")
                    except:
                        access_token = input("Authentification failed, try again, or leave this field empty to skip:\n")
                else:
                    break
        else:
            print("'gpsoauth' library missing. \
                  \nInstall library in order to obtain Google Master Token with an Access Token. \
                  \nHowever, Link Master can be used without this feature.")

    if not KEEP_TOKEN:
        print("Master Token missing.\nFinishing setup.\n")
        open(f'{HOMEPATH}/.paths', 'w').write(f'{KEEP_TOKEN}\n{KEEP_FILE}\n')
        return

    print()

    if KEEP_FILE:
        print(f"Current saved Google Keep cache file:\n{KEEP_FILE}") 
    print("Please enter path to cache file (or leave empty to ", end = '')
    if KEEP_FILE:
        print("keep current cache): ")
    else:
        print("skip): ")

    while True: 
        try:
            keep_file = get_path(input(), check_file=True)
            result    = "good path"
        except Exception as e:
            keep_file = ""
            result    = str(e) 
        finally:
            if result == "good path":
                if yes_or_no("File found.\nWarning: if this is not already a Google Keep cache, this file will be overwritten and its contents will be lost.\nAre you sure you want to use this file as a Google Keep cache?", default_answer="no") == "yes":
                    break
                print("Please enter path to cache file (or leave empty to ", end = '')
                if KEEP_FILE:
                    print("keep current cache): ")
                else:
                    print("skip): ")
            elif result in ["empty", "space"]:
                print()
                break
            elif result == "not file":
                print("That is not a file, please try again:")
            elif result == "not exists":
                print("Keep Cache not found, please try again:")

    if keep_file and not keep_file.isspace():
        KEEP_FILE = keep_file

    open(f'{HOMEPATH}/.paths', 'w').write(f'{KEEP_TOKEN}\n{KEEP_FILE}\n')

    try_upload = yes_or_no("Would you like to do a test upload (also creates the Keep Cache, which is slower on the first upload)?") == "yes"

    if try_upload:
        try:
            gkeep_upload(press_enter=False)
        except Exception as e:
            print(f"\nError: '{type(e).__name__}'.")
            if type(e).__name__ == 'LoginException':
                print("Master Token authentification failed, check that it is correct or retry obtaining it with an Access Token.")
            elif type(e).__name__ == 'ModuleNotFoundError':
                print("The 'gkeepapi' library is missing.\nPlease install it with 'pip3 install gkeepapi' to be able to upload the link lists to Google Keep.")
            elif type(e).__name__ == 'FileNotFoundError' or type(e).__name__ == 'OSError':
                print("The cache file path is broken.\nThis path will be removed, but you can change it back to an existing file by rerunning this setup.")
                open(f'{HOMEPATH}/.paths', 'w').write(f'{KEEP_TOKEN}\n\n')
            else:
                print("Unknown error type.")
            print()

        if from_link_list:
            print("Press enter to continue.")
            waitForEnter()


if __name__ == "__main__":
    keep_setup(False)