"""Toy solver: random-restart 2-opt local search on a generated Euclidean TSP instance.

This stands in for a real solver in the g5k-kickstart example. What it demonstrates
is the WORKER CONTRACT, which any real solver should follow too:

- fully determined by CLI arguments (instance, seed, time limit, output path);
- deterministic instance generation from the instance name (no data files to ship);
- logs reproducibility metadata (hostname, timestamps, parameters) into the result;
- writes the result to a temp file in the output directory and renames it into
  place at the end, so the output tree never contains partial files.

Usage:
    python -m example_experiment.solver --instance rnd-n050-i03 --seed 42 \
        --time-limit 5 --output outputs/demo/rnd-n050-i03/seed_00042.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import socket
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def instance_points(instance: str) -> list[tuple[float, float]]:
    """Generate the instance deterministically from its name (e.g. rnd-n050-i03)."""
    n = int(instance.split("-")[1].removeprefix("n"))
    digest = hashlib.sha256(instance.encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    return [(rng.uniform(0, 1000), rng.uniform(0, 1000)) for _ in range(n)]


def tour_length(points: list[tuple[float, float]], tour: list[int]) -> float:
    total = 0.0
    for i, a in enumerate(tour):
        b = tour[(i + 1) % len(tour)]
        total += math.dist(points[a], points[b])
    return total


def nearest_neighbor_tour(points: list[tuple[float, float]], start: int) -> list[int]:
    unvisited = set(range(len(points)))
    unvisited.remove(start)
    tour = [start]
    while unvisited:
        last = points[tour[-1]]
        nxt = min(unvisited, key=lambda j: math.dist(last, points[j]))
        unvisited.remove(nxt)
        tour.append(nxt)
    return tour


def two_opt(points: list[tuple[float, float]], tour: list[int], deadline: float) -> list[int]:
    """First-improvement 2-opt until local optimum or deadline."""
    n = len(tour)
    improved = True
    while improved and time.monotonic() < deadline:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n if i > 0 else n - 1):
                a, b = points[tour[i]], points[tour[i + 1]]
                c, d = points[tour[j]], points[tour[(j + 1) % n]]
                delta = math.dist(a, c) + math.dist(b, d) - math.dist(a, b) - math.dist(c, d)
                if delta < -1e-9:
                    tour[i + 1 : j + 1] = reversed(tour[i + 1 : j + 1])
                    improved = True
            if time.monotonic() >= deadline:
                break
    return tour


def solve(instance: str, seed: int, time_limit: float) -> dict:
    points = instance_points(instance)
    rng = random.Random(seed)
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    deadline = t0 + time_limit

    best_cost = math.inf
    restarts = 0
    while time.monotonic() < deadline:
        tour = nearest_neighbor_tour(points, rng.randrange(len(points)))
        tour = two_opt(points, tour, deadline)
        cost = tour_length(points, tour)
        best_cost = min(best_cost, cost)
        restarts += 1

    return {
        "instance": instance,
        "n": len(points),
        "seed": seed,
        "time_limit_s": time_limit,
        "best_cost": round(best_cost, 3),
        "restarts": restarts,
        "elapsed_s": round(time.monotonic() - t0, 3),
        "hostname": socket.gethostname(),
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_atomically(result: dict, output: Path) -> None:
    """Temp file in the SAME directory, then rename: rename is atomic within a filesystem."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=output.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    os.replace(tmp_path, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance", required=True, help="instance name, e.g. rnd-n050-i03")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--time-limit", type=float, default=5.0, help="seconds per task")
    parser.add_argument("--output", type=Path, required=True, help="result JSON path")
    args = parser.parse_args()

    result = solve(args.instance, args.seed, args.time_limit)
    write_atomically(result, args.output)
    print(f"{args.instance} seed={args.seed}: best={result['best_cost']} restarts={result['restarts']}")


if __name__ == "__main__":
    main()
