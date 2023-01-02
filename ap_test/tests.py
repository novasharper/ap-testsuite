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


class DeletedObject(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.deleted_object_id:
            log.info("Skipping; Deleted Object ID not configured")
            return True
        return False

    def run(self) -> bool:
        expected_code = (
            requests.codes.gone if self.ctx.use_tombstone else requests.codes.not_found
        )
        try:
            log.info("Dereference deleted object")
            transport.get(self.ctx.deleted_object_id)
            log.error(
                "Successfully fetched the object. "
                "Are you sure you specified the correct object id?"
            )
            return False
        except requests.HTTPError as e:
            resp: requests.Response = e.response
            if resp.status_code != expected_code:
                log.error(
                    "Invalid status code %s; expected %s",
                    resp.status_code,
                    expected_code,
                )
                return False
        return True


class InvalidObject(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.invalid_object_id:
            log.info("Skipping; Invalid Object ID not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            log.info("Dereference invalid object")
            transport.get(self.ctx.invalid_object_id)
            log.error(
                "Successfully fetched the object. "
                "Are you sure you specified the correct object id?"
            )
            return False
        except requests.HTTPError as e:
            resp: requests.Response = e.response
            if resp.status_code != requests.codes.not_found:
                log.error(
                    "Invalid status code %s; expected %s",
                    resp.status_code,
                    requests.codes.not_found,
                )
                return False
        return True


class PrivateObject(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.private_object_id:
            log.info("Skipping; Private Object ID not configured")
            return True
        return False

    def run(self) -> bool:
        expected_code = (
            requests.codes.forbidden
            if self.ctx.use_forbidden
            else requests.codes.not_found
        )
        try:
            log.info("Dereference private object")
            transport.get(self.ctx.private_object_id)
            log.error(
                "Successfully fetched the object. "
                "Are you sure you specified the correct object id?"
            )
            return False
        except requests.HTTPError as e:
            resp: requests.Response = e.response
            if resp.status_code != expected_code:
                log.error(
                    "Invalid status code %s; expected %s",
                    resp.status_code,
                    expected_code,
                )
                return False
        return True


COMMON_TESTS = [
    ActorTest,
    ObjectTest,
    DeletedObject,
    InvalidObject,
    PrivateObject,
]
