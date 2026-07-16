# Worked example: a MAMUT-routing solver campaign on nancy/gros

A concrete, end-to-end narrative of how a real campaign for the [MAMUT-routing](https://github.com/MAMUT-routing) collaboration (time-dependent vehicle routing benchmarks, solved with tools like [KAYROS](https://github.com/0nyr/kayros)) runs on Grid'5000. Replace names and numbers with your own; the shape is what matters.

## Why nancy/gros

The `gros` cluster at nancy (~120 identical nodes, 1 CPU x 18 cores, 96 GiB RAM, SSD, no GPU) is ideal for single-thread solver sweeps dispatched with GNU parallel: many homogeneous cores, no `-t exotic` flag, and enough nodes that reasonable reservations schedule easily. Check the current load before planning: https://intranet.grid5000.fr/oar/Nancy/drawgantt-svg/

## The campaign

Goal: run the solver on 300 benchmark instances x 10 seeds with a 600 s time limit per run.

Budget: 3000 tasks x 600 s = 500 core-hours. On 18-core gros nodes that is about 28 node-hours, so a reservation of **4 nodes x 8 h** (72 parallel slots, 32 node-hours) covers it with margin for stragglers and startup.

## Step 0: bootstrap (once, on the frontend)

```bash
ssh nancy.g5k
git clone git@github.com:<org>/<experiment-repo>.git my-experiments   # needs the GitHub key from docs/getting-started.md
cd my-experiments
curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.local/bin/env
uv sync --frozen
# any C++ component: module load gcc/13.2.0_gcc-10.4.0, build with -static-libstdc++
```

## Step 1: dry run

```bash
uv run python -m <runner> --dry-run
```

Read the printed worker commands and the `parallel` invocation. Task count, output paths and the resume filter must all look right. Do this locally first, then again on the frontend (a dry run is preparation, so it is frontend-legal).

## Step 2: smoke run (daytime, quota-free)

```bash
oarsub -q default -p gros -n mamut-smoke -l host=1,walltime=1 "sleep infinity"
oarsub -C <JOB_ID>
# inside the job:
wc -l "$OAR_NODEFILE"                # expect 18 (one line per core)
bash scripts/launch.sh --limit 20    # 20 real tasks through the full stack
tail -f run.log                      # then check the joblog and the 20 output JSONs
oardel <JOB_ID>                      # release the rest of the hour
```

Rerun `--limit 20` once: it must skip all 20 ("resume" proof).

## Step 3: the reservation

A weeknight 19:00 start keeps the whole window inside the 14 h cap:

```bash
oarsub -q default -p gros -n mamut-sweep -l host=4,walltime=8 -r '2026-07-16 19:00'
```

Note the `JOB_ID` and report it to your collaborators (or your human, if you are an agent). Check it appears in `oarstat -u $USER` with state `W`.

## Step 4: launch at 19:00

From your own machine, non-interactively (this is how an agent does it; `-tt` is mandatory):

```bash
ssh -tt nancy.g5k "bash -lc 'oarsub -C <JOB_ID>'" << 'EOF'
cd ~/my-experiments
bash scripts/launch.sh
exit
EOF
```

The launcher checks `$OAR_NODEFILE`, raises `ulimit -n`, and `nohup`s the runner so the run survives the shell exiting.

## Step 5: monitor overnight

```bash
ssh nancy.g5k 'tail -n 5 ~/my-experiments/run.log'
ssh nancy.g5k 'wc -l ~/my-experiments/run.joblog'                              # rows ~ completed tasks
ssh nancy.g5k 'find ~/my-experiments/outputs/sweep -name "*.json" | wc -l'     # results landed
```

If it will not finish in time, extend while the job still lives: `ssh nancy.g5k 'oarwalltime <JOB_ID> +2:00'` (check the 9:00 boundary first). If the job dies anyway, nothing is lost beyond in-flight tasks: the next launch resumes from the existing output files.

## Step 6: wrap up (morning after)

```bash
rsync -az --info=progress2 nancy.g5k:my-experiments/outputs/sweep/ ./outputs/sweep/
# verify counts and sizes on both sides, spot-check JSONs parse (see docs/storage-and-sync.md)
ssh nancy.g5k 'rm -rf my-experiments/outputs/sweep'
ssh nancy.g5k 'oarstat -u $USER'      # nothing left running or waiting
ssh nancy.g5k 'du -sh ~/* 2>/dev/null | sort -rh | head'
```

Done: 3000 results in the local tree, a lean remote home, no idle reservations, and a campaign you can rerun or extend with one command thanks to the resume mechanism.

The `../example/` directory is a miniature runnable version of exactly this workflow with a toy solver; rehearse there before your first real campaign.
