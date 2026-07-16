"""Experiment runner: build one worker command per (instance, seed) task and dispatch.

Demonstrates the three ideas any campaign runner needs:

- task enumeration: instances x seeds, one self-contained command line each;
- resume: tasks whose output file already exists are skipped, so a rerun after a
  crash or an expired reservation picks up where the campaign stopped;
- staged execution: --dry-run prints everything and runs nothing, --limit N runs
  a small sample, no flag runs the full remainder.

Usage examples (from the example/ directory, after `uv sync`):
    .venv/bin/python -m example_experiment.runner --dry-run
    .venv/bin/python -m example_experiment.runner --limit 4 --jobs 2
    .venv/bin/python -m example_experiment.runner --tag full_run
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from example_experiment.parallel_backend import on_g5k, run_gnu_parallel_commands

EXAMPLE_DIR = Path(__file__).resolve().parents[2]
WORKER_PYTHON = ".venv/bin/python"


def build_tasks(sizes: list[int], instances_per_size: int, seeds: list[int]) -> list[tuple[str, int]]:
    tasks = []
    for n in sizes:
        for i in range(1, instances_per_size + 1):
            instance = f"rnd-n{n:03d}-i{i:02d}"
            for seed in seeds:
                tasks.append((instance, seed))
    return tasks


def output_path(output_dir: Path, instance: str, seed: int) -> Path:
    return output_dir / instance / f"seed_{seed:05d}.json"


def worker_command(instance: str, seed: int, time_limit: float, output: Path) -> str:
    return " ".join(
        [
            WORKER_PYTHON,
            "-m",
            "example_experiment.solver",
            "--instance",
            instance,
            "--seed",
            str(seed),
            "--time-limit",
            str(time_limit),
            "--output",
            shlex.quote(str(output)),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sizes", default="20,50", help="comma-separated instance sizes")
    parser.add_argument("--instances-per-size", type=int, default=5)
    parser.add_argument("--seeds", default="1,2,3,4", help="comma-separated seeds")
    parser.add_argument("--time-limit", type=float, default=3.0, help="seconds per task")
    parser.add_argument("--tag", default="demo", help="run name, groups outputs under outputs/<tag>")
    parser.add_argument("--dry-run", action="store_true", help="print commands, run nothing")
    parser.add_argument("--limit", type=int, default=None, help="run at most N pending tasks")
    parser.add_argument("--jobs", type=int, default=None, help="local parallel jobs (ignored on g5k: per-host slots are derived from $OAR_NODEFILE)")
    args = parser.parse_args()

    sizes = [int(s) for s in args.sizes.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    output_dir = EXAMPLE_DIR / "outputs" / args.tag

    tasks = build_tasks(sizes, args.instances_per_size, seeds)
    pending = [(inst, seed) for inst, seed in tasks if not output_path(output_dir, inst, seed).exists()]
    skipped = len(tasks) - len(pending)
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"Tasks: {len(tasks)} total, {skipped} already done (skipped), {len(pending)} to run")
    print(f"Backend: {'G5K ($OAR_NODEFILE detected)' if on_g5k() else 'local'}")

    commands = [
        worker_command(inst, seed, args.time_limit, output_path(output_dir, inst, seed))
        for inst, seed in pending
    ]

    if args.dry_run:
        for cmd in commands:
            print(cmd)
        print(f"[dry-run] {len(commands)} command(s) printed, nothing executed.")
        return

    if not commands:
        print("Nothing to do.")
        return

    status = run_gnu_parallel_commands(
        commands,
        workdir=EXAMPLE_DIR,
        temp_dir=EXAMPLE_DIR / ".cache" / "parallel",
        n_jobs=args.jobs,
    )
    sys.exit(status)


if __name__ == "__main__":
    main()
