import json
import sys
import threading
import time

import requests
from dotenv import load_dotenv
from plexapi.library import MovieSection, ShowSection
from get_ids import update_database

from utilities import get_from_env, get_plex_server, log

load_dotenv()

ARGS = sys.argv[1:]
NUMBER_OF_ARGS = len(ARGS)

if len(ARGS) < 4:
    print("Not enough arguments given !")
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
            PLEX_USER = arg
    i += 2

if TYPE not in ["movies", "episodes"]:
    raise ValueError("Invalid value !")

plex = get_plex_server()

ALL_SECTIONS = plex.library.sections()
MOVIES_SECTIONS = [
    section for section in ALL_SECTIONS if isinstance(section, MovieSection)
]
SHOWS_SECTIONS = [
    section for section in ALL_SECTIONS if isinstance(section, ShowSection)
]

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {get_from_env('access_token', PLEX_USER)}",
    "trakt-api-version": "2",
    "trakt-api-key": get_from_env("client_id", PLEX_USER),
}

# we keep the sections we want based on the -c argument inputed
SECTIONS = MOVIES_SECTIONS if TYPE == "movies" else SHOWS_SECTIONS

# if we sync we are probably doing so because Tautulli triggered `Recently Added` so we update the database for later scrobbling
thread = threading.Thread(target=update_database)
thread.start()

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

# We post the content list with all the ids, it is either movies or episodes based on TYPE
req = requests.post(
    "https://api.trakt.tv/sync/collection",
    headers=HEADERS,
    data=json.dumps({f"{TYPE}": contents}),
)


def display_req(req):
    try:
        log(f"{req.status_code} - {req.json()}")
        print(f"{req.status_code} - {req.json()}")
    except (
        requests.exceptions.JSONDecodeError
    ):  # if there is an error we get text not json
        log(f"{req.status_code} - {req.text}")
        print(f"{req.status_code} - {req.text}")


display_req(req)
while req.status_code == 429:
    time.sleep(5)
    req = requests.post(
        "https://api.trakt.tv/sync/collection",
        headers=HEADERS,
        data=json.dumps({f"{TYPE}": contents}),
    )
    display_req(req)
