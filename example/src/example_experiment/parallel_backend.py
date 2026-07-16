"""Dispatch a list of shell commands through GNU parallel, locally or on Grid'5000.

On Grid'5000 the OAR scheduler writes one line per reserved CPU core to
``$OAR_NODEFILE``. GNU parallel's ``--slf`` reads that file (unique hostname =
remote host, duplicate lines = job slots on that host) and ``--ssh oarsh`` uses
OAR's SSH wrapper. CRITICAL: with ``--slf``, ``-j N`` means N jobs PER HOST,
not in total, so we pass the per-host slot count, never the total (passing the
total oversubscribes every node by a factor of len(hosts)).
"""

from __future__ import annotations

import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path


def get_g5k_host_file() -> str | None:
    return os.getenv("OAR_NODEFILE")


def on_g5k() -> bool:
    return get_g5k_host_file() is not None


def get_g5k_slots_per_host() -> dict[str, int]:
    host_file = get_g5k_host_file()
    if host_file is None:
        return {}
    counts: dict[str, int] = {}
    with open(host_file) as f:
        for line in f:
            host = line.strip()
            if host:
                counts[host] = counts.get(host, 0) + 1
    return counts


def build_parallel_command(
    commands: list[str],
    *,
    workdir: Path,
    temp_dir: Path,
    n_jobs: int | None = None,
) -> tuple[str, Path, Path]:
    """Write the command file and assemble the parallel invocation (without running it)."""
    temp_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
    cfg_path = temp_dir / f"{timestamp}.cfg"
    with open(cfg_path, "w") as f:
        for command in commands:
            f.write(f"{command}\n")

    log_path = temp_dir / f"{timestamp}.joblog"

    g5k_extra = ""
    jobs_flag = f"-j {n_jobs}" if n_jobs is not None else ""
    host_file = get_g5k_host_file()
    if host_file:
        g5k_extra = f"--ssh oarsh --slf {shlex.quote(host_file)}"
        slots_per_host = get_g5k_slots_per_host()
        total_slots = sum(slots_per_host.values())
        # Per-host job cap (see module docstring); min over hosts if heterogeneous.
        per_host = min(slots_per_host.values())
        jobs_flag = f"-j {per_host}"
        print(
            f"G5K mode: {len(slots_per_host)} host(s), {total_slots} total CPU slots "
            f"(-j {per_host} per-host)"
        )
        for host, slots in sorted(slots_per_host.items()):
            print(f"  {host}: {slots} slots")

    parallel_cmd = " ".join(
        part
        for part in [
            "parallel",
            f"--workdir {shlex.quote(str(workdir))}",
            jobs_flag,
            f"--joblog {shlex.quote(str(log_path))}",
            "--progress",
            g5k_extra,
            f":::: {shlex.quote(str(cfg_path))}",
        ]
        if part
    )
    return parallel_cmd, cfg_path, log_path


def run_gnu_parallel_commands(
    commands: list[str],
    *,
    workdir: Path,
    temp_dir: Path,
    n_jobs: int | None = None,
) -> int:
    """Run command lines through GNU parallel locally or on G5K; return exit status."""
    parallel_cmd, _, log_path = build_parallel_command(
        commands, workdir=workdir, temp_dir=temp_dir, n_jobs=n_jobs
    )
    print(f"Running: {parallel_cmd}", flush=True)
    print(f"Joblog:  {log_path}", flush=True)
    completed = subprocess.run(parallel_cmd, shell=True, check=False)
    print(f"GNU parallel exited with status {completed.returncode}")
    return completed.returncode
