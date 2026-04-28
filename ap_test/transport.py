# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

import json
import logging
from datetime import datetime

import requests

from .auth import BaseAuth

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


def get(iri: str, with_profile: bool = False, auth: BaseAuth | None = None):
    log.info("GET %s", iri)
    headers = get_headers(with_profile)
    if auth is not None:
        headers = headers | auth.sign_request("GET", iri, headers, None)
    r = requests.get(iri, headers=headers, timeout=30.0)
    r.raise_for_status()
    return r.json()


def post(iri: str, body: dict, auth: BaseAuth | None = None):
    log.info("POST %s", iri)
    body_bytes = json.dumps(body).encode("utf-8")
    headers = post_headers()
    if auth is not None:
        headers = headers | auth.sign_request("POST", iri, headers, body_bytes)
    r = requests.post(iri, data=body_bytes, headers=headers, timeout=30.0)
    r.raise_for_status()
    return r.json() if r.content else {}
