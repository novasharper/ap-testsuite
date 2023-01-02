#!/usr/bin/env python3

import argparse as ap
import logging

from ap_test.helper import TestContext
from ap_test.tests import BaseTest, COMMON_TESTS


def run_tests(tests: list[BaseTest], failfast: bool = False):
    def _log(msg):
        print(f"==== {msg} ====")

    for test in tests:
        test_name = test.__class__.__name__
        if test.skip():
            _log(f"Skipping {test_name}")
            continue

        _log(f"Running {test_name}")
        passed = test.run()
        status = "passed" if passed else "failed"
        _log(f"Test {test_name} {status}")
        if failfast and not passed:
            return False

    return True


def main():
    parser = ap.ArgumentParser("ap-test")
    parser.add_argument("--config-file", "-c")
    parser.add_argument("-v", dest="verbosity", action="count")
    parser.add_argument("--failfast", "-x", action="store_true")
    for arg in TestContext.ARGS:
        parser.add_argument(f'--{arg.replace("_", "-")}')
    opt = parser.parse_args()

    if opt.verbosity:
        logging.basicConfig(
            level=logging.INFO if opt.verbosity == 1 else logging.DEBUG,
            format="%(name)-24s: %(levelname)-8s %(message)s",
        )

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
    run_tests(
        [tc(ctx) for tc in COMMON_TESTS],
        failfast=opt.failfast,
    )


if __name__ == "__main__":
    main()
