#!/usr/bin/env python3
"""Compatibility entry point for adding a Git or skills.sh skill source."""

import sys

from skills import main


if __name__ == "__main__":
    sys.argv.insert(1, "add")
    raise SystemExit(main())
