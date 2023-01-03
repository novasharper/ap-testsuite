# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

try:
    import tomllib as toml
except ImportError:
    import tomli as toml

from typing import Any
from urllib.parse import urljoin, urlparse


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

    def load_config(self, config_file):
        with open(config_file, "rb") as f:
            cfg = toml.load(f)

        any_arg = False
        section = cfg.get("test_config", {})
        server = section.get("server")
        for arg in self.ARGS:
            argv = section.get(arg)
            if arg.endswith("_id") and server and argv:
                argv = urljoin(server, argv)
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
