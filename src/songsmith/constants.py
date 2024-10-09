#!/usr/bin/env python3

""" Constants. """

#
#  Songsmith constants.
#
#  author: ramr

#
#  Copyright 2024 ramr
#
#  License: See https://github.com/ramr/songsmith/blob/master/LICENSE
#

from pathlib import Path

INSTDIR = Path(__file__).absolute().parent.parent.parent
CONFIGDIR = INSTDIR.joinpath("config")
CONFIGFILE = CONFIGDIR.joinpath("songsmith.conf")

DATADIR = INSTDIR.joinpath("data")
LIBRARY = DATADIR.joinpath("Library.xml")
DATAFILE = DATADIR.joinpath("songsmith.pickle")
