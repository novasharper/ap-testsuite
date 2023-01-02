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
    parser.add_argument("--config-file", "-c")
    for arg in TestContext.ARGS:
        parser.add_argument(f'--{arg.replace("_", "-")}')
    opt = parser.parse_args()

    ctx = TestContext()
    loaded = False
    if opt.config_file:
        loaded = ctx.load_config(opt.config_file)
    loaded |= ctx.load_opts(opt)

    if not loaded:
        print("No config passed.")
        print()
        print("Either pass config using arguments or via a TOML config file.")
        return

    print("=== RUNNING BASE TESTS ===")
    run_tests([tc(ctx) for tc in COMMON_TESTS])


if __name__ == "__main__":
    main()
