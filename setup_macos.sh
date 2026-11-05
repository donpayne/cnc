#!/bin/sh
# Installs the Knight's Fusion script and tests the check scripts. Safe to run again.
set -eu
cd "$(dirname "$0")"

# On a Mac without developer tools, python3 exists but only prompts to install them.
if ! python3 --version >/dev/null 2>&1; then
    echo "Python 3 is required. Install it from https://www.python.org/downloads/ and run this again." >&2
    exit 1
fi
exec python3 -B setup_fusion.py
