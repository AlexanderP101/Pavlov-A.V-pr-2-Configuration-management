#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m apkgraph "$@"
