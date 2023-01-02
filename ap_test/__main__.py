#!/usr/bin/env python3

import argparse as ap

from ap_test.helper import TestContext
from ap_test.tests import BaseTest, COMMON_TESTS


def run_tests(tests: list[BaseTest]):
    for test in tests:
        if test.skip():
            print(f"Skipping {test.__class__.__name__}")
            continue

        result = test.run()
        status = "passed" if result else "failed"
        print(f"Test {test.__class__.__name__} {status}")


def main():
    parser = ap.ArgumentParser("ap-test")
    parser.add_argument("--actor-id", required=True)
    parser.add_argument("--object-id")
    opt = parser.parse_args()

    ctx = TestContext()
    ctx.actor_id = opt.actor_id
    ctx.object_id = opt.object_id

    run_tests([tc(ctx) for tc in COMMON_TESTS])
