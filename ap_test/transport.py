# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

from datetime import datetime
import logging

import requests

log = logging.getLogger(__name__)

PROFILE_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'
ACTIVITY_TYPE = "application/activity+json"


def default_headers() -> dict[str, str]:
    return {
        "Accept-Charset": "utf-8",
        "Date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S"),
        "User-Agent": "ap-testsuite",
    }


def get_headers(with_profile: bool = False) -> dict[str, str]:
    return default_headers() | {
        "Accept": PROFILE_TYPE if with_profile else ACTIVITY_TYPE,
    }


def post_headers() -> dict[str, str]:
    return default_headers() | {"Content-Type": PROFILE_TYPE}


def get(iri: str, with_profile: bool = False):
    log.info("GET %s", iri)
    r = requests.get(
        iri,
        headers=get_headers(with_profile),
        timeout=30.
    )
    r.raise_for_status()
    return r.json()
