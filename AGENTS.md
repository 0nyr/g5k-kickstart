# AGENTS.md — g5k-kickstart

Instructions for AI coding agents (Claude Code, Codex, ...) working in or from this repository.

## What this repository is

A kickstart kit for running experiment campaigns on the [Grid'5000](https://www.grid5000.fr/) testbed. It packages the operational knowledge as an agent skill, human documentation, and a runnable example experiment.

## Where to look

- **`skills/g5k/SKILL.md`** is the operational core: golden rules, agent operating modes, OAR cheatsheet, non-interactive SSH patterns, distributed-run methodology, cleanup protocol. If you are about to touch Grid'5000 in any way (reserve, launch, monitor, sync, clean), read it first and follow it.
- **`docs/`** holds the longer human-readable guides (getting started, usage policy, running experiments, storage and sync, MAMUT-routing worked example).
- **`example/`** is a fully runnable toy experiment demonstrating the dry-run, smoke-run, full-run methodology with GNU parallel, locally and on g5k.

Claude Code users should install this repo as a plugin (see `README.md`), which exposes the skill as `/g5k-kickstart:g5k`. Agents without plugin support can simply read `skills/g5k/SKILL.md`.

## Hard rules for agents operating Grid'5000

These are restated here because they are the ones that protect the account:

1. Never run compute on a frontend. Experiments only run inside OAR jobs.
2. Never install or launch an AI agent, LLM runtime, or IDE server on a g5k frontend or node. Agents drive g5k remotely over SSH from the user's machine.
3. Respect the day/night usage policy: weekday jobs must not cross the 9:00 and 19:00 boundaries (exceptions in the skill), campaigns go to nights and weekends.
4. Release idle reservations, report every `oarsub` you place to the user, and clean the remote home after each campaign (sync back, verify, delete).
5. Fill in or ask for the user configuration (login, project, site, cluster) before issuing any g5k command.

## Conventions in this repository

- Prose in Markdown files is written one paragraph per physical line (editor soft-wrap), never hard-wrapped to a column width.
- Commands in docs use `<login>`, `<site>`, `<cluster>`, `<JOB_ID>` placeholders; keep them generic, personal values do not belong in this repo.
