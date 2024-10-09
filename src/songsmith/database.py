#!/usr/bin/env python3

""" Songsmith database load and populate code. """

#
#  Songsmith code for database load and database populate from an
#  exported Apple Music library (iTunes/Music xml format).
#
#  author: ramr

#
#  Copyright 2024 ramr
#
#  License: See https://github.com/ramr/songsmith/blob/master/LICENSE
#

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict
from xml.etree import ElementTree

import pandas
import numpy

from songsmith.constants import LIBRARY, DATAFILE
from songsmith.logger import LOG


BOOLEAN_COLUMNS = ["Album Loved", "Apple Music", "Clean", "Compilation",
                   "Explicit", "HD", "Has Video", "Loved", "Matched",
                   "Music Video", "Part of Gapless Album", "Playlist Only",
                  ]
NUMERIC_COLUMNS =["Artwork Count", "Bit Rate", "Disc Count", "Disc Number",
                  "Play Count", "Play Date", "Sample Rate", "Size",
                  "Skip Count", "Track Count", "Track ID", "Track Number",
                  "Year",
                 ]
DATE_COLUMNS = ["Date Added", "Date Modified", "Play Date UTC",
                "Release Date", "Skip Date",
               ]

# Apple uses different Unix epoch time - Jan 1, 1904 (earliest new year's
# daya that fell on a leap year). Unix epoch is Jan 1, 1970 so adjust the
# Play Date column value by about 24107 days ((66 * 365) + 17 leap days).
# And 24107 * 60 * 60 * 24 = 2082844800
APPLE_EPOCH_DELTA_SECONDS = 2082844800

KEY_TAG = "key"
DICT_TAG = "dict"
ARRAY_TAG = "array"
TRACKS_KEY = "Tracks"


def _metadata(tree: ElementTree.Element) -> Dict[str, Any]:
    """ Return metadata. """
    md = {}
    k = ""
    for _, elem in enumerate(tree):
        if elem.tag == KEY_TAG:
            k = elem.text
        elif elem.tag == DICT_TAG:
            if k == TRACKS_KEY:
                #  Number of tracks are large, so just use size ... halve
                #  the number of elements to account for key-dict elements.
                md[k] = int(len(elem)/2)
            else:
                md[k] = _metadata(elem)

        elif elem.tag == ARRAY_TAG:
            if k == "Playlist Items":
                #  Number of track ids in a playlist could be large, so
                #  just use size. This is a flat list of track ids, so use
                #  the size as is.
                md[k] = int(len(elem))
            else:
                md[k] = []
                for subtree in elem:
                    md[k].append(_metadata(subtree))

        elif not k.startswith("Smart"):
            md[k] = elem.text

    return md


def _find(tree: ElementTree.Element, name: str, tag: str) -> ElementTree.Element:
    """ Find a matching element (by name and tag type). """
    k = ""
    for _, elem in enumerate(tree):
        if elem.tag == KEY_TAG:
            k = elem.text
        elif elem.tag == tag and k == name:
            return elem

    return None


def _build_dataframe(tree: ElementTree.Element) -> pandas.DataFrame:
    """ Build a pandas dataframe containing information of all songs. """
    LOG.info("Finding song tracks ...")
    tracks = _find(tree, TRACKS_KEY, DICT_TAG)
    if tracks is None:
        LOG.error("No tracks found")
        return None

    column_names = []
    for _, elements in enumerate(tracks):
        for _, elem in enumerate(elements):
            if elem.tag == KEY_TAG:
                column_names.append(elem.text)

    columns = sorted(list(set(column_names)))

    LOG.info("Tracks columns: %s", columns)

    data = defaultdict(list)

    for _, elements in enumerate(tracks):
        cols = list.copy(columns)
        if elements.tag == KEY_TAG:
            continue

        k = ""
        for _, elem in enumerate(elements):
            if elem.tag == KEY_TAG:
                k = elem.text
            else:
                if k in BOOLEAN_COLUMNS:
                    data[k].append(elem.tag)
                else:
                    data[k].append(elem.text)

                cols.remove(k)

        #  Set missing column entries to NaNs.
        for c in cols:
            data[c].append(numpy.nan)

    df = pandas.DataFrame(data)
    df[NUMERIC_COLUMNS] = df[NUMERIC_COLUMNS].apply(pandas.to_numeric)
    df[DATE_COLUMNS] = df[DATE_COLUMNS].apply(pandas.to_datetime)

    # Apple uses different Unix epoch time - Jan 1, 1904 (earliest new
    # year's day that fell on a leap year). Unix epoch is Jan 1, 1970 so
    # adjust the Play Date column value by about 24107 days (66 * 365 +
    # 17 leap days).  And 24107 * 24 * 60 * 60 = 2082844800 seconds
    #
    #pylint: disable=C0301
    # Ref: https://web.archive.org/web/20200805105853/http://joabj.com/Writing/Tech/Tuts/Java/iTunes-PlayDate.html

    delta = APPLE_EPOCH_DELTA_SECONDS
    df["Play Date"] = pandas.to_datetime(df["Play Date"] - delta, unit="s")
    df["Total Time"] = df["Total Time"].apply(pandas.to_numeric)
    df["Total Time"] = pandas.to_timedelta(df["Total Time"], unit="ms")

    LOG.info("Successfully built tracks dataframe.")
    return df


def populate(library=LIBRARY, database=DATAFILE) -> Dict[str, Any]:
    """ Populates local data file from the Apple Music library. """
    #pylint: disable=C0301
    # adapted from: https://jun-s-choi.medium.com/itunes-library-data-analysis-using-python-2b71bf95d07

    tree = ElementTree.parse(library)
    root = tree.getroot()

    metadata = _metadata(root[0])

    df = _build_dataframe(root[0])
    #  this should probably be a debug log.
    LOG.info("Dataframe:\n%s", df.head())

    LOG.info("Saving dataframe to %s ...", database)
    df.to_pickle(database)

    LOG.info("Saved dataframe to %s", database)

    return metadata


def load(database: Path = DATAFILE) -> pandas.DataFrame:
    """ Loads the local data file. """
    return pandas.read_pickle(database)
