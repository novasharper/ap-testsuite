# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

import logging
from typing import Any
from urllib.parse import urljoin, urlparse, urlencode

try:
    import tomllib as toml
except ImportError:
    import tomli as toml

import requests

from . import transport

log = logging.getLogger(__name__)


class TestContext:
    ARGS = [
        # Entity IDs
        "actor_id",
        "object_id",
        "deleted_object_id",
        "invalid_object_id",
        "private_object_id",
        # Config
        "use_tombstone",
        "use_forbidden",
    ]

    def __init__(self) -> None:
        self.db = {}
        self.server = None
        # ARGS
        ## Entity IDs
        self.actor_id = None
        self.object_id = None
        self.deleted_object_id = None
        self.invalid_object_id = None
        self.private_object_id = None
        ## Config
        self.use_tombstone = None
        self.use_forbidden = None

    def validate(self, arg: str, argv: Any):
        if argv is None:
            return

        if arg.startswith("use_"):
            if not isinstance(argv, bool):
                raise TypeError(f"value for {arg} must be a boolean")

        elif arg.endswith("_id"):
            if not isinstance(argv, str):
                raise TypeError(f"value for {arg} must be a string")

            # Ensure that arg is a valid url
            urlparse(argv)

    def setarg(self, arg, argv):
        if arg not in self.ARGS:
            raise KeyError(f"Invalid arg {arg}")

        if argv is None and getattr(self, arg, None) is not None:
            return

        self.validate(arg, argv)
        setattr(self, arg, argv)

    def load_opts(self, opt):
        any_arg = False
        for arg in self.ARGS:
            argv = getattr(opt, arg, None)
            any_arg |= bool(argv)
            self.setarg(arg, argv)
        return any_arg

    def load_user(self, user):
        log.info("Loading info for user %s", user)
        query = urlencode({"resource": f"acct:{user}"})
        try:
            info = transport.get(f"{self.server}/.well-known/webfinger?{query}")
        except requests.HTTPError as exc:
            log.error("failed to fetch webfinger info for %s: %s", user, exc)
            return False

        self.actor_id = next(
            link["href"] for link in info["links"] if link["rel"] == "self"
        )
        return True

    def load_config(self, config_file):
        with open(config_file, "rb") as f:
            cfg = toml.load(f)

        any_arg = False
        test_config = cfg.get("test_config", {})
        if "user" in test_config:
            user = test_config["user"]
            if user.count("@") != 1:
                raise ValueError(f"Invalid user account {user}")
            self.server = f"https://{user.split('@')[1]}"
            any_arg |= self.load_user(user)

        else:
            self.server = test_config.get("server")

        if "resources" in test_config:
            resources = test_config["resources"]
            for arg in self.ARGS:
                if arg not in resources:
                    continue
                argv = resources[arg]
                if arg.endswith("_id") and self.server and argv:
                    argv = urljoin(self.server, argv)
                any_arg |= bool(argv)
                self.setarg(arg, argv)

        return any_arg


def get_id(obj) -> str:
    """Get ID for JSON-LD object

    TODO: Implement support for non-href id???
    """
    if "@id" in obj:
        return obj["@id"]
    return obj.get("id")
