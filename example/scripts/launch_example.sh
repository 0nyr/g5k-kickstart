#!/usr/bin/env bash
# Launch the example experiment inside an active OAR reservation.
# Run this INSIDE `oarsub -C <JOB_ID>` (never on the frontend).
#
# Usage: bash scripts/launch_example.sh [extra runner args, e.g. --limit 20]
#
# The real workload is nohup'd so it survives this shell (and the SSH session)
# exiting; monitor via the printed log file and the GNU-parallel joblog.
set -euo pipefail

if [ -z "${OAR_NODEFILE:-}" ]; then
    echo "ERROR: OAR_NODEFILE is not set. Attach to a reservation first (oarsub -C <JOB_ID>)." >&2
    exit 1
fi

EXAMPLE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$EXAMPLE_DIR"

if [ ! -x .venv/bin/python ]; then
    echo "ERROR: no .venv in $EXAMPLE_DIR. Bootstrap first: uv sync (see example/README.md)." >&2
    exit 1
fi

# GNU parallel over many hosts keeps many file descriptors open.
ulimit -n 8192

LOG="$EXAMPLE_DIR/run.log"
nohup .venv/bin/python -m example_experiment.runner "$@" > "$LOG" 2>&1 &
echo "PID: $!"
echo "Log: $LOG"
echo "Monitor: tail -f $LOG"
