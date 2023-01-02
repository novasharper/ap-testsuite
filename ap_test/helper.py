try:
    import tomllib as toml
except ImportError:
    import tomli as toml

from urllib.parse import urljoin


class TestContext:
    ARGS = [
        "actor_id",
        "object_id",
    ]

    def __init__(self) -> None:
        self.db = {}
        self.set_default_args()

    def set_default_args(self):
        for arg in self.ARGS:
            setattr(self, arg, None)

    def setdefault(self, arg, argv):
        if arg not in self.ARGS:
            raise KeyError(f"Invalid arg {arg}")

        if getattr(self, arg, None) is not None:
            return

        setattr(self, arg, argv)

    def load_opts(self, opt):
        any_arg = False
        for arg in self.ARGS:
            argv = getattr(opt, arg, None)
            any_arg |= bool(argv)
            self.setdefault(arg, argv)
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
            self.setdefault(arg, argv)

        return any_arg


def get_id(obj) -> str:
    """Get ID for JSON-LD object

    TODO: Implement support for non-href id???
    """
    if "@id" in obj:
        return obj["@id"]
    return obj.get("id")
