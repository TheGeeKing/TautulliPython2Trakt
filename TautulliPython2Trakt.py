import json
import os
import subprocess
import sys
import time

import requests
from dotenv import load_dotenv, set_key
from plexapi.myplex import MyPlexAccount

from utilities import ProgressBar, get_from_env, log

args = sys.argv[1:]

if not args:
    print("No arguments given! Use -h for help.")
    sys.exit(1)
log(f"initial startup args:\n{args}\n")

if args[0] == "-h":
    print(
        """
# <- not yet implemented
-h                  Help
-setup              Setup aplication
-reset              Reset settings and revoke token
-refreshToken       Refreshes the Trakt token
-add                Add a new Plex user
-remove             Remove a Plex user

------------------ Trakt Scrobbling ------------------
-m                  Media type (movie, show, episode)
-a                  Action (start, pause, stop)
-s                  Name of the TV Series
-M                  Name of the Moviename
-y                  Year of the movie/TV Show
-S                  Season number
-E                  Episode number
-t                  TVDB ID
-i                  IMDB ID
-r                  ratingKey (Plex Server internal content id)
-P                  Percentage progress (Ex: 10.0)
-PlexUser           The Plex username

------------------ Trakt Collection ------------------
-c                  Media type (movies, episodes)
-PlexUser           The Plex username (check 'Syncing behavior' in section 'More info' in the README.md file)
#-A                  Collection action (add, remove)

          """
    )
    sys.exit(0)


def _add_user_env(user):
    if not load_dotenv():
        with open(".env", "w", encoding="utf-8") as f:
            f.write("DATA='{}'")
    load_dotenv()
    data = json.loads(get_from_env("DATA"))
    data.update(user)
    set_key(".env", "DATA", json.dumps(data))


def _setup_user_process():
    plex_user = input("Enter the Plex username: ")
    trakt_client_id = input("Enter Trakt.tv 'Client ID': ")
    trakt_client_secret = input("Enter Trakt.tv 'Client Secret': ")
    if not all([plex_user, trakt_client_id, trakt_client_secret]):  # if empty
        print("One or more fields are empty!")
        sys.exit(1)

    req = requests.post(
        "https://api.trakt.tv/oauth/device/code", data={"client_id": trakt_client_id}
    )
    print(
        req.json()
    )  # {'device_code': '6764ad68383eca00b3e3a960b0cf02dcbc055dab2452f8dd583e786683578e9c', 'user_code': 'FB222899', 'verification_url': 'https://trakt.tv/activate', 'expires_in': 600, 'interval': 5}

    device_code = req.json()["device_code"]
    user_code = req.json()["user_code"]
    expires_in = req.json()["expires_in"]

    print(
        f"""
Autorize the aplication.
1. Open the URL https://trakt.tv/activate
2. Copy the temp code {user_code} (Note it is already in the windows clipboard)
3. Accept Web prompts.

This Screen will auto refresh untill the token is accepted.
There are {expires_in} seconds untill the code {user_code} expires.
"""
    )
    os.system(f"start {req.json()['verification_url']}")
    os.system(f"echo {user_code}| clip")

    status_code = 0
    progress_bar = ProgressBar("Granting access")
    progress_bar.start()
    while status_code != 200 and status_code != 409 and expires_in > 0:
        time.sleep(5)
        expires_in -= 5
        body = {
            "code": device_code,
            "client_id": trakt_client_id,
            "client_secret": trakt_client_secret,
        }
        req = requests.post(
            "https://api.trakt.tv/oauth/device/token", data=body
        )  # {'access_token': 'xxx', 'token_type': 'bearer', 'expires_in': 7776000, 'refresh_token': 'xxx', 'scope': 'public', 'created_at': 1690327181}
        status_code = req.status_code

        expires_in -= 5
        progress_bar.update((600 - expires_in) / 600 * 100)
    progress_bar.end()

    user = {
        plex_user: {"client_id": trakt_client_id, "client_secret": trakt_client_secret}
    }
    for key, value in req.json().items():
        user[plex_user][key] = value

    # set_key(".env", "DATA", json.dumps(user))
    return user


