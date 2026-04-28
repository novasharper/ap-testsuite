# Copyright (c) 2023 Pat Long
# SPDX-License-Identifier: MIT

import http.server
import json
import logging
import queue
import threading

log = logging.getLogger(__name__)


class InboxServer:
    def __init__(self, port: int = 0, public_url: str | None = None, auth=None) -> None:
        self._port = port
        self._public_url = public_url
        self._auth = auth
        self._queue: queue.Queue = queue.Queue()
        self._httpd: http.server.HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        activity_queue = self._queue

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    activity = json.loads(body)
                except json.JSONDecodeError:
                    self.send_response(400)
                    self.end_headers()
                    return
                activity_queue.put(activity)
                self.send_response(202)
                self.end_headers()

            def log_message(self, fmt, *args):  # pylint: disable=arguments-differ
                log.debug("InboxServer: " + fmt, *args)

        self._httpd = http.server.HTTPServer(("", self._port), Handler)
        self._port = self._httpd.socket.getsockname()[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        log.info("InboxServer started on port %d", self._port)

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            if self._thread:
                self._thread.join(timeout=5.0)
            self._httpd = None
            self._thread = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    @property
    def inbox_url(self) -> str:
        return self._public_url or f"http://localhost:{self._port}/inbox"

    def wait_for_activity(self, timeout: float = 30.0) -> dict | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
