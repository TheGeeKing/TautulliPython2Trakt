<p align="center">
  <a href="https://github.com/TheGeeKing/TautulliPython2Trakt">
    <img src="image.png" alt="TautulliPython2Trakt's logo" width="80" height="80">
  </a>
  <h1 align="center">Tautulli Python 2 Trakt</h1>
</p>

## Table of Contents <!-- omit from toc -->

- [Description](#description)
- [What it can do](#what-it-can-do)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Script Setup](#script-setup)
  - [Tautulli Setup](#tautulli-setup)
    - [Scrobbling](#scrobbling)
    - [Collection](#collection)
- [Usage](#usage)
- [More info](#more-info)
- [Similar Projects](#similar-projects)

## Description

Python script to scrobble what you watch, sync your collected movies and TV shows from [Tautulli](https://github.com/Tautulli/Tautulli) to [Trakt.tv](https://trakt.tv/).

## What it can do

- Track watched status of movies and TV shows
- Sync collected movies and TV shows to Trakt.tv

## Requirements

- Tautulli 2.12.5 or higher
- Python 3.11 or higher
- install requirements.txt
  1. `pip install -r requirements.txt`

## Installation

### Script Setup

Download the latest release from [here](https://github.com/TheGeeKing/TautulliPython2Trakt/releases), unzip it and place all files in a folder.

Create a new [application](https://trakt.tv/oauth/applications) and add the following settings:

**Name:** `TautulliPython2Trakt` \
**Redirect uri:** `urn:ietf:wg:oauth:2.0:oob` \
**Permissions:** `/scrobble`

Run the script:

```bash
python TautulliPython2Trakt.py -setup
```

Follow the setup steps.

If you want to collect your movies and TV shows, you need to do the Plex Media Server setup! You might also want to add credentials/token to access your Plex Media Server as this can help to scrobble the correct episode to Trakt.tv if you don't use the TMDB database for sorting your shows. [How to find my token ?](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)

### Tautulli Setup

#### Scrobbling

1. Go to Tautulli > `Settings` > `Notification Agents` > `Add a new notification agent` > `Script`
2. Set the `Script Folder` to the folder where you placed the script, then select the script `TautulliPython2Trakt.py` in the `Script File` field. Put the `Script Timeout` to `0`.
3. In the `Triggers` section, select:
   1. `Playback Start`
   2. `Playback Stop`
   3. `Playback Pause`
   4. `Playback Resume`
   5. `Watched`
4. Put conditions if you want to, like username, media type, etc.
5. In the `Arguments` tab, put the following arguments:
   1. Playback Start / Playback Resume: `pythonw -m {media_type} -s "{show_name}" -M "{title}" -y "{year}" -t "{thetvdb_id}" -i "{imdb_id}" -r {rating_key} -S {season_num} -E {episode_num} -P {progress_percent} -a start -PlexUser {username}`
   2. Playback Stop / Watched: `pythonw -m {media_type} -s "{show_name}" -M "{title}" -y "{year}" -t "{thetvdb_id}" -i "{imdb_id}" -r {rating_key} -S {season_num} -E {episode_num} -P {progress_percent} -a stop -PlexUser {username}`
   3. Playback Pause: `pythonw -m {media_type} -s "{show_name}" -M "{title}" -y "{year}" -t "{thetvdb_id}" -i "{imdb_id}" -r {rating_key} -S {season_num} -E {episode_num} -P {progress_percent} -a pause -PlexUser {username}`

#### Collection

1. Go to Tautulli > `Settings` > `Notification Agents` > `Add a new notification agent` > `Script`.
2. Set the `Script Folder` to the folder where you placed the script, then select the script `TautulliPython2Trakt.py` in the `Script File` field. Put the `Script Timeout` to `0`.
3. In the `Triggers` section, select `Recently Added`.
4. Put conditions if you want to, like media type, etc.
5. In the `Arguments` tab, put the following argument:
   1. Recently Added: `<movie>pythonw -c movies -PlexUser %OWNER%</movie><episode>pythonw -c episodes -PlexUser %OWNER%</episode><season>pythonw -c episodes -PlexUser %OWNER%</season><show>pythonw -c episodes -PlexUser %OWNER%</show>`

## Usage

```
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
```

## More info

Default scrobbler behavior is for:

- Movies, the data from Tautulli is sent directly to Trakt.
- Episodes:
  - If your Plex Media Server is connected, we get the ratingkey from the data sent by Tautulli. We make a database filled with ratingkey paired to ids. We search for the ids linked to the ratingkey in the database. We send the ids to Trakt. Trakt.tv uses TMDB database, so sending basic info like season and episode number can mismatch with your plex configuration. This way we ensure that the episode is scrobbled to the correct one on the Trakt end.
  - If you are not connected to your Plex Media Server, we send the data from Tautulli directly to Trakt.

Syncing behavior:

- Based on the -c argument, we either sync movies or episodes. It is syncing your entire collection, not just the recently added, so it might take some time. If it takes way too much time, open an issue and I might add/find a way to only sync the recently added content.
- Based on the -PlexUser argument:
  - (default behavior) `%OWNER%`, we sync the collections to the owner Trakt account.
  - If a user is specified, we sync the collections to the specified user Trakt account. ⚠️ **It will sync like if it was the owner, so even if the user has not access to the library where the content was added.** You can also use a list: `"[username1, username2]"`, typo is very important.
  - If `%ALL%` is specified, we sync the collections to all the users Trakt account. It will check if the users have access to the content before adding it to their collection.

## Similar Projects

Inspired from: https://github.com/frugglehost/TautulliBatch2Trakt

- https://github.com/JvSomeren/tautulli-watched-sync
- https://github.com/xanderstrike/goplaxt
- https://github.com/gazpachoking/trex
- https://github.com/dabiggm0e/plextrakt
- https://github.com/trakt/Plex-Trakt-Scrobbler
- https://github.com/Generator/tautulli2trakt
