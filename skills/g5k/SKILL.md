---
name: g5k
description: Operating Grid'5000 (g5k) for experiment campaigns. Covers OAR reservations, the day/night usage policy, autonomous daytime iteration jobs for AI agents, non-interactive run patterns over SSH, GNU-parallel distributed runs, monitoring, syncing results back, and home-directory cleanup. Use whenever work involves Grid5000 (any site alias like nancy.g5k or lyon.g5k), reserving nodes, launching or monitoring runs, extending or releasing reservations, syncing outputs, or planning an experiment campaign.
---

# g5k: Grid'5000 operations

[Grid'5000](https://www.grid5000.fr/w/Grid5000:Home) is a French large-scale testbed for experiment-driven research in computer science. Concretely, it is a set of sites (Nancy, Lyon, Rennes, Grenoble, ...), each hosting one or more clusters of bare-metal machines that you reserve through the OAR scheduler and use to run algorithmic experiments.

Authoritative external docs: [Getting Started](https://www.grid5000.fr/w/Getting_Started), [Usage Policy](https://www.grid5000.fr/w/Grid5000:UsagePolicy), [Hardware](https://www.grid5000.fr/w/Hardware). This repository's `docs/` folder holds the longer human-readable guides; `example/` holds a runnable end-to-end example experiment.

## User configuration (fill this in)

Adapt every command in this skill with the values below. If you are an agent and these are not filled in, ask the user before touching g5k.

- **Login**: `<login>` (your Grid'5000 account name)
- **Project**: `<project>` (the g5k project/team your account belongs to)
- **Primary site / cluster**: `<site>` / `<cluster>` (e.g. `nancy` / `gros`; pick from [Hardware](https://www.grid5000.fr/w/Hardware) based on what your experiments need)
- **SSH aliases**: `~/.ssh/config` entries so that `ssh <site>.g5k` works (see `docs/getting-started.md`)

For the MAMUT-routing collaboration, the recommended defaults are site `nancy`, cluster `gros` (see the worked example at the end).

## Golden rules (non-negotiable)

1. **Never run compute on the frontend** (the machine you land on after `ssh <site>.g5k`, e.g. `fnancy`). The frontend is a shared gateway for preparation only: git, rsync, edits, environment bootstrap, light builds. All experiments run inside an OAR job. Running heavy background processes on the frontend violates the usage policy and can get the account restricted. If a reservation expires mid-run, stop and relaunch under a new job; never "finish it on the frontend".
   The policy also prohibits running VS Code Server, AI extensions, or background AI agents/LLMs **on** g5k machines. The intended setup is out of that rule's scope by construction: agents (Claude Code, Codex, ...) run on the user's own machine and drive g5k remotely over SSH, on the user's behalf, strictly as an experiment testbed. Nothing agent- or LLM-shaped ever executes on g5k itself. Keep it that way: never install or launch an agent, LLM runtime, or IDE server on a frontend or node.
2. **Weekday jobs must not cross the 9:00 and 19:00 boundaries.** Exceptions: a job submitted at or after 17:00 may cross 19:00 (the 17:00 to 19:00 portion is quota-free); a same-day submission may cross 9:00 (the after-9:00 portion counts against the day quota).
3. **Day = small-scale, night/weekend = campaigns.** Daytime quota (Mon-Fri 9:00-19:00, excluding French public holidays): the equivalent of 2 hours on all cores of the cluster, per user per day. On a 100+ node cluster that is a generous 200+ node-hours, so a few short multi-node jobs sit far below the ceiling; the binding constraints are the boundary rules and courtesy toward other users. Max job length is 14 h on weeknights (19:00 to 9:00) and 62 h on weekends (Friday 19:00 to Monday 9:00).
4. **Reserved-but-idle time still counts as usage.** Release unused reservations promptly (`oardel`), don't hoard nodes, and check `oarstat -u $USER` for zombie jobs at session start and end. There is no hard cap on the number of concurrent reservations; usage is governed by the quota and boundary rules, not a job count. Still, don't hoard.
5. **Keep the remote home lean.** Repos, venvs and dependencies live there; accumulated experiment outputs do not. Temporarily crossing GiB comfort levels during a campaign is fine as long as it does not last: sync results back, verify, then delete remote outputs (protocol below).
6. **Self-audit when in doubt**: `usagepolicycheck -t` (current usage), `usagepolicycheck -l --sites <site>` (violations), `usagepolicycheck -v --start '... +0100' --end '...'` (a time range).

## Agent operating modes

### Mode A: daytime iteration (agents may do this autonomously)

For smoke tests, microbenchmarks, build validation and small sweeps during 9:00-19:00, on `<cluster>`:

- **Preferred: quota-free short jobs.** Jobs of walltime <= 1 h submitted less than 10 minutes before start are **excluded from daily quotas**. An immediate submission qualifies:
  ```bash
  oarsub -q default -p <cluster> -n agent-smoke -l host=1,walltime=1 "sleep infinity"
  ```
  (`sleep infinity` holds the job so you can attach; the job dies at walltime. Or pass the real command directly for a batch run.)
- **Need more time?** Extensions of <= 1 h requested less than 10 minutes before the job ends are also quota-free and renewable several times: `oarwalltime <JOB_ID> +1:00`. Use this to keep an iteration node alive across a debugging session, but this is for iterating, not for smuggling a campaign into the day.
- **Multi-node during the day** is legal (the quota is generous) but stay modest: up to 10 nodes and 2 h autonomously; anything larger or longer, propose the `oarsub` line to the user first. Always name agent jobs (`-n <tag>`) so they are auditable.
- Never let a day job cross 19:00 unless it was submitted at or after 17:00 the same day. Compute the walltime accordingly before submitting.
- If an immediate job stays `W` (Waiting) for more than a few minutes the cluster is busy: `oardel` it, check the load, and either retry smaller or fall back to Mode B. Cluster load Gantt: `https://intranet.grid5000.fr/oar/<Site>/drawgantt-svg/` (browser; from the frontend, `oarstat | wc -l` gives a rough feel).

### Mode B: overnight / weekend campaigns

Large sweeps wait for night or weekend reservations. Agents may place them autonomously whenever a planned campaign needs one, but **always report the `oarsub` line and the resulting `JOB_ID` to the user right away**, and double-check the walltime against the boundary rules before submitting (a weeknight 19:00 start caps at 14 h; only a Friday-evening start may go long):

```bash
# weeknight: 19:00 -> 9:00 is exactly the 14 h maximum
oarsub -q default -p <cluster> -l host=20,walltime=14 -r '2026-07-07 19:00'
# weekend: up to 62 h from Friday 19:00
oarsub -q default -p <cluster> -l host=20,walltime=62 -r '2026-07-10 19:00'
```

Then poll `oarstat -u $USER` until state `R`, attach, launch, monitor. Extending a live reservation: `oarwalltime <JOB_ID> +7:00` (large extensions may be queued for approval; check with `oarwalltime <JOB_ID>` alone). A reservation can be reused across sessions while it lives.

## OAR cheatsheet

Run on the frontend (`ssh <site>.g5k`):

```bash
oarsub -q default -p <cluster> -l host=1,walltime=2 -I            # interactive (dies with the shell)
oarsub -q default -p <cluster> -n tag -l host=1,walltime=1 "cmd"  # batch: runs cmd on the first node, quota-free if <=1h & immediate
oarsub -q default -p <cluster> -l host=20,walltime=14 -r '2026-07-07 19:00'   # advance reservation
oarsub -q default -t exotic -p <exotic-cluster> -l host=1,walltime=5 -r '...' # exotic clusters need -t exotic
oarsub -C <JOB_ID>       # attach a shell INSIDE the job (sets $OAR_NODEFILE); needs a tty, see below
oarstat -u $USER         # my jobs (S column: W waiting, L launching, R running)
oarstat -f -j <JOB_ID>   # full detail incl. assigned_hostnames
oarwalltime <JOB_ID> +2:00   # extend
oardel <JOB_ID>              # release / cancel
```

Notes: `-p <cluster>` selects the cluster; plain `ssh <node>` from the frontend reaches a node you own but does **not** set `$OAR_NODEFILE`, so distributed launches must go through `oarsub -C`. Never hand-craft `$OAR_NODEFILE` from `oarstat` output: GNU parallel will hang without the OAR cpuset context.

## Non-interactive patterns (how an agent drives g5k from the user's machine)

Everything below runs from the local machine; no human terminal needed.

Frontend one-liners:

```bash
ssh <site>.g5k 'oarstat -u $USER'
ssh <site>.g5k 'cd ~/my-experiments && du -sh outputs/'
```

Attach to a reservation and launch (the validated heredoc pattern; `-tt` is mandatory, a single `-t` fails):

```bash
ssh -tt <site>.g5k "bash -lc 'oarsub -C <JOB_ID>'" << 'EOF'
cd ~/my-experiments
bash scripts/launch_example.sh
exit
EOF
```

The launcher must `nohup ... &` its real workload so it survives the shell exiting; the heredoc `exit` cleanly leaves the OAR shell and SSH.

Fire-and-forget alternative for simple single-node day runs: pass the command directly to `oarsub "..."` (stdout/stderr land in `OAR.<JOB_ID>.stdout/.stderr` in the submission directory).

## Running distributed experiments

The validated stack (see `example/` in this repository): one worker command per run, dispatched by GNU parallel with `--ssh oarsh --slf $OAR_NODEFILE`, resume-by-existing-output-file, tmp-file-then-rename writes so no partial outputs ever land in the results tree.

- Verify the attach before launching: `wc -l "$OAR_NODEFILE"` (slots) and `sort -u "$OAR_NODEFILE" | wc -l` (hosts).
- Always `--dry-run` first; the expected worker command lines and the full `parallel` invocation must print.
- **`-j N` with `--slf` means N jobs PER HOST, not in total.** Pass the per-host core count, never the total slot count, or you oversubscribe every node.
- `ulimit -n 8192` before large parallel runs (the launcher does it).
- Launch with `nohup ... > run.log 2>&1 &`; monitor with `tail -f run.log`, the GNU-parallel joblog (rows grow, `Exitval` stays 0), and output-file counts (`find <outdir> -name '*.json' | wc -l`).
- **NFS rename race**: never rename or move a log file that a node-side `nohup` just created; the writer keeps the old inode and the "moved" log goes silent. Monitor via the joblog instead.
- Workers must not rely on an interactive environment: wrap as `bash -lc '. ./env.sh && exec ...'` when a module/runtime env is needed, or build self-contained binaries (see gotchas).
- If the job runs out of walltime before a started worker finishes, that worker's progress is lost; the resume mechanism only skips fully written outputs. Size the walltime with margin.

## Storage hygiene & cleanup protocol

Home dirs are per-site NFS shares with quotas (view them at https://api.grid5000.fr/stable/users/). The home is shared between the frontend and the nodes of the same site, not across sites. Frontend `/tmp` is small and shared: **never** use it (a full `/tmp` breaks ssh-agent for everyone); use `~/tmp` or a repo-local `.cache/tmp/` and export `TMPDIR` accordingly. Node-local `/tmp` inside a job is fine and is wiped at job end.

After every campaign (an agent does this without being asked):

1. **Sync back** to the local outputs tree: `rsync -az --info=progress2 <site>.g5k:<remote_run_dir>/ <local_run_dir>/` (see `example/scripts/sync_results_back.sh`).
2. **Verify** the local copy: matching recursive file counts (`find ... -type f | wc -l` on both sides), matching `du -s`, spot-check a few output files parse.
3. **Delete the remote run directory** (only dirs created by this workflow; anything unexpected, ask the user first).
4. **Audit** the home at session end: `ssh <site>.g5k 'du -sh ~/* 2>/dev/null | sort -rh | head'` and flag anything unexpectedly large to the user.

Temporary overshoot during a running campaign is acceptable; a home that *stays* fat is not. Old venvs, stale build caches, dead run dirs and superseded dependency trees are fair game for cleanup, but list them to the user before removing anything not created in the current session.

## Environment & bootstrap gotchas

- **Toolchain**: nodes and frontends run Debian with an old default GCC; `module avail gcc` lists newer ones (e.g. `module load gcc/13.2.0_gcc-10.4.0` on nancy) for modern C++. Best practice: build on the frontend with the modern gcc **and `-static-libstdc++`** so compute nodes need no module environment at run time. Otherwise workers hit `GLIBCXX_... not found` unless each is wrapped in `bash -lc '. ./env.sh && exec ...'`.
- **Python**: install `uv` once (`curl -LsSf https://astral.sh/uv/install.sh | sh`, then `source $HOME/.local/bin/env`), then `uv sync --frozen` in the project; prefer `uv run` over venv activation in batch jobs.
- **Git/GitHub**: avoid relying on ssh-agent state on the frontend; use `GIT_SSH_COMMAND='ssh -i ~/.ssh/<key> -o IdentitiesOnly=yes' git pull --ff-only`. Unauthenticated submodule clones must use HTTPS URLs (SSH URLs fail without credentials).
- File transfer: `rsync`/`scp` via the `.g5k` aliases (see `docs/getting-started.md` for the `~/.ssh/config` block).

## Session checklist

Start: `oarstat -u $USER` (live jobs? zombies?), then plan against the clock (what can finish before 19:00?), then reserve or attach. End: results synced and verified, remote outputs deleted, no idle reservation left behind (`oardel`, or a deliberate keep with a stated reason), home `du` audit clean, `usagepolicycheck -t` if anything felt borderline.

## Worked example: a MAMUT-routing campaign on nancy/gros

A concrete end-to-end narrative for the [MAMUT-routing](https://github.com/MAMUT-routing) collaboration (time-dependent vehicle routing benchmarks and the [KAYROS](https://github.com/0nyr/kayros) solver). Cluster choice: **gros** at nancy (~120 nodes, 1 CPU x 18 cores each, 96 GiB RAM, SSD, no GPU) is ideal for single-thread solver sweeps dispatched with GNU parallel: many identical cores, no exotic flags needed.

Suppose the campaign is "run the solver on 300 instances x 10 seeds with a 10-minute time limit each": 3000 tasks x 600 s = 500 core-hours, so about 28 node-hours on 18-core gros nodes. A single weeknight reservation of 4 nodes x 8 h (72 slots) covers it with margin.

1. **Bootstrap once** (frontend, `ssh nancy.g5k`): clone the experiment repo and the benchmark data into the home, install `uv`, `uv sync --frozen`, build any C++ component with gcc 13 and `-static-libstdc++`.
2. **Dry-run locally and on the frontend**: the runner prints 3000 worker command lines and the `parallel` invocation, executes nothing.
3. **Mode A smoke run** (daytime, quota-free): `oarsub -q default -p gros -n mamut-smoke -l host=1,walltime=1 "sleep infinity"`, attach with `oarsub -C <JOB_ID>`, launch the runner with `--limit 20`, watch the joblog, confirm 20 result JSONs land and a re-run skips them.
4. **Mode B campaign**: `oarsub -q default -p gros -n mamut-sweep -l host=4,walltime=8 -r '<next weekday> 19:00'` (19:00 start, well within the 14 h weeknight cap). Report the JOB_ID to the user. At 19:00, attach via the non-interactive heredoc pattern, `nohup` the launcher, detach.
5. **Monitor from the local machine**: `ssh nancy.g5k 'tail -n 5 ~/my-experiments/run.log'`, joblog row counts, output-file counts. Extend with `oarwalltime` only if needed and legal.
6. **Wrap up**: rsync outputs back, verify counts on both sides, delete the remote run dir, `oardel` anything still held, home audit, done.

The `example/` directory of this repository is a miniature, fully runnable version of exactly this workflow with a toy solver, so you can rehearse steps 2 to 6 end to end before touching real experiments.
