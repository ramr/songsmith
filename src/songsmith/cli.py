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

DETAILS_COLUMNS = ["Name", "Artist", "Album", "Genre", "Mins",
                   "Composer", "Album Artist", "Year",
                   "Track Number", "Disc Number", "Disc Count",
                   "Size", "Total Time", "Bit Rate", "Sample Rate",
                   "Location",
                   "Comments",
                  ]

DISPLAY_OPTIONS = ['display.max_rows', 100,
                   'display.max_columns', None,
                   'display.precision', 2,
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

    parser.add_argument('-r', '--artists', type=str,
                        help="filter songs for the matched artists")
    parser.add_argument('-a', '--albums', type=str,
                        help="filter songs in the matched albums")
    parser.add_argument('-s', '--songs', type=str,
                        help="filter matching songs")

    parser.add_argument('-p', '--play', action="store_true",
                        help="play the filtered song list")

    parser.add_argument('-l', '--list', action="store_true",
                        help="list details about the filtered song list")

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


def _search(database: str, args: argparse.Namespace) -> pandas.DataFrame:
    """ Search for songs matching the filtering criteria. """
    criteria = {"songs": args.songs, "albums": args.albums,
                "artists": args.artists,
               }

    df = load(database)
    return apply(df, criteria)


def _list(df: pandas.DataFrame, details: bool = False) -> None:
    """ List details about the songs found. """

    #  Convert total track time to minutes.
    df["Mins"] = df['Total Time'].dt.total_seconds()/60

    if len(df) == 1:
        LOG.info("Result: \n%s", df[DETAILS_COLUMNS].T)
        return

    with pandas.option_context(*DISPLAY_OPTIONS):
        columns = DETAILS_COLUMNS if details else DETAILS_COLUMNS[:5]
        LOG.info("Results: \n%s", df[columns])


def _play(df: pandas.DataFrame, player: str = None) -> None:
    """ Play all the tracks found. """
    _list(df)

    if not player:
        return

    songs = [unquote(urlparse(yuri).path) for yuri in list(df['Location'])]

    counter = 0
    for song in sorted(songs):
        counter += 1

        args = player.split(" ")
        args.extend([song])
        LOG.info("Running command %s ...", args)
        LOG.info("Playing song %s ...\n  - Song #%d of %d\n", song,
                 counter, len(songs))

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

    df = _search(config[CONFIG_DATABASE_KEY], args)

    if args.play:
        _play(df, config[CONFIG_PLAYER_KEY])
        return

    _list(df, details=args.list)


#
#  main():
#
if __name__ == "__main__":
    cli()
