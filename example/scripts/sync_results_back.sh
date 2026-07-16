#!/usr/bin/env bash
# Pull example-run results from a g5k site back into the local outputs tree.
# Run LOCALLY (on your own machine).
#
# Usage: bash scripts/sync_results_back.sh [site] [tag] [remote_example_dir]
#   site               g5k SSH alias prefix (default: nancy)
#   tag                run name used with --tag  (default: demo)
#   remote_example_dir path of example/ in the remote home (default: g5k-kickstart/example)
set -euo pipefail

SITE="${1:-nancy}"
TAG="${2:-demo}"
REMOTE_DIR="${3:-g5k-kickstart/example}"
EXAMPLE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

rsync -az --info=progress2 \
    "$SITE.g5k:$REMOTE_DIR/outputs/$TAG/" \
    "$EXAMPLE_DIR/outputs/$TAG/"

echo "Synced to $EXAMPLE_DIR/outputs/$TAG"
echo
echo "Now VERIFY before deleting anything remote:"
echo "  find $EXAMPLE_DIR/outputs/$TAG -type f | wc -l"
echo "  ssh $SITE.g5k 'find $REMOTE_DIR/outputs/$TAG -type f | wc -l'"
echo "Then delete the remote copy:"
echo "  ssh $SITE.g5k 'rm -rf $REMOTE_DIR/outputs/$TAG'"
