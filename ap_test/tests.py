import requests

from .helper import TestContext, get_id
from . import transport


class BaseTest:
    def __init__(self, ctx: TestContext) -> None:
        self.ctx = ctx

    def skip(self) -> bool:
        return False

    def run(self) -> bool:
        raise NotImplementedError


class ActorTest(BaseTest):
    """GET Actor

    Side effects:
    - Adds remote actor to the local database
    """

    def run(self) -> bool:
        try:
            actor = transport.get(self.ctx.actor_id)
        except requests.HTTPError:
            print(f"Failed to get actor {self.ctx.actor_id}")
            return False

        outbox_iri = actor["outbox"]
        try:
            outbox = transport.get(outbox_iri)
        except requests.HTTPError:
            print(f"Failed to get actor outbox {outbox_iri}")
            return False

        t = outbox["type"]
        if t not in ("OrderedCollection", "OrderedCollectionPage"):
            print(f"Invalid outbox type {t}")
            return False

        if t == "OrderedCollectionPage":
            outbox_page_iri = outbox["first"]
            try:
                transport.get(outbox_page_iri)
            except requests.HTTPError:
                print(f"Failed to get actor outbox page {outbox_iri}")
                return False

        return True


class ObjectTest(BaseTest):
    def skip(self) -> bool:
        return not self.ctx.object_id

    def run(self) -> bool:
        try:
            transport.get(self.ctx.object_id)
        except requests.HTTPError as e:
            print(f"Get with profile failed: {e}")
            return False

        try:
            transport.get(self.ctx.object_id, True)
        except requests.HTTPError as e:
            print(f"Get with activity failed: {e}")
            return False

        return True


COMMON_TESTS = [
    ActorTest,
    ObjectTest,
]
