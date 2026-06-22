#!/usr/bin/env python3
"""Compatibility entry point for syncing registered skills."""

import sys

from skills import main


if __name__ == "__main__":
    sys.argv.insert(1, "sync")
    raise SystemExit(main())
