class TestContext:
    def __init__(self) -> None:
        self.db = {}
        # ARGS
        self.actor_id = None
        self.object_id = None


def get_id(obj) -> str:
    """Get ID for JSON-LD object

    TODO: Implement support for non-href id???
    """
    if "@id" in obj:
        return obj["@id"]
    return obj.get("id")
