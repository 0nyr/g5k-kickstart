# Example experiment: rehearse the full g5k workflow with a toy solver

A miniature but complete experiment campaign: a stdlib-only Python "solver" (random-restart 2-opt on generated TSP instances), a runner that enumerates (instance, seed) tasks and dispatches them with GNU parallel, and launch/sync scripts for Grid'5000. Nothing here needs real benchmark data or dependencies; instances are generated deterministically from their names.

The point is to rehearse the methodology end to end (dry run, local smoke run, g5k smoke run, full run, sync back, clean up) before you touch real experiments. Default settings define 40 tasks of 3 s each, so every stage is cheap.

## What the code demonstrates

- **Worker contract** (`src/example_experiment/solver.py`): fully determined by CLI args, logs hostname/timestamps/params into the result, writes JSON via temp-file-then-rename so no partial outputs ever land.
- **Runner** (`src/example_experiment/runner.py`): task enumeration, resume-by-existing-output-file, `--dry-run` / `--limit N` / full staging.
- **Parallel backend** (`src/example_experiment/parallel_backend.py`): GNU parallel locally, or across reserved nodes via `--ssh oarsh --slf $OAR_NODEFILE`, with the critical per-host `-j` handling.
- **Launcher** (`scripts/launch_example.sh`): OAR-attach checks, `ulimit`, `nohup` so the run survives the SSH session.
- **Sync-back** (`scripts/sync_results_back.sh`): rsync results home, with the verify-then-delete checklist.

## Stage 0: bootstrap

Locally and (later) on the g5k frontend, from this `example/` directory:

```bash
uv sync            # creates .venv and installs the package (needs uv, see docs/getting-started.md)
```

GNU parallel must be on the PATH for real runs (`parallel --version`). It is preinstalled on g5k; locally install it via your package manager (on NixOS: `nix shell nixpkgs#parallel`).

## Stage 1: dry run (runs nothing)

```bash
.venv/bin/python -m example_experiment.runner --dry-run
```

Expect: "Tasks: 40 total, 0 already done (skipped), 40 to run", backend "local", then 40 worker command lines. Read a couple end to end.

## Stage 2a: local smoke run

```bash
.venv/bin/python -m example_experiment.runner --limit 4 --jobs 2
find outputs/demo -name '*.json' | wc -l     # expect 4
.venv/bin/python -m example_experiment.runner --limit 4 --jobs 2   # expect "4 already done", runs 4 MORE pending tasks
```

Check a result: `cat outputs/demo/rnd-n020-i01/seed_00001.json`. The resume mechanism is the "already done (skipped)" counter.

## Stage 2b: g5k smoke run (daytime, quota-free)

On the frontend (`ssh <site>.g5k`), clone this repo and bootstrap (Stage 0). Then:

```bash
oarsub -q default -p <cluster> -n kickstart-smoke -l host=1,walltime=1 "sleep infinity"
oarsub -C <JOB_ID>
# now inside the job:
cd ~/g5k-kickstart/example
wc -l "$OAR_NODEFILE"                          # one line per reserved core
bash scripts/launch_example.sh --limit 20 --tag smoke
tail -f run.log                                # G5K mode banner, progress, exit status 0
oardel <JOB_ID>                                # release the remaining walltime when done
```

## Stage 3: "full" run on several nodes

For the rehearsal, scale the workload up a bit and reserve 2 nodes for an hour (still quota-free if immediate, or use a night reservation to practice Mode B):

```bash
oarsub -q default -p <cluster> -n kickstart-full -l host=2,walltime=1 "sleep infinity"
oarsub -C <JOB_ID>
cd ~/g5k-kickstart/example
bash scripts/launch_example.sh --sizes 20,50,100 --instances-per-size 10 --seeds 1,2,3,4,5 --tag full_run
```

Monitor from your own machine:

```bash
ssh <site>.g5k 'tail -n 5 g5k-kickstart/example/run.log'
ssh <site>.g5k 'find g5k-kickstart/example/outputs/full_run -name "*.json" | wc -l'   # climbs to 150
```

## Stage 4: sync back and clean up

From your own machine, in this directory:

```bash
bash scripts/sync_results_back.sh <site> full_run
```

Then follow the printed verify-then-delete steps, release any reservation still held (`oardel`), and audit the remote home (`ssh <site>.g5k 'du -sh ~/* | sort -rh | head'`). That is the whole discipline; `../docs/storage-and-sync.md` has the details.
