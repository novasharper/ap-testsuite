# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

import base64
import hashlib
import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

log = logging.getLogger(__name__)


class BaseAuth:  # pylint: disable=too-few-public-methods
    def sign_request(self, method: str, url: str, headers: dict, body: bytes | None) -> dict:
        raise NotImplementedError


class BearerTokenAuth(BaseAuth):  # pylint: disable=too-few-public-methods
    def __init__(self, token: str) -> None:
        self._token = token

    def sign_request(self, method, url, headers, body) -> dict:
        return {"Authorization": f"Bearer {self._token}"}


class CookieAuth(BaseAuth):  # pylint: disable=too-few-public-methods
    def __init__(self, cookie: str) -> None:
        self._cookie = cookie

    def sign_request(self, method, url, headers, body) -> dict:
        return {"Cookie": self._cookie}


class HttpSignatureAuth(BaseAuth):  # pylint: disable=too-few-public-methods
    def __init__(self, actor_id: str, private_key_pem: str | bytes) -> None:
        self._key_id = f"{actor_id}#main-key"
        if isinstance(private_key_pem, str):
            private_key_pem = private_key_pem.encode()
        self._private_key = serialization.load_pem_private_key(private_key_pem, password=None)

    def _digest_header(self, body: bytes) -> str:
        return "SHA-256=" + base64.b64encode(hashlib.sha256(body).digest()).decode()

    def sign_request(self, method: str, url: str, headers: dict, body: bytes | None) -> dict:
        date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        parsed = urlparse(url)
        path = parsed.path + (f"?{parsed.query}" if parsed.query else "")

        signed = ["(request-target)", "host", "date"]
        parts = [
            f"(request-target): {method.lower()} {path}",
            f"host: {parsed.netloc}",
            f"date: {date}",
        ]
        extra = {"Date": date}

        if body:
            digest = self._digest_header(body)
            signed.append("digest")
            parts.append(f"digest: {digest}")
            extra["Digest"] = digest

        sig = self._private_key.sign(
            "\n".join(parts).encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        extra["Signature"] = (
            f'keyId="{self._key_id}",algorithm="rsa-sha256",'
            f'headers="{" ".join(signed)}",'
            f'signature="{base64.b64encode(sig).decode()}"'
        )
        return extra


def load_auth(config: dict) -> BaseAuth | None:
    auth_type = config.get("type")
    if auth_type == "bearer":
        return BearerTokenAuth(config["token"])
    if auth_type == "cookie":
        return CookieAuth(config["cookie"])
    if auth_type == "http_signature":
        actor_id = config["actor_id"]
        with open(config["private_key_file"], "rb") as fh:
            pem = fh.read()
        return HttpSignatureAuth(actor_id, pem)
    if auth_type is None:
        return None
    raise ValueError(f"Unknown auth type: {auth_type!r}")


def build_activity(activity_type: str, actor_id: str, obj: dict | str, **kwargs) -> dict:
    activity = {
        "type": activity_type,
        "actor": actor_id,
        "object": obj,
    }
    activity.update(kwargs)
    return activity


def build_note(actor_id: str, content: str, **kwargs) -> dict:
    note = {
        "type": "Note",
        "attributedTo": actor_id,
        "content": content,
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
    }
    note.update(kwargs)
    return note


def encode_body(body: dict) -> bytes:
    return json.dumps(body).encode("utf-8")
