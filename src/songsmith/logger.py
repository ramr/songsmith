#!/usr/bin/env python3

""" Logger. """

#
#  Logging utility code.
#
#  author: ramr

#
#  Copyright 2024 ramr
#
#  License: See https://github.com/ramr/songsmith/blob/master/LICENSE
#

import logging
import sys

#  Default logger name.
LOGGER_NAME = "songsmith"

LOG_FMT = '%(asctime)s %(name)s pid=%(process)d: %(levelname)s - %(message)s'


def _default_logger() -> logging.Logger:
    """ Returns default logger. """
    logging.basicConfig(level=logging.NOTSET)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FMT, "%H:%M:%S")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    if logger.handlers is not None:
        logger.handlers.clear()

    logger.addHandler(handler)
    logger.propagate = False

    return logger


#  Default logger.
LOG = _default_logger()


def get() -> logging.Logger:
    """ Returns the default logger. """
    return LOG
