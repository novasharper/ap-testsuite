# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

import logging
import tomllib as toml
from typing import Any
from urllib.parse import urljoin, urlparse, urlencode

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
        # Federation entity IDs
        "local_actor_id",
        "inbox_id",
        "followers_id",
        "following_id",
        "accepted_follow_actor_id",
        "rejected_follow_actor_id",
        # Config
        "use_tombstone",
        "use_forbidden",
    ]

    def __init__(self) -> None:
        self.db = {}
        self.server = None
        # Entity IDs
        self.actor_id = None
        self.object_id = None
        self.deleted_object_id = None
        self.invalid_object_id = None
        self.private_object_id = None
        # Federation entity IDs
        self.local_actor_id = None
        self.inbox_id = None
        self.followers_id = None
        self.following_id = None
        self.accepted_follow_actor_id = None
        self.rejected_follow_actor_id = None
        # Config flags
        self.use_tombstone = None
        self.use_forbidden = None
        # Auth + local server (populated by load_config, not CLI)
        self.auth = None
        self.local_server = None

    @property
    def has_local_server(self) -> bool:
        return self.local_server is not None

    def validate(self, arg: str, argv: Any):
        if argv is None:
            return

        if arg.startswith("use_"):
            if not isinstance(argv, bool):
                raise TypeError(f"value for {arg} must be a boolean")

        elif arg.endswith("_id"):
            if not isinstance(argv, str):
                raise TypeError(f"value for {arg} must be a string")

            parsed = urlparse(argv)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(f"value for {arg} must be a valid http/https URL, got {argv!r}")

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

        link = next(
            (link for link in info.get("links", []) if link.get("rel") == "self"),
            None,
        )
        if link is None:
            log.error("No self link found in webfinger response for %s", user)
            return False
        self.actor_id = link["href"]
        return True

    def _load_auth_config(self, test_config: dict):
        if "auth" not in test_config:
            return
        from .auth import load_auth  # pylint: disable=import-outside-toplevel
        auth_cfg = test_config["auth"]
        if "actor_id" not in auth_cfg and self.local_actor_id:
            auth_cfg = auth_cfg | {"actor_id": self.local_actor_id}
        self.auth = load_auth(auth_cfg)

    def _load_server_config(self, test_config: dict):
        if "local_server" not in test_config:
            return
        from .server import InboxServer  # pylint: disable=import-outside-toplevel
        srv = test_config["local_server"]
        self.local_server = InboxServer(
            port=srv.get("port", 0),
            public_url=srv.get("public_url"),
            auth=self.auth,
        )

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

        self._load_auth_config(test_config)
        self._load_server_config(test_config)

        return any_arg
