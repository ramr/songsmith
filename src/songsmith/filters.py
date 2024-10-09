#!/usr/bin/env python3

""" Filter songs by names, albums and artists. """

#
#  Filter songs by names, albums and artists.
#
#  author: ramr

#
#  Copyright 2024 ramr
#
#  License: See https://github.com/ramr/songsmith/blob/master/LICENSE
#

from typing import Any, Dict

import pandas

from songsmith.logger import LOG


FILTER_COLUMNS_MAP = {"songs": "Name", "albums": "Album",
                     "artists": "Artist",
                    }


def _filter(df: pandas.DataFrame, filters: Dict[str, Any]) -> pandas.DataFrame:
    """ Select rows in a pandas dataframe based on `filters`. """
    zdf = df.copy(deep=True)

    if not filters or not isinstance(filters, dict):
        return zdf

    for k, v in filters.items():
        if k in FILTER_COLUMNS_MAP:
            column = FILTER_COLUMNS_MAP[k]
            zdf = zdf[zdf[column].str.contains(v, case=False, na=False)]
        else:
            LOG.info("No mapping for filter %s: %s, ignoring it ...", k, v)
            continue

    return zdf


def _generate(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """ Generate a pandas dataframe pattern filter. """
    filters = dict.fromkeys(list(FILTER_COLUMNS_MAP.keys()), [])

    def _convert(value: str) -> str:
        """ Convert criteria to a pandas dataframe pattern filter. """
        if not value or len(value) == 0:
            return ""

        filters = []

        for v in value.split("|"):
            pieces = [p for p in v.split(" ") if len(p) > 0]
            filters.append(".*".join(pieces))

        return "|".join(filters)


    #  Generate filters - convert the criteria to a pandas usable filter.
    for k, v in criteria.items():
        if k in filters:
            LOG.info("Generating filter %s ...", k)
            filters[k] = _convert(v)
        else:
            LOG.info("Ignoring unsupported criteria %s: %s", k, v)

    return filters


def apply(df: pandas.DataFrame, criteria: Dict[str, Any]) -> pandas.DataFrame:
    """ Applies the criteria to the pandas dataframe. """
    if df is None or not isinstance(df, pandas.DataFrame):
        return None

    if not criteria or not isinstance(criteria, dict):
        return df

    LOG.info("Generating filters ...")
    filters = _generate(criteria)

    LOG.info("Applying filters %s ...", filters)
    filtered_df = _filter(df, filters)

    LOG.info("Applied filters, returning data.")
    return filtered_df
