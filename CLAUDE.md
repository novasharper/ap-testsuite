# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**ap-testsuite** is a CLI tool for validating ActivityPub (AP) protocol compliance. It approximates the functionality of [go-fed/testsuite](https://github.com/go-fed/testsuite) but in Python. It tests whether a federated server correctly handles actor fetching, object retrieval, deleted/invalid/private object responses, and HTTP status codes.

## Commands

```bash
# Install dependencies
make install       # poetry install --with dev

# Lint
make pylint        # runs pylint on ap_test/

# Format
make format        # runs black on ap_test/

# Run the test suite (after `make install`)
ap-test --config-file testconfig.toml
ap-test --actor-id <URL> --object-id <URL>
ap-test -c testconfig.toml -v        # INFO logging
ap-test -c testconfig.toml -vv       # DEBUG logging
ap-test -c testconfig.toml --failfast
```

There is no unit test suite — the tests *are* the product (AP compliance checks run against a live server).

## Architecture

### Core Components

- **`ap_test/__main__.py`** — CLI entry point. Parses args, builds a `TestContext`, iterates `COMMON_TESTS`, calls `skip()` then `run()` on each. Handles verbosity, failfast, and barrier-separated output.
- **`ap_test/helper.py`** — `TestContext` class. Holds all configuration state (actor_id, object_id, flags). `load_config()` reads a TOML file; `load_opts()` applies CLI overrides. Performs WebFinger lookup when a `user@domain` string is given instead of a URL.
- **`ap_test/transport.py`** — Thin HTTP wrapper. Provides `ACTIVITY_TYPE` and `PROFILE_TYPE` header constants for ActivityPub content negotiation. The `get()` function sets Accept headers and calls `raise_for_status()`.
- **`ap_test/tests.py`** — All test classes. Each subclasses `BaseTest` (which holds `self.ctx`), overrides `run() -> bool` and optionally `skip() -> bool`. `ActorTest` can auto-discover `object_id` and `invalid_object_id` from the actor's outbox.

### Adding a New Test

1. Subclass `BaseTest` in `tests.py`.
2. Override `run()` to return `True` (pass) or `False` (fail); use `self.ctx` for config and `transport.get()` for HTTP calls.
3. Override `skip()` if the test should be conditional on config flags.
4. Append the class to `COMMON_TESTS` in `__main__.py`.

### Configuration

`testconfig.toml` is the canonical example:
```toml
[test_config]
user = 'LWN@fosstodon.org'
# Optional: object_id, invalid_object_id, deleted_object_id, private_object_id
# Flags: use_tombstone (bool), use_forbidden (bool)
```

Config precedence: TOML `[resources]` section → WebFinger-derived values → CLI `--` flags. Relative resource paths are automatically resolved against the configured server base URL.

### Linting

Pylint is configured via `pylint.toml` with `fail-under = 10` (must score 10/10 to pass). CI runs on Python 3.8–3.11 whenever `.py` files are changed.