def setup_plex():
    if not load_dotenv():
        print("Try to run -setup first!")
        sys.exit(1)
    # print("This part assume that the Plex Media Server is running on the same machine as this script for now.")
    print("Recommended to run Plex Media Server on same machine as this script.")
    print(
        """
Next step you have 2 choices:
1. If your Plex Media Server is running on the same machine as this script, you can use local login with plex url and token.
2. If your Plex Media Server is running on a different machine or you want to use remote login, you will need to provide username and password. The script will then generate a token for you and store it in the .env file. Your username and password will not be stored. You can check the ".env" file after or read the code.

case 1 is recommended if you are running the script on the same machine as the Plex Media Server or you have some IT knowledges.
case 2 is recommended if you are running the script on a different machine than the Plex Media Server or you don't have any IT knowledges and have your credentials with you.
"""
    )
    choice = int(input("Enter your choice (1/2): "))
    if choice == 1:
        PLEX_BASEURL = input("Enter Plex Base URL (default: http://localhost:32400): ")
        PLEX_TOKEN = input(
            "Enter Plex Token (https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/): "
        )
    elif choice == 2:
        PLEX_USERNAME = input("Enter your Plex Username: ")
        PLEX_PASSWORD = input(
            "Enter your Plex Password (if 2fa is enabled add the code at the end e.g. password123456): "
        )
        PLEX_BASEURL = input(
            "Enter the Plex Media Server name (name on the top left when view more): "
        )
        if PLEX_USERNAME and PLEX_PASSWORD:
            account = MyPlexAccount(PLEX_USERNAME, PLEX_PASSWORD)
            PLEX_TOKEN = account.authenticationToken
        else:
            print("Invalid credentials!")
            sys.exit(1)
    else:
        print("Invalid choice!")
        sys.exit(1)

    set_key(".env", "PLEX_BASEURL", PLEX_BASEURL or "http://localhost:32400")
    set_key(".env", "PLEX_TOKEN", PLEX_TOKEN)
    print(
        """
Your Plex Media Server credentials are stored in the .env file.
If you modify your password, the token might become invalid.
You will need to run -setup again to update the token or manually editing it in the .env file.
"""
    )


def add_user_process():
    user = _setup_user_process()
    _add_user_env(user)


if args[0] == "-setup":
    if (
        not load_dotenv()
        or not get_from_env("DATA")
        or not json.loads(get_from_env("DATA"))
    ):
        add_user_process()
        print(
            """
Some of your shows might use a different season/episode numbering system than Trakt.tv.
The fallback method to avoid any issues requires access to your Plex Media Server to retrieve the needed data to point to the correct episode.
Syncing your Plex collection to Trakt.tv also requires access to your Plex Media Server.
"""
        )
        setup_plex_ = input(
            "Do you want to setup access to your Plex Media Server ? (y/n): "
        )
        if setup_plex_.lower() == "y":
            setup_plex()
        print("Setup completed!")
        sys.exit(0)
    else:
        print("The .env file already exists!")
        print(
            "If you want to reset the settings, use -reset. If you want to add a new user, use -add. For more help, use -h"
        )
        sys.exit(1)

if args[0] == "-reset":
    if load_dotenv() and get_from_env("DATA"):
        os.remove(".env")
        if os.path.exists("ratingkeys.db"):
            os.remove("ratingkeys.db")
            print(
                "The .env file and the ratingkeys.db file have been deleted! You can now run -setup"
            )
        else:
            print("The .env file has been deleted! You can now run -setup")
    else:
        print("Haha, there is no data, you should first run -setup!")
    sys.exit(0)


def _refresh_token(user: dict, data: dict):
    print(data, type(data))
    print(user, type(user))

    body = {
        "refresh_token": user["refresh_token"],
        "client_id": user["client_id"],
        "client_secret": user["client_secret"],
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "refresh_token",
    }
    req = requests.post(
        "https://api.trakt.tv/oauth/token", data=body
    )  # {"access_token": "xxx", "token_type": "Bearer", "expires_in": 7775999, "refresh_token": "xxx", "scope": "public", "created_at": 1690376320}

    for key, value in req.json().items():
        user[key] = value
    set_key(".env", "DATA", json.dumps(data))


