# g5k-kickstart

A kickstart kit for running experiment campaigns on [Grid'5000](https://www.grid5000.fr/), the French large-scale testbed for experiment-driven research in computer science. It packages battle-tested operational knowledge so that you (and your AI coding agents) can go from "I have an account" to "my 3000-task sweep ran overnight on 4 nodes and the results are synced back" without stepping on the usage policy.

Built for the [MAMUT-routing](https://github.com/MAMUT-routing) collaboration; generic for anyone running solver sweeps or similar batch experiments on g5k.

## What's inside

| Path | What it is |
|---|---|
| `skills/g5k/SKILL.md` | The operational core, packaged as an agent skill: golden rules, OAR cheatsheet, agent operating modes, non-interactive SSH patterns, distributed runs with GNU parallel, cleanup protocol, and a MAMUT-routing worked example. |
| `docs/` | Human-readable guides: getting started, usage policy, running experiments, storage and sync, MAMUT-routing example. |
| `example/` | A fully runnable toy experiment (stdlib-only Python, `uv`-managed) demonstrating the dry-run, smoke-run, full-run methodology, locally and on g5k. |
| `AGENTS.md` | Entry point for AI agents working from this repo without plugin support. |

## Install as a Claude Code plugin

From any Claude Code session:

```
/plugin marketplace add 0nyr/g5k-kickstart
/plugin install g5k-kickstart@g5k-kickstart
```

This works with the private repo as long as your `gh` or git credentials can read it. The skill is then available as `/g5k-kickstart:g5k`, and Claude will pull it in automatically whenever a task involves Grid'5000.

Not using Claude Code? Point your agent at `AGENTS.md` and `skills/g5k/SKILL.md`, or copy the skill into your own agent setup.

## Quickstart (human)

1. Get a Grid'5000 account and upload your SSH key: https://www.grid5000.fr/w/Grid5000:Get_an_account
2. Follow `docs/getting-started.md` to set up SSH aliases (`ssh nancy.g5k`) and bootstrap your environment on a frontend.
3. Read `docs/usage-policy.md`. Seriously. The day/night rules and the "never compute on the frontend" rule are what keep the account (and the collaboration's reputation) safe.
4. Run the example experiment end to end: `example/README.md` walks you through the dry run, a local smoke run, a quota-free g5k smoke run, and a full multi-node run.
5. Adapt the example's runner pattern (one command per task, resume by output file, GNU parallel over `$OAR_NODEFILE`) to your real experiments.

## The methodology in one paragraph

Every experiment is a list of independent worker commands, one per (instance, seed) task, each writing a single result file via tmp-write-then-rename. The runner can print the commands (`--dry-run`), run a few (`--limit N`), or run everything, skipping tasks whose output file already exists (resume). Execution goes through GNU parallel, locally or across reserved g5k nodes via `--ssh oarsh --slf $OAR_NODEFILE`. You validate with a dry run, then a local smoke run, then a 1-node quota-free g5k smoke run, and only then launch the full campaign on a night or weekend reservation. Afterwards you sync results back, verify, and delete them from the remote home.

## Citing

If this kit is useful in your research workflow, cite it via `CITATION.cff` (GitHub's "Cite this repository" button).

## License

MIT, see `LICENSE`.
