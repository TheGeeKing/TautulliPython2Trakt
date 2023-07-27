import json
import os
import sys

from dotenv import load_dotenv
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

MAX_LINES = 200


def log(msg):
    """
    The `log` function appends a message to a log file, keeping only the last `MAX_LINES` lines if the
    file exceeds that limit.

    :param msg: The `msg` parameter is a string that represents the message to be logged
    """

    # check if log.txt exists, otherwise create it
    if not os.path.exists("log.txt"):
        with open("log.txt", "w", encoding="utf-8") as f:
            f.write("")

    # if log.txt exists, but is longer than MAX_LINES lines, keep only last (MAX_LINES-1) lines
    with open("log.txt", "r", encoding="utf-8") as f1:
        lines = f1.readlines()
        if len(lines) > MAX_LINES:
            with open("log.txt", "w", encoding="utf-8") as f2:
                f2.writelines(lines[-(MAX_LINES - 1) :])

    # if log.txt exists, append to it
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")


def guids_to_ids(guids):
    """
    The function `guids_to_ids` takes a list of objects with `id` attributes and returns a dictionary
    mapping the first part of the `id` string to the second part, converting the second part to an
    integer if the first part is either "tmdb" or "tvdb".

    :param guids: The `guids` parameter is a list of objects. Each object has an `id` attribute, which
    is a string representing a unique identifier. The format of the `id` string is "protocol://value",
    where the protocol can be "tmdb", "tvdb", or any other
    :return: a dictionary called "ids" which contains the extracted IDs from the given list of guids.
    """
    ids = {}
    for obj in guids:
        ids[f"{obj.id.split('://')[0]}"] = (
            int(obj.id.split("://")[1])
            if f"{obj.id.split('://')[0]}" in ["tmdb", "tvdb"]
            else obj.id.split("://")[1]
        )
    return ids


def get_plex_server():
    """
    The function `get_plex_server` returns a PlexServer object based on the provided environment
    variables.
    :return: a `PlexServer` object.
    """
    load_dotenv()
    if (os.getenv("PLEX_BASEURL").startswith("http")) and os.getenv("PLEX_TOKEN"):
        return PlexServer(os.getenv("PLEX_BASEURL"), os.getenv("PLEX_TOKEN"))
    elif (not (os.getenv("PLEX_BASEURL").startswith("http"))) and os.getenv(
        "PLEX_TOKEN"
    ):
        account = MyPlexAccount(token=os.getenv("PLEX_TOKEN"))
        return account.resource(
            os.getenv("PLEX_BASEURL")
        ).connect()  # returns a PlexServer instance


def get_from_env(
    key: str,
    user: str = None,
):
    """
    The function `get_from_env` retrieves a value from the environment variables based on a given key,
    and optionally for a specific user.

    :param key: The `key` parameter is a string that represents the name of the environment variable you
    want to retrieve
    :type key: str
    :param user: The `user` parameter is an optional parameter that specifies the user for which the
    environment variable value should be retrieved. If the `user` parameter is not provided, the
    function will return the value of the environment variable specified by the `key` parameter
    :type user: str
    :return: the value associated with the given key from the environment variables. If the optional
    user parameter is provided, it will return the value associated with the given key for that specific
    user from the "DATA" environment variable.
    """
    load_dotenv()
    if not user:
        return os.getenv(key)
    data = json.loads(os.getenv("DATA"))
    if user in data:
        return data[user][key]


class ProgressBar:
    def __init__(self, title):
        self.title: str = title
        self.progress: float = 0
        self.parts: int = 50

    def start(self):
        """
        The function `start` writes a progress bar to the console using the `title` and `parts`
        attributes of the object.
        """
        # sys.stdout.write(self.title + ": [" + "-"*self.parts + "]" + chr(8)*(self.parts+1))
        sys.stdout.write(f"{self.title} : [ {'-'*self.parts} ] {chr(8)*(self.parts+1)}")
        sys.stdout.flush()

    def update(self, value: float | int):
        """
        The function updates the progress bar based on the given value.

        :param value: The `value` parameter represents the progress value that needs to be updated. It
        can be either a float or an integer
        :type value: float | int
        """
        value = int(value * self.parts // 100)
        sys.stdout.write("#" * (value - self.progress))
        sys.stdout.flush()
        self.progress = value

    def end(self):
        """
        The function prints a string of "#" characters based on the difference between the total number
        of parts and the progress.
        """
        sys.stdout.write("#" * (self.parts - self.progress) + "]\n")
        sys.stdout.flush()
