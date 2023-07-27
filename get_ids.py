import json
import os
import sys
import threading

from dotenv import load_dotenv
from plexapi.library import MovieSection, ShowSection

from sql import SQL
from utilities import get_plex_server, guids_to_ids

load_dotenv()

ARGS = sys.argv[1:]

plex = get_plex_server()

ALL_SECTIONS = plex.library.sections()
MOVIES_SECTIONS = [
    section for section in ALL_SECTIONS if isinstance(section, MovieSection)
]
SHOWS_SECTIONS = [
    section for section in ALL_SECTIONS if isinstance(section, ShowSection)
]


def get_json_ids(guids):
    """
    The function `get_json_ids` takes a list of objects with `id` attributes and returns a dictionary
    where the keys are the parts of the `id` before `://` and the values are the parts after `://`,
    converted to integers if the key is either "tmdb" or "tvdb".

    :param guids: A list of objects containing ids
    :return: a dictionary containing the IDs extracted from the given list of guids.
    """
    ids = {}
    for obj in guids:
        # add the id to the dict, format is taking before :// as key and after as value
        ids[f"{obj.id.split('://')[0]}"] = (
            int(obj.id.split("://")[1])
            if f"{obj.id.split('://')[0]}" in ["tmdb", "tvdb"]
            else obj.id.split("://")[1]
        )
    return ids


def _create_database():
    db = SQL(db="ratingkeys.db")
    db.create_table("ratingkeys", (("ratingkey", "INTEGER UNIQUE"), ("ids", "JSON")))


def setup_database():
    if not does_database_exist("ratingkeys.db"):
        _create_database()
    db = SQL(db="ratingkeys.db")

    to_add: list[tuple] = []
    for lib in ALL_SECTIONS:
        search = lib.searchEpisodes() if isinstance(lib, ShowSection) else lib.search()
        for content in search:
            ids = guids_to_ids(content.guids)
            if ids:
                to_add.append((content.ratingKey, json.dumps(ids)))
    db.executemany("INSERT INTO ratingkeys (ratingkey, ids) VALUES (?, ?)", to_add)


def does_database_exist(name: str):
    return os.path.exists(name if name.endswith(".db") else f"{name}.db")


def is_database_empty(table: str):
    if not does_database_exist("ratingkeys.db"):
        return True
    db = SQL(db="ratingkeys.db")
    res = db.execute(f"SELECT * FROM {table}").fetchone()
    return res is None


def update_database():
    """
    The function `update_database` updates the `ids` column in the `ratingkeys` table of a database with
    the JSON representation of the content's guids, for each content in the search results.
    """
    db = SQL(db="ratingkeys.db")
    to_update = []
    for lib in ALL_SECTIONS:
        search = lib.searchEpisodes() if isinstance(lib, ShowSection) else lib.search()
        for content in search:
            ids = json.dumps(guids_to_ids(content.guids))
            to_update.append(({"ratingkey": content.ratingKey, "ids": ids}))
    db.executemany(
        "UPDATE ratingkeys SET ids = :ids WHERE ratingkey = :ratingkey AND ids != :ids",
        to_update,
    )


def _raw_search_for_media_ratingkey_database(ratingkey: int):
    if is_database_empty("ratingkeys"):
        setup_database()
    db = SQL(db="ratingkeys.db")
    res = db.execute(
        "SELECT * FROM ratingkeys WHERE ratingkey = ? LIMIT 1", (ratingkey,)
    ).fetchone()
    return res["ids"] if res else None


def verify_ratingkey(media, ratingkey: int):
    return None if media["ratingKey"] != ratingkey else media


def _raw_search_for_media_ratingkey(media_type: ["movie", "episode"], ratingkey: int):
    SECTIONS = MOVIES_SECTIONS if media_type == "movie" else SHOWS_SECTIONS
    for lib in SECTIONS:
        search = lib.searchEpisodes() if media_type == "episode" else lib.search()
        for content in search:
            if content.__dict__["ratingKey"] == ratingkey:
                return content
    # return verify_ratingkey(plex.fetchItem(ratingkey), ratingkey) /!\ Non working module is trying to but -> 'Failed to parse: http://localhost:3240013954' the ratingkey is merged with the port. otherwise might be a better solution to directly ask the plex server with plex.fetchItem


def search_for_media_ratingkey(
    media_type: ["movie", "episode"], ratingkey: int, database_search: bool = True
):
    if database_search:
        ids = _raw_search_for_media_ratingkey_database(ratingkey)
        if ids:
            return json.loads(ids)
    obj = _raw_search_for_media_ratingkey(media_type, ratingkey)
    if obj:
        # If we are here, it means that the database is outdated
        thread = threading.Thread(target=update_database)
        thread.start()
        return get_json_ids(obj.__dict__["guids"])
    return None
