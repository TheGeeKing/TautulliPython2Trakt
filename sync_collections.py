import json
import sys
import threading
import time

import requests
from dotenv import load_dotenv
from plexapi.library import MovieSection, ShowSection

from get_ids import update_database
from utilities import get_from_env, get_headers, get_plex_server, log

load_dotenv()

ARGS = sys.argv[1:]
NUMBER_OF_ARGS = len(ARGS)

if len(ARGS) < 4:
    print("Not enough arguments given!")
    sys.exit(1)

i = 0
while i < NUMBER_OF_ARGS:
    current_arg = ARGS[i]
    if (
        not current_arg.startswith("-")
        or i + 1 >= NUMBER_OF_ARGS
        or ARGS[i + 1].startswith("-")
    ):
        i += 1
        continue
    # log(f"{i}: {current_arg}")
    arg = ARGS[i + 1]
    match current_arg:
        case "-c":
            TYPE = arg
        case "-PlexUser":
            if arg == "%OWNER%":
                load_dotenv()
                data = get_from_env("DATA")
                plex = get_plex_server()
                if plex.myPlexAccount().username in list(data.keys()):
                    PLEX_USER = plex.myPlexAccount().username
                else:
                    print("Owner of the server not found in the env!")
                    sys.exit(1)
            elif arg == "%ALL%":  # %ALL% option will sync to all users found in the env
                PLEX_USER = list(data.keys())
                # We will later as a privacy measure, check if the user has access to the item before adding it to his collection.
            else:
                # The else is for when we want to sync the collections of a specific user. If owner trusts a user, he can add a notification agent and write the username in the argument -PlexUser. You can do for example, `py TautulliPython2Trakt.py -c movies -PlexUser "username"`. It will bypass the verification if the user has access to the item before adding it to his collection.
                PLEX_USER = arg
    i += 2

if TYPE not in ["movies", "episodes"]:
    raise ValueError("Invalid value!")

# if we sync we are probably doing so because Tautulli triggered `Recently Added` so we update the database for later scrobbling
# might cause some issues if the user has not setup plex access. It might raise an error stopping the script
thread = threading.Thread(target=update_database)
thread.start()

plex = get_plex_server()

ALL_SECTIONS = plex.library.sections()
MOVIES_SECTIONS = [
    section for section in ALL_SECTIONS if isinstance(section, MovieSection)
]
SHOWS_SECTIONS = [
    section for section in ALL_SECTIONS if isinstance(section, ShowSection)
]


def get_ids_for_sections(SECTIONS: list):
    contents = []
    # we go through each library and get the media/content and retrieve its ids
    # we append the ids to the contents list
    for lib in SECTIONS:
        search = lib.searchEpisodes() if isinstance(lib, ShowSection) else lib.search()
        for content in search:
            ids = {}
            # Iterate through each object in the "ids" list
            for obj in content.guids:
                # Update the ids dictionary with the dynamic key-value pairs
                ids[f"{obj.id.split('://')[0]}"] = (
                    int(obj.id.split("://")[1])
                    if f"{obj.id.split('://')[0]}" in ["tmdb", "tvdb"]
                    else obj.id.split("://")[1]
                )
            if ids:
                contents.append({"ids": ids})
    return contents


def sync_with_trakt(contents: list, HEADERS: dict):
    # We post the content list with all the ids, it is either movies or episodes based on TYPE
    req = requests.post(
        "https://api.trakt.tv/sync/collection",
        headers=HEADERS,
        data=json.dumps({f"{TYPE}": contents}),
    )
    return req


def display_req(req):
    try:
        log(f"{req.status_code} - {req.json()}")
        print(f"{req.status_code} - {req.json()}")
    except (
        requests.exceptions.JSONDecodeError
    ):  # if there is an error we get text not json
        log(f"{req.status_code} - {req.text}")
        print(f"{req.status_code} - {req.text}")


def sync(ids, HEADERS):
    req = sync_with_trakt(ids, HEADERS)
    display_req(req)
    while req.status_code == 429:
        time.sleep(5)
        req = sync_with_trakt(ids, HEADERS)
        display_req(req)


def sync_non_owner(users: list):
    plex = get_plex_server()
    plex_users = plex.myPlexAccount().users()

    # users is the list(data.keys()) from the data env variable, so we redefine the users variable to only include the users that are in the plex_users list
    # this will remove the owner as the owner is not in the plex_users list
    users = [
        user for user in plex_users if user.username in users
    ]  # in users is the list(data.keys())
    log(f"Users: {users}")
    for user in users:
        # we keep the sections we want based on the -c argument inputed
        # we define this here to then after, remove the sections that the user doesn't have access to
        sections = MOVIES_SECTIONS if TYPE == "movies" else SHOWS_SECTIONS

        for lib_index in range(len(sections)):
            #! Here we assume the owner share only one server with the user, if he shares more than one, this might have unknown behaviour
            if user.servers[0].section(sections[lib_index].title).shared is False:
                sections.pop(
                    lib_index
                )  # we remove the library from the list if the user doesn't have access to it
        HEADERS = get_headers(user.username)

        ids = get_ids_for_sections(sections)
        sync(ids, HEADERS)


def sync_owner_like(username):
    """If username is empty, we sync the owner of the PMS.
    If the username is passed, we sync the username that has been passed with same privileges as the owner. It means that even if the username doesn't have access to a library, it will still be synced. For privacy concerns, the `sync_non_owner` function is recommended.
    """

    # we keep the sections we want based on the -c argument inputed
    # we define this here to then after, remove the sections that the user doesn't have access to
    SECTIONS = MOVIES_SECTIONS if TYPE == "movies" else SHOWS_SECTIONS

    data = json.loads(get_from_env("data"))
    if username == plex.myPlexAccount().username and username not in list(data.keys()):
        print(
            f"Owner of the server {plex.myPlexAccount().username} not found in the env!"
        )
        log(
            f"Owner of the server {plex.myPlexAccount().username} not found in the env!"
        )
        sys.exit(1)
    elif username not in list(data.keys()):
        print(f"Username {username} not found in the env!")
        log(f"Username {username} not found in the env!")
        sys.exit(1)

    HEADERS = get_headers(username)

    ids = get_ids_for_sections(SECTIONS)
    sync(ids, HEADERS)


if arg == "%OWNER%":  # we sync the owner
    log("Syncing owner...")
    sync_owner_like(plex.myPlexAccount().username)
elif (
    arg == "%ALL%"
):  # if the argument is %ALL%, we sync all the users and check that they have each access to the libraries
    log("Syncing all...")
    sync_owner_like(plex.myPlexAccount().username)
    sync_non_owner(PLEX_USER)
elif arg != "":  # we sync the user or users that have been passed
    if arg.startswith("[") and arg.endswith("]"):
        arg = arg.strip("][").split(", ")
        log(f"Passed users: {arg}")
        for user in arg:
            log(f"Syncing {user}...")
            sync_owner_like(user)
    else:
        log(f"Syncing {arg}...")
        sync_owner_like(PLEX_USER)
else:
    print("No argument passed!")
    log("No argument passed!")
    sys.exit(1)
log("Synced!")
