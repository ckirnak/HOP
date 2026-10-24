#!/bin/sh
# Run from an extracted HOP source archive on the PBX.
set -eu
cd "$(dirname "$0")"
exec python3 backend/setup.py "$@"
