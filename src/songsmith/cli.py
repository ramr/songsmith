#!/usr/bin/env python3

""" Command line utility to search and play local music files. """

#
#  Songsmith command line utility.
#
#  author: ramr

#
#  Copyright 2024 ramr
#
#  License: See https://github.com/ramr/songsmith/blob/master/LICENSE
#

import argparse
import copy
#from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import random
import subprocess
from typing import Any, Dict
from urllib.parse import unquote, urlparse

import pandas

from songsmith.constants import CONFIGFILE, LIBRARY, DATAFILE

from songsmith.filters import apply
from songsmith.logger import LOG
from songsmith.database import populate, load


DEFAULT_MEDIA_PLAYER = "mpv --vo=null --no-audio-display"
CONFIG_PLAYER_KEY = "player"
CONFIG_DATABASE_KEY = "database"

LONG_VIEW_COLUMNS = ["Name", "Artist", "Album", "Genre", "Mins",
                     "Composer", "Album Artist", "Year",
                    ]

DETAILS_COLUMNS = ["Name", "Artist", "Album", "Genre", "Mins",
                   "Track Number", "Disc Number", "Disc Count",
                   "Size", "Total Time", "Play Count", "Year",
                   "Bit Rate", "Sample Rate", "Date Added",
                   "Compilation", "Favorited", "Music Video",
                   "Location",
                   "Comments",
                  ]

DISPLAY_OPTIONS = ['display.max_rows', 128,
                   'display.max_columns', None,
                   'display.precision', 2,
                   'display.width', 0,
                   'display.max_colwidth', 32,
                  ]


def _parse_args() -> argparse.Namespace:
    """ Parse command line arguments. """
    parser = argparse.ArgumentParser(description="Songsmith")

    parser.add_argument('-c', '--config', type=str, default=CONFIGFILE,
                        help=f"custom config file [{CONFIGFILE}]")

    parser.add_argument('-b', '--build', action="store_true",
                        help="build songsmith database from xml library")
    parser.add_argument('-x', '--xml', type=str, default=LIBRARY,
                        help="location of exported music Library.xml")

    parser.add_argument('-v', '--validate', action="store_true",
                        help="check and validate song database")

    parser.add_argument('-s', '--songs', type=str,
                        help="filter matching songs")
    parser.add_argument('-a', '--albums', type=str,
                        help="filter songs in the matched albums")
    parser.add_argument('-r', '--artists', type=str,
                        help="filter songs for the matched artists")

    parser.add_argument('-l', '--list', action="store_true",
                        help="list details about the filtered song list")

    parser.add_argument('-p', '--play', action="store_true",
                        help="play the filtered song list")

    parser.add_argument('-m', '--mix', action="store_true",
                        help="mix up (shuffle) the filtered song list")

    parser.add_argument('-n', '--nsamples', type=int, default=0,
                        help="randomly sample 'n' songs")

    args = parser.parse_args()
    return args


def _load_config(path: Path = CONFIGFILE) -> Dict[str, Any]:
    """ Reads config file. """
    config = {}

    if path.exists():
        with path.open("rt", encoding="utf-8") as zfp:
            for line in zfp.read().splitlines():
                if line.startswith("#"):
                    continue

                pieces = line.split("=")
                if len(pieces) > 1:
                    values = [v.strip() for v in pieces[1:]]
                    config[pieces[0].strip()] = "=".join(values)

    if CONFIG_PLAYER_KEY not in config:
        config[CONFIG_PLAYER_KEY] = DEFAULT_MEDIA_PLAYER

    if CONFIG_DATABASE_KEY not in config:
        config[CONFIG_DATABASE_KEY] = DATAFILE

    return config


def _build_database(source: Path, database: Path = DATAFILE) -> None:
    """ Build the songsmith database. """

    LOG.info("Building database from %s ...", source)
    metadata = populate(source, database)

    LOG.info("Database file: %s", database)

    #  A large number of playlists could make the display unwieldy, so
    #  trim those out.
    summary = copy.deepcopy(metadata)

    #  For names you can use:
    #playlists = [d['Name'] for d in metadata['Playlists']]

    #  For brevity in output, using just the number of playlists.
    summary['Playlists'] = len(metadata['Playlists'])

    LOG.info("Metadata: %s", json.dumps(summary, indent=4))


def _validate(database: str) -> None:
    """ Validate songs in the database. """
    df = load(database)

    missing = []

    for yuri in df['Location']:
        song = unquote(urlparse(yuri).path)
        if not Path(song).exists():
            missing.append(song)

    if len(missing) == 0:
        LOG.info("Hakuna matata - all is good ... one less worry!")
        return

    LOG.info("%d Missing files:\n%s\n", len(missing),
             json.dumps(missing, indent=4))




def _search(database: str, args: argparse.Namespace) -> pandas.DataFrame:
    """ Search for songs matching the filtering criteria. """
    df = load(database)

    criteria = {"songs": args.songs, "albums": args.albums,
                "artists": args.artists,
               }
    results = apply(df, criteria)

    if args.nsamples > 0 and args.nsamples < len(results):
        results = results.sample(n=args.nsamples)

    return results


def _list(df: pandas.DataFrame, details: bool = False) -> None:
    """ List details about the songs found. """

    #  Convert total track time to minutes.
    df["Mins"] = df['Total Time'].dt.total_seconds()/60

    if len(df) == 1:
        LOG.info("Result: \n%s", df[DETAILS_COLUMNS].T)
        return

    cols = ["Name", "Artist", "Mins"]

    with pandas.option_context(*DISPLAY_OPTIONS):
        columns = LONG_VIEW_COLUMNS if details else cols
        LOG.info("Results: %d songs\n%s", len(df), df[:][columns])


def _play(df: pandas.DataFrame, player: str = None,
          shuffle: bool = False) -> None:
    """ Play all the tracks found. """
    _list(df)

    if not player:
        return

    paths = [unquote(urlparse(yuri).path) for yuri in list(df['Location'])]
    playlist = sorted(paths)
    if shuffle:
        random.shuffle(playlist)

    counter = 0
    for song in playlist:
        counter += 1

        args = player.split(" ")
        args.extend([song])
        LOG.info("Running command %s ...", args)
        LOG.info("Playing song %s ...\n  - Song #%d of %d\n", song,
                 counter, len(playlist))

        try:
            _proc = subprocess.run(args, check=True)

        except KeyboardInterrupt:
            os._exit(4)

        #  Ideally we would have captured stdout and stderr and streamed
        #  the info but mpv and afplay keep updating the play time, so
        #  that's like a constant stream of messages ...
        #
        #  with subprocess.Popen(args, shell=True, stdout=subprocess.PIPE,
        #                        stderr=subprocess.STDOUT) as sproc:
        #      for aline in sproc.stdout:
        #          LOG.info(aline.decode('utf-8'))


def cli() -> None:
    """ Songsmith command line utility. """
    args = _parse_args()

    config = _load_config(args.config)

    if args.build:
        _build_database(args.xml, config[CONFIG_DATABASE_KEY])
        return

    if args.validate:
        _validate(config[CONFIG_DATABASE_KEY])
        return

    df = _search(config[CONFIG_DATABASE_KEY], args)

    if args.play:
        _play(df, config[CONFIG_PLAYER_KEY], shuffle=args.mix)
        return

    _list(df, details=args.list)


#
#  main():
#
if __name__ == "__main__":
    cli()
