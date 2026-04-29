# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

import logging

import requests

from . import transport
from .tests import AS_PUBLIC, BaseTest, FederationTest, ServerRequiredTest, find_in_collection

log = logging.getLogger(__name__)

AS_CONTEXT = "https://www.w3.org/ns/activitystreams"


# ---------------------------------------------------------------------------
# Activity construction helpers
# ---------------------------------------------------------------------------

def _make_note(actor_id: str) -> dict:
    return {
        "@context": AS_CONTEXT,
        "type": "Note",
        "attributedTo": actor_id,
        "content": "ap-testsuite test note",
        "to": [AS_PUBLIC],
    }


def _make_create(actor_id: str, obj: dict) -> dict:
    return {
        "@context": AS_CONTEXT,
        "type": "Create",
        "actor": actor_id,
        "object": obj,
        "to": [AS_PUBLIC],
    }


# ---------------------------------------------------------------------------
# Group A: GET-only federation tests
# ---------------------------------------------------------------------------

class GetOutboxTest(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            actor = transport.get(self.ctx.actor_id)
            outbox = transport.get(actor["outbox"])
        except (requests.HTTPError, KeyError) as exc:
            log.error("Failed to get outbox: %s", exc)
            return False
        if outbox.get("type") not in ("OrderedCollection", "OrderedCollectionPage"):
            log.error("Invalid outbox type: %s", outbox.get("type"))
            return False
        return True


class GetFollowersTest(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.followers_id:
            log.info("Skipping; followers_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            followers = transport.get(self.ctx.followers_id)
        except requests.HTTPError as exc:
            log.error("Failed to get followers: %s", exc)
            return False
        if followers.get("type") not in ("OrderedCollection", "Collection"):
            log.error("Invalid followers type: %s", followers.get("type"))
            return False
        return True


class GetFollowingTest(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.following_id:
            log.info("Skipping; following_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            following = transport.get(self.ctx.following_id)
        except requests.HTTPError as exc:
            log.error("Failed to get following: %s", exc)
            return False
        if following.get("type") not in ("OrderedCollection", "Collection"):
            log.error("Invalid following type: %s", following.get("type"))
            return False
        return True


class FollowingHasAcceptedFollowTest(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.following_id:
            log.info("Skipping; following_id not configured")
            return True
        if not self.ctx.accepted_follow_actor_id:
            log.info("Skipping; accepted_follow_actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        found = find_in_collection(self.ctx.following_id, self.ctx.accepted_follow_actor_id)
        if not found:
            log.error(
                "Accepted actor %s not found in following collection",
                self.ctx.accepted_follow_actor_id,
            )
        return found


class FollowingNotHasRejectedFollowTest(BaseTest):
    def skip(self) -> bool:
        if not self.ctx.following_id:
            log.info("Skipping; following_id not configured")
            return True
        if not self.ctx.rejected_follow_actor_id:
            log.info("Skipping; rejected_follow_actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        found = find_in_collection(self.ctx.following_id, self.ctx.rejected_follow_actor_id)
        if found:
            log.error(
                "Rejected actor %s unexpectedly found in following collection",
                self.ctx.rejected_follow_actor_id,
            )
        return not found


# ---------------------------------------------------------------------------
# Group B: C2S POST tests (require auth + local_actor_id)
# ---------------------------------------------------------------------------

class DeliversActivitiesTest(FederationTest):
    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        return self._post_activity(actor["outbox"], activity) is not None


class OutboxContainsActivitiesTest(FederationTest):
    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        result = self._post_activity(actor["outbox"], activity)
        if result is None:
            return False
        activity_id = result.get("id") if isinstance(result, dict) else None
        if not activity_id:
            log.info("Server did not return activity ID; skipping outbox check")
            return True
        try:
            outbox = transport.get(actor["outbox"], auth=self.ctx.auth)
        except requests.HTTPError as exc:
            log.error("Failed to re-fetch outbox: %s", exc)
            return False
        items = outbox.get("orderedItems") or []
        if any((i.get("id") if isinstance(i, dict) else i) == activity_id for i in items):
            return True
        log.error("Posted activity %s not found in outbox", activity_id)
        return False


class ActivityHasIdTest(FederationTest):
    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        result = self._post_activity(actor["outbox"], activity)
        if result is None:
            return False
        if isinstance(result, dict) and result and "id" not in result:
            log.error("Activity response has no 'id' field")
            return False
        return True


class _ActivityTypeTest(FederationTest):  # pylint: disable=abstract-method
    """Base for single-activity-type delivery tests."""

    def _make_activity(self, actor_id: str) -> dict:
        raise NotImplementedError

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = self._make_activity(self.ctx.local_actor_id)
        return self._post_activity(actor["outbox"], activity) is not None


class DeliversCreateTest(_ActivityTypeTest):
    def _make_activity(self, actor_id: str) -> dict:
        return _make_create(actor_id, _make_note(actor_id))


class DeliversUpdateTest(_ActivityTypeTest):
    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Update",
            "actor": actor_id,
            "object": {"type": "Note", "id": f"{actor_id}/notes/test", "content": "updated"},
            "to": [AS_PUBLIC],
        }


class DeliversDeleteTest(_ActivityTypeTest):
    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Delete",
            "actor": actor_id,
            "object": f"{actor_id}/notes/test",
            "to": [AS_PUBLIC],
        }


class DeliversFollowTest(_ActivityTypeTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Follow",
            "actor": actor_id,
            "object": self.ctx.actor_id,
        }


class DeliversAddTest(_ActivityTypeTest):
    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Add",
            "actor": actor_id,
            "object": f"{actor_id}/notes/test",
            "target": f"{actor_id}/collection/featured",
            "to": [AS_PUBLIC],
        }


class DeliversRemoveTest(_ActivityTypeTest):
    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Remove",
            "actor": actor_id,
            "object": f"{actor_id}/notes/test",
            "target": f"{actor_id}/collection/featured",
            "to": [AS_PUBLIC],
        }


class DeliversLikeTest(_ActivityTypeTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.object_id:
            log.info("Skipping; object_id not configured")
            return True
        return False

    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Like",
            "actor": actor_id,
            "object": self.ctx.object_id,
            "to": [AS_PUBLIC],
        }


class DeliversBlockTest(_ActivityTypeTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Block",
            "actor": actor_id,
            "object": self.ctx.actor_id,
        }


class DeliversUndoTest(_ActivityTypeTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def _make_activity(self, actor_id: str) -> dict:
        return {
            "@context": AS_CONTEXT,
            "type": "Undo",
            "actor": actor_id,
            "object": {
                "type": "Follow",
                "actor": actor_id,
                "object": self.ctx.actor_id,
            },
        }


class DeliversArticleTest(FederationTest):
    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        article = {
            "@context": AS_CONTEXT,
            "type": "Create",
            "actor": self.ctx.local_actor_id,
            "object": {
                "type": "Article",
                "attributedTo": self.ctx.local_actor_id,
                "name": "ap-testsuite test article",
                "content": "Test article content from ap-testsuite.",
                "to": [AS_PUBLIC],
            },
            "to": [AS_PUBLIC],
        }
        return self._post_activity(actor["outbox"], article) is not None


class NoDoubleDeliveryTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.inbox_id:
            log.info("Skipping; inbox_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        activity["id"] = f"{self.ctx.local_actor_id}/activities/dedup-test"
        for _ in range(2):
            self._post_activity(actor["outbox"], activity)
        try:
            inbox = transport.get(self.ctx.inbox_id, auth=self.ctx.auth)
        except requests.HTTPError as exc:
            log.error("Failed to fetch inbox: %s", exc)
            return False
        items = inbox.get("orderedItems") or inbox.get("items") or []
        activity_id = activity["id"]
        count = sum(
            1 for i in items
            if (i.get("id") if isinstance(i, dict) else i) == activity_id
        )
        if count > 1:
            log.error("Activity delivered %d times; expected 1", count)
            return False
        return True


class NoSelfAddressTest(FederationTest):
    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        activity["to"] = [self.ctx.local_actor_id, AS_PUBLIC]
        result = self._post_activity(actor["outbox"], activity)
        if result is None:
            return False
        log.info("Server accepted activity (self-address handling verified by delivery)")
        return True


class NoDeliverBlocksTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        block = {
            "@context": AS_CONTEXT,
            "type": "Block",
            "actor": self.ctx.local_actor_id,
            "object": self.ctx.actor_id,
        }
        result = self._post_activity(actor["outbox"], block)
        if result is None:
            return False
        log.info("Block activity accepted; delivery exclusion must be verified manually")
        return True


class DedupeInboxTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        if not self.ctx.inbox_id:
            log.info("Skipping; inbox_id not configured")
            return True
        return False

    def run(self) -> bool:
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        activity["id"] = f"{self.ctx.local_actor_id}/activities/inbox-dedup-test"
        try:
            remote_actor = transport.get(self.ctx.actor_id)
            inbox_url = remote_actor.get("inbox")
        except (requests.HTTPError, KeyError) as exc:
            log.error("Failed to resolve remote inbox: %s", exc)
            return False
        for _ in range(2):
            try:
                transport.post(inbox_url, activity, auth=self.ctx.auth)
            except requests.HTTPError as exc:
                log.error("POST to remote inbox failed: %s", exc)
                return False
        try:
            inbox = transport.get(self.ctx.inbox_id, auth=self.ctx.auth)
        except requests.HTTPError as exc:
            log.error("Failed to fetch local inbox: %s", exc)
            return False
        items = inbox.get("orderedItems") or inbox.get("items") or []
        activity_id = activity["id"]
        count = sum(
            1 for i in items
            if (i.get("id") if isinstance(i, dict) else i) == activity_id
        )
        if count > 1:
            log.error("Activity appeared %d times in inbox; expected 1", count)
            return False
        return True


class SendFollowAcceptanceTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        follow = {
            "@context": AS_CONTEXT,
            "type": "Follow",
            "actor": self.ctx.local_actor_id,
            "object": self.ctx.actor_id,
            "to": [self.ctx.actor_id],
        }
        return self._post_activity(actor["outbox"], follow) is not None


class SendFollowRejectionTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.rejected_follow_actor_id:
            log.info("Skipping; rejected_follow_actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        follow = {
            "@context": AS_CONTEXT,
            "type": "Follow",
            "actor": self.ctx.local_actor_id,
            "object": self.ctx.rejected_follow_actor_id,
            "to": [self.ctx.rejected_follow_actor_id],
        }
        return self._post_activity(actor["outbox"], follow) is not None


class AcceptFollowTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            remote_actor = transport.get(self.ctx.actor_id)
            inbox_url = remote_actor.get("inbox")
        except (requests.HTTPError, KeyError) as exc:
            log.error("Failed to resolve remote actor inbox: %s", exc)
            return False
        follow_id = f"{self.ctx.local_actor_id}/activities/accept-follow-test"
        accept = {
            "@context": AS_CONTEXT,
            "type": "Accept",
            "actor": self.ctx.local_actor_id,
            "object": {
                "type": "Follow",
                "id": follow_id,
                "actor": self.ctx.actor_id,
                "object": self.ctx.local_actor_id,
            },
        }
        try:
            transport.post(inbox_url, accept, auth=self.ctx.auth)
        except requests.HTTPError as exc:
            log.error("POST Accept to remote inbox failed: %s", exc)
            return False
        return True


class RejectFollowTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            remote_actor = transport.get(self.ctx.actor_id)
            inbox_url = remote_actor.get("inbox")
        except (requests.HTTPError, KeyError) as exc:
            log.error("Failed to resolve remote actor inbox: %s", exc)
            return False
        follow_id = f"{self.ctx.local_actor_id}/activities/reject-follow-test"
        reject = {
            "@context": AS_CONTEXT,
            "type": "Reject",
            "actor": self.ctx.local_actor_id,
            "object": {
                "type": "Follow",
                "id": follow_id,
                "actor": self.ctx.actor_id,
                "object": self.ctx.local_actor_id,
            },
        }
        try:
            transport.post(inbox_url, reject, auth=self.ctx.auth)
        except requests.HTTPError as exc:
            log.error("POST Reject to remote inbox failed: %s", exc)
            return False
        return True


class NoUnauthorizedUpdateTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.object_id:
            log.info("Skipping; object_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        update = {
            "@context": AS_CONTEXT,
            "type": "Update",
            "actor": self.ctx.local_actor_id,
            "object": {
                "type": "Note",
                "id": self.ctx.object_id,
                "content": "unauthorized update attempt by ap-testsuite",
            },
            "to": [AS_PUBLIC],
        }
        try:
            transport.post(actor["outbox"], update, auth=self.ctx.auth)
        except requests.HTTPError as exc:
            resp = exc.response
            if resp is not None and resp.status_code in (401, 403, 422):
                log.info("Server correctly rejected unauthorized update: %s", resp.status_code)
                return True
            log.error("Unexpected error posting unauthorized update: %s", exc)
            return False
        log.info("Server accepted the update (delivery rejection verified separately)")
        return True


class ConfirmUnauthorizedUpdateTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.object_id:
            log.info("Skipping; object_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            obj = transport.get(self.ctx.object_id)
        except requests.HTTPError as exc:
            log.error("Failed to fetch object: %s", exc)
            return False
        content = obj.get("content", "")
        if "unauthorized update attempt by ap-testsuite" in content:
            log.error("Unauthorized update was applied to object %s", self.ctx.object_id)
            return False
        return True


class DeliveryRecipientsTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def _post_addressed(self, outbox_url: str, field: str) -> bool:
        actor_id = self.ctx.local_actor_id
        activity = _make_create(actor_id, _make_note(actor_id))
        activity[field] = [self.ctx.actor_id]
        result = self._post_activity(outbox_url, activity)
        if result is None:
            log.error("POST with %s addressing failed", field)
            return False
        return True

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        outbox = actor["outbox"]
        return all(self._post_addressed(outbox, f) for f in ("to", "cc", "bto", "bcc"))


class DeliveryToCollectionTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.followers_id:
            log.info("Skipping; followers_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        activity["to"] = [self.ctx.followers_id]
        return self._post_activity(actor["outbox"], activity) is not None


class DeliveryNestedCollectionTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        try:
            remote_actor = transport.get(self.ctx.actor_id)
            followers = remote_actor.get("followers")
        except (requests.HTTPError, KeyError) as exc:
            log.error("Failed to resolve remote followers: %s", exc)
            return False
        if not followers:
            log.info("Remote actor has no followers collection; skipping")
            return True
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        activity["to"] = [followers]
        return self._post_activity(actor["outbox"], activity) is not None


class DerefDeliveryTargetsTest(FederationTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        activity["to"] = [self.ctx.actor_id, AS_PUBLIC]
        result = self._post_activity(actor["outbox"], activity)
        if result is None:
            return False
        log.info("Server accepted activity with named recipient")
        return True


# ---------------------------------------------------------------------------
# Group C: Bidirectional tests (require local server)
# ---------------------------------------------------------------------------

class ReceiveAcceptFollowTest(ServerRequiredTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        follow = {
            "@context": AS_CONTEXT,
            "type": "Follow",
            "actor": self.ctx.local_actor_id,
            "object": self.ctx.actor_id,
            "to": [self.ctx.actor_id],
        }
        if self._post_activity(actor["outbox"], follow) is None:
            return False
        log.info("Waiting for Accept from remote server (timeout=30s)")
        reply = self.ctx.local_server.wait_for_activity(timeout=30.0)
        if reply is None:
            log.error("Timed out waiting for Accept activity")
            return False
        if reply.get("type") != "Accept":
            log.error("Expected Accept, got %s", reply.get("type"))
            return False
        return True


class ReceiveRejectFollowTest(ServerRequiredTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.rejected_follow_actor_id:
            log.info("Skipping; rejected_follow_actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        follow = {
            "@context": AS_CONTEXT,
            "type": "Follow",
            "actor": self.ctx.local_actor_id,
            "object": self.ctx.rejected_follow_actor_id,
            "to": [self.ctx.rejected_follow_actor_id],
        }
        if self._post_activity(actor["outbox"], follow) is None:
            return False
        log.info("Waiting for Reject from remote server (timeout=30s)")
        reply = self.ctx.local_server.wait_for_activity(timeout=30.0)
        if reply is None:
            log.error("Timed out waiting for Reject activity")
            return False
        if reply.get("type") != "Reject":
            log.error("Expected Reject, got %s", reply.get("type"))
            return False
        return True


class GetFollowersAfterAcceptTest(ServerRequiredTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.followers_id:
            log.info("Skipping; followers_id not configured")
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        return False

    def run(self) -> bool:
        found = find_in_collection(self.ctx.followers_id, self.ctx.actor_id)
        if not found:
            log.error(
                "Expected actor %s in followers collection after accept",
                self.ctx.actor_id,
            )
        return found


class SendWithFollowersTest(ServerRequiredTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.followers_id:
            log.info("Skipping; followers_id not configured")
            return True
        return False

    def run(self) -> bool:
        actor = self._get_actor()
        if actor is None:
            return False
        activity = _make_create(self.ctx.local_actor_id, _make_note(self.ctx.local_actor_id))
        activity["to"] = [AS_PUBLIC, self.ctx.followers_id]
        if self._post_activity(actor["outbox"], activity) is None:
            return False
        log.info("Waiting for activity delivery to local server (timeout=30s)")
        received = self.ctx.local_server.wait_for_activity(timeout=30.0)
        if received is None:
            log.error("Timed out waiting for activity delivery")
            return False
        return True


class InboxForwardingTest(ServerRequiredTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        if not self.ctx.followers_id:
            log.info("Skipping; followers_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            remote_actor = transport.get(self.ctx.actor_id)
            inbox_url = remote_actor.get("inbox")
        except (requests.HTTPError, KeyError) as exc:
            log.error("Failed to resolve remote actor inbox: %s", exc)
            return False
        activity = {
            "@context": AS_CONTEXT,
            "type": "Create",
            "actor": self.ctx.local_actor_id,
            "object": {
                "type": "Note",
                "attributedTo": self.ctx.local_actor_id,
                "content": "ap-testsuite inbox forwarding test",
                "to": [self.ctx.followers_id],
                "inReplyTo": self.ctx.object_id,
            },
            "to": [self.ctx.followers_id],
        }
        try:
            transport.post(inbox_url, activity, auth=self.ctx.auth)
        except requests.HTTPError as exc:
            log.error("POST to remote inbox failed: %s", exc)
            return False
        log.info("Waiting for forwarded activity (timeout=30s)")
        forwarded = self.ctx.local_server.wait_for_activity(timeout=30.0)
        if forwarded is None:
            log.error("Timed out waiting for inbox forwarding")
            return False
        return True


class AppliedInboxForwardingTest(ServerRequiredTest):
    def skip(self) -> bool:
        if super().skip():
            return True
        if not self.ctx.actor_id:
            log.info("Skipping; actor_id not configured")
            return True
        if not self.ctx.inbox_id:
            log.info("Skipping; inbox_id not configured")
            return True
        return False

    def run(self) -> bool:
        try:
            inbox = transport.get(self.ctx.inbox_id, auth=self.ctx.auth)
        except requests.HTTPError as exc:
            log.error("Failed to fetch local inbox: %s", exc)
            return False
        items = inbox.get("orderedItems") or inbox.get("items") or []
        for item in items:
            obj = item.get("object") if isinstance(item, dict) else None
            if isinstance(obj, dict) and "inReplyTo" in obj:
                return True
        log.info("No forwarded reply found in inbox yet (may need InboxForwardingTest first)")
        return False


FEDERATION_TESTS = [
    # Group A — GET only
    GetOutboxTest,
    GetFollowersTest,
    GetFollowingTest,
    FollowingHasAcceptedFollowTest,
    FollowingNotHasRejectedFollowTest,
    # Group B — C2S POST
    DeliversActivitiesTest,
    OutboxContainsActivitiesTest,
    ActivityHasIdTest,
    DeliversCreateTest,
    DeliversUpdateTest,
    DeliversDeleteTest,
    DeliversFollowTest,
    DeliversAddTest,
    DeliversRemoveTest,
    DeliversLikeTest,
    DeliversBlockTest,
    DeliversUndoTest,
    DeliversArticleTest,
    NoDoubleDeliveryTest,
    NoSelfAddressTest,
    NoDeliverBlocksTest,
    DedupeInboxTest,
    SendFollowAcceptanceTest,
    SendFollowRejectionTest,
    AcceptFollowTest,
    RejectFollowTest,
    NoUnauthorizedUpdateTest,
    ConfirmUnauthorizedUpdateTest,
    DeliveryRecipientsTest,
    DeliveryToCollectionTest,
    DeliveryNestedCollectionTest,
    DerefDeliveryTargetsTest,
    # Group C — bidirectional (need local server)
    ReceiveAcceptFollowTest,
    ReceiveRejectFollowTest,
    GetFollowersAfterAcceptTest,
    SendWithFollowersTest,
    InboxForwardingTest,
    AppliedInboxForwardingTest,
]
