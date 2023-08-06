import json
import sys
import time

import requests
from dotenv import load_dotenv

from get_ids import search_for_media_ratingkey
from utilities import get_from_env, log

load_dotenv()

args = sys.argv[1:]
NUMBER_OF_ARGS = len(args)


log(f"args:\n{args}\n")
log(f"NUMBER_OF_ARGS: {NUMBER_OF_ARGS}\n")

i = 0
while i < NUMBER_OF_ARGS:
    current_arg = args[i]
    if (
        current_arg.startswith("-")
        and i + 1 < NUMBER_OF_ARGS
        and not args[i + 1].startswith("-")
    ):  # if it isn't a show -s is empty followed by -M, so we go to the next arg -M otherwise we would go to the title string
        pass
    else:
        i += 1
        continue
    # log(f"{i}: {current_arg}")
    arg = args[i + 1]
    match current_arg:
        case "-m":
            MEDIA_TYPE = arg
        case "-s":
            SHOW_NAME = arg
        case "-M":
            MOVIE_NAME = arg
        case "-y":
            MEDIA_YEAR = arg
        case "-t":
            TVDB_ID = int(arg)
        case "-i":
            IMDB_ID = arg
        case "-r":
            RATINGKEY = arg
        case "-S":
            SEASON = int(arg)
        case "-E":
            EPISODE = int(arg)
        case "-P":
            PROGRESS = float(arg)
        case "-a":
            ACTION = arg
        case "-PlexUser":
            PLEX_USER = arg
    i += 2

if "MEDIA_YEAR" not in locals():
    MEDIA_YEAR = 0

if MEDIA_YEAR == "":
    MEDIA_YEAR = 0

body = ""
log(f"media_type: {MEDIA_TYPE}")
if MEDIA_TYPE == "movie":
    body = {
        "movie": {
            "title": f"{MOVIE_NAME}",
            "year": f"{MEDIA_YEAR}",
            "ids": {"imdb": f"{IMDB_ID}"},
        }
    }
elif MEDIA_TYPE in ["show", "episode"]:
    if get_from_env("PLEX_BASEURL") and search_for_media_ratingkey(
        MEDIA_TYPE, RATINGKEY
    ):  # this is slower, but it's more reliable if season/episode database is not the same one as Trakt.tv
        ids = search_for_media_ratingkey(MEDIA_TYPE, RATINGKEY)
        body = {"episode": {"ids": ids}}
    else:
        body = {
            "show": {
                "title": f"{SHOW_NAME}",
                "year": MEDIA_YEAR,
                "ids": {"tvdb": TVDB_ID},
            },
            "episode": {"season": SEASON, "number": EPISODE},
        }

else:
    log("Invalid media type")
    sys.exit(1)

body["progress"] = PROGRESS
body["app_version"] = "1.0"
body["app_date"] = time.strftime("%Y-%m-%d")

URI = f"https://api.trakt.tv/scrobble/{ACTION}"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {get_from_env('access_token', PLEX_USER)}",
    "trakt-api-version": "2",
    "trakt-api-key": get_from_env("client_id", PLEX_USER),
}

body = json.dumps(body)

log(body)
log(URI)

r = requests.post(URI, headers=HEADERS, data=body)
log(f"{r.status_code} | {r.text}")
if r.status_code == 404:
    if MEDIA_TYPE == "movie":
        ids = search_for_media_ratingkey(MEDIA_TYPE, RATINGKEY)
        if ids:
            body = {
                "movie": {
                    "ids": ids,
                }
            }
            body["progress"] = PROGRESS
            body["app_version"] = "1.0"
            body["app_date"] = time.strftime("%Y-%m-%d")
            body = json.dumps(body)
            r = requests.post(URI, headers=HEADERS, data=body)
        else:
            msg = "404, movie or episode not found on Trakt.tv. If this is incorrect, please report it on github."
            log(msg)
            print(msg)
            sys.exit(1)
while r.status_code == 429:
    time.sleep(5)
    r = requests.post(URI, headers=HEADERS, data=body)
    log(f"{r.status_code} | {r.text}")
print(r.status_code)
sys.exit(0)
