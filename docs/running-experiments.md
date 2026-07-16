# Running experiments: OAR, GNU parallel, and the three-stage methodology

This is the heart of the kit. The `example/` directory implements everything below with a toy solver; rehearse it there first.

## OAR in five commands

All on the frontend (`ssh <site>.g5k`):

```bash
oarsub -q default -p <cluster> -l host=1,walltime=2 -I             # interactive shell on a node (dies with your terminal)
oarsub -q default -p <cluster> -n mytag -l host=1,walltime=1 "cmd" # batch job; quota-free if <=1h and immediate
oarsub -q default -p <cluster> -l host=4,walltime=14 -r '2026-07-07 19:00'  # advance reservation
oarstat -u $USER                                                   # your jobs (W waiting, L launching, R running)
oardel <JOB_ID>                                                    # cancel / release
```

Extras: `oarstat -f -j <JOB_ID>` shows full detail including `assigned_hostnames`; `oarwalltime <JOB_ID> +2:00` extends a running job; exotic clusters need `-t exotic`; batch job output lands in `OAR.<JOB_ID>.stdout/.stderr` in the submission directory.

To get a shell **inside** a reservation (with the environment needed for distributed launches):

```bash
oarsub -C <JOB_ID>
```

This sets `$OAR_NODEFILE`, a file with one line per reserved CPU core. Plain `ssh <node>` to a node you own works for inspection but does not set `$OAR_NODEFILE`; distributed launches must go through `oarsub -C`. Never hand-craft a nodefile from `oarstat` output: GNU parallel will hang without the OAR cpuset context.

## The experiment pattern

When you need to run a set of configurations A on a set of instances I:

1. **One command per task.** Generate one worker command line for each (a, i) pair (plus seed, time limit, ...). The worker writes its result to a temp file first and renames it into place at the end, so the output tree never contains partial files:
   ```bash
   TMP=$(mktemp -p outputs/.tmp); solver <params> instances/i.txt > "$TMP" && mv "$TMP" outputs/a/i.json
   ```
   The worker should log everything useful for analysis and reproducibility: date, seed, hostname, parameters, code version.
2. **Resume by output file.** Before generating commands, skip every task whose output file already exists. A rerun after a crash or an expired walltime picks up exactly where the campaign stopped. Caveat: a task killed mid-run loses its own progress (only whole output files count), so size walltimes with margin.
3. **Dispatch with GNU parallel:**
   ```bash
   parallel --workdir . -j <jobs> --joblog run.joblog --progress :::: commands.txt                     # local
   parallel --workdir . -j <jobs-per-host> --joblog run.joblog --ssh oarsh --slf "$OAR_NODEFILE" :::: commands.txt   # on g5k
   ```

**The one flag that will burn you**: with `--slf`, `-j N` means N jobs **per host**, not in total. Pass the per-host core count (e.g. 18 on an 18-core node), never the total slot count, or every node runs len(hosts) times too many workers.

## The three-stage methodology

Never launch a campaign cold. Escalate through:

### Stage 1: dry run (anywhere, free)

The runner prints every worker command line and the exact `parallel` invocation, and executes nothing. Read a few command lines end to end. Check the task count, the output paths, the resume filter ("skipping K existing").

### Stage 2: smoke run

First locally on your machine with a handful of tasks (`--limit 4`): outputs appear, parse, and a rerun skips them. Then on g5k with a quota-free immediate job:

```bash
oarsub -q default -p <cluster> -n smoke -l host=1,walltime=1 "sleep infinity"
oarsub -C <JOB_ID>
# inside the job:
wc -l "$OAR_NODEFILE"; sort -u "$OAR_NODEFILE" | wc -l   # slots and hosts sanity check
bash scripts/launch_example.sh --limit 20
```

Watch the joblog grow, check `Exitval` is 0 everywhere, confirm the result files land. Release the job (`oardel`) when done if walltime remains.

### Stage 3: full run (night or weekend)

Reserve for the real size, e.g. `oarsub -q default -p <cluster> -n sweep -l host=4,walltime=14 -r '<date> 19:00'`. Estimate first: tasks x time-per-task / (hosts x cores-per-host), then add 30-50% margin. At start time, attach and launch through `nohup` so the run survives the shell:

```bash
nohup bash scripts/launch_example.sh > run.log 2>&1 &
```

An agent can do the attach-and-launch non-interactively from your machine (note `-tt`, a single `-t` fails):

```bash
ssh -tt <site>.g5k "bash -lc 'oarsub -C <JOB_ID>'" << 'EOF'
cd ~/my-experiments
bash scripts/launch_example.sh
exit
EOF
```

## Monitoring a running campaign

From your machine, over SSH:

```bash
ssh <site>.g5k 'tail -n 20 ~/my-experiments/run.log'          # launcher log
ssh <site>.g5k 'wc -l ~/my-experiments/run.joblog'            # completed tasks (rows grow)
ssh <site>.g5k "awk 'NR>1 && \$7!=0' ~/my-experiments/run.joblog | wc -l"   # non-zero exit codes (want 0)
ssh <site>.g5k 'find ~/my-experiments/outputs -name "*.json" | wc -l'       # results landed
```

Gotchas learned the hard way:

- `ulimit -n 8192` before large parallel runs (the example launcher does it); GNU parallel over many hosts keeps many file descriptors open.
- **NFS rename race**: never rename or move a log file that a node-side `nohup` process just created. The writer keeps the old inode and the "moved" log silently stops updating. Monitor via the joblog instead.
- Workers must not rely on an interactive environment (modules, venv activation). Either build self-contained artifacts (`-static-libstdc++`, `uv run`), or wrap each command as `bash -lc '. ./env.sh && exec ...'`.
- If a job stays `W` for more than a few minutes during the day, the cluster is busy: `oardel` it and retry smaller, or fall back to a night reservation. Check the load Gantt at `https://intranet.grid5000.fr/oar/<Site>/drawgantt-svg/`.

## After the run

Sync back, verify, delete remote outputs, release leftover reservations. Full protocol in `storage-and-sync.md`.
