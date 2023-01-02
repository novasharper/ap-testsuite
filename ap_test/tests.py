import logging

import requests

from .helper import TestContext, get_id
from . import transport

log = logging.getLogger(__name__)


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

    def skip(self) -> bool:
        if not self.ctx.actor_id:
            log.info("Skipping; Actor ID not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            log.info("Dereference Actor")
            actor = transport.get(self.ctx.actor_id)
        except requests.HTTPError:
            log.error(f"Failed to get actor {self.ctx.actor_id}")
            return False

        outbox_iri = actor["outbox"]
        try:
            log.info("Dereference Actor outbox")
            outbox = transport.get(outbox_iri)
        except requests.HTTPError:
            log.error(f"Failed to get actor outbox {outbox_iri}")
            return False

        log.info("Validate outbox type")
        t = outbox["type"]
        if t not in ("OrderedCollection", "OrderedCollectionPage"):
            log.error(f"Invalid outbox type {t}")
            return False

        if t == "OrderedCollection":
            log.info(
                "Outbox was a collection, dereference + validate "
                "referenced page type"
            )
            outbox_page_iri = outbox["first"]
            try:
                transport.get(outbox_page_iri)
            except requests.HTTPError:
                log.error(f"Failed to get actor outbox page {outbox_iri}")
                return False

        return True


class ObjectTest(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.object_id:
            log.info("Skipping; Object ID not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            log.info("Dereference object (accept=activity+json)")
            transport.get(self.ctx.object_id)
        except requests.HTTPError as e:
            log.error(f"Get with profile failed: {e}")
            return False

        try:
            log.info("Dereference object (accept=ld+json, profile specified)")
            transport.get(self.ctx.object_id, True)
        except requests.HTTPError as e:
            log.error(f"Get with activity failed: {e}")
            return False

        return True


COMMON_TESTS = [
    ActorTest,
    ObjectTest,
]