def refresh_token(plex_user=None):
    data = json.loads(get_from_env("DATA"))
    # user: { "created_at": 123, "expires_in": 12}
    # if created_at + expires_in < 1 month till the date, then refresh the token
    if plex_user:
        user = data[plex_user]
        _refresh_token(user, data)
    else:
        for user in data:
            _refresh_token(data[user], data)


def less_month_expiration_token_users(data):
    """
    The function `less_month_expiration_token_users` returns a list of users whose tokens are expiring
    within one month.

    :param data: The `data` parameter is a list of dictionaries, where each dictionary represents a
    user. Each user dictionary should have the following keys:
    :return: a list of users whose tokens are expiring within one month.
    """
    users = []
    for key, value in data.items():
        user = value
        # using time to get the 1 month in seconds
        time_trigger = 60 * 60 * 24 * 30
        if (
            user["created_at"] + user["expires_in"] < time.time() + time_trigger
        ):  #  and user["created_at"] + user["expires_in"] > time.time() - time_trigger #* see comment below
            users.append(key)
        # elif (user["created_at"] + user["expires_in"]) - time.time() < 0:
        #     log(f"User {user['username']} token has expired ! You need to -setup") #* not sure if the refresh_token work indefinitely, in case not, this will be usefull
    return users


if args[0] == "-refreshToken":
    if load_dotenv() and get_from_env("DATA"):
        refresh_token()
        sys.exit(0)
    else:
        print("Haha, there is no data, you should first run -setup !")
        sys.exit(1)


if load_dotenv() and get_from_env("DATA"):
    users = less_month_expiration_token_users(json.loads(get_from_env("DATA")))
    if users:
        for user in users:
            refresh_token(user)
            print(f"User {user}'s token has been refreshed!")
            if len(users) > 1:
                time.sleep(3)  # to be sure not to get a 429 (rate limit)


if args[0] == "-add":
    add_user_process()
    sys.exit(0)

if args[0] == "-remove":
    data = json.loads(get_from_env("DATA"))

    if load_dotenv() and get_from_env("DATA"):
        data = json.loads(get_from_env("DATA"))
        plex_user = input("Enter the Plex username: ")
        if plex_user in data:
            del data[plex_user]
            set_key(".env", "DATA", json.dumps(data))
            print(f"User {plex_user} has been removed!")
            sys.exit(0)
        else:
            print(f"User {plex_user} doesn't exist!")
    else:
        print("Haha, there is no data, you should first run -setup !")
    sys.exit(1)


if not load_dotenv():
    raise FileNotFoundError("Couldn't load .env file! Run -setup to create it.")

NUMBER_OF_ARGS = len(args)

arguments_list = []
if args[0] == "-m":
    SCROBBLE = True
    i = 0
    while i < NUMBER_OF_ARGS:
        current_arg = args[i]
        if (
            current_arg.startswith("-")
            and i + 1 < NUMBER_OF_ARGS
            and not args[i + 1].startswith("-")
        ):  # if it isn't a show -s is empty followed by -M, so we go to the next arg -M otherwise we would go to the title string
            next_arg = args[i + 1] if i + 1 < NUMBER_OF_ARGS else ""
            if " " in next_arg:
                next_arg = f'"{next_arg}"'
            arguments_list += [current_arg, next_arg]
            i += 2
        else:
            i += 1
else:
    SCROBBLE = False

log(f"ARGUMENTS: {args}")

log(f"SCROBBLE: {SCROBBLE}")
if SCROBBLE:
    proc = subprocess.check_output(["py", "scrobble.py"] + args, shell=True, text=True)
else:
    proc = subprocess.check_output(
        ["py", "sync_collections.py"] + args, shell=True, text=True
    )

log(proc)
print(proc)
