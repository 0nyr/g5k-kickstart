# Usage policy: the rules that protect your account

Authoritative source: [Grid'5000 Usage Policy](https://www.grid5000.fr/w/Grid5000:UsagePolicy). Read it once in full. This page is the operational digest, with the rules ordered by how much trouble they save you.

## 1. Never run compute on the frontend

The frontend (`fnancy`, `flyon`, ...) is a shared gateway for **preparation only**: git, rsync, edits, environment bootstrap, light builds. All experiments run inside an OAR job on reserved nodes. Running heavy background processes on the frontend violates the policy and can get your account restricted. If a reservation expires mid-run, stop and relaunch under a new job; never "finish it on the frontend".

## 2. No AI agents, LLMs, or IDE servers on g5k machines

The policy prohibits running VS Code Server, AI extensions, or background AI agents/LLMs **on** Grid'5000 machines. The setup this kit teaches is out of that rule's scope by construction: agents (Claude Code, Codex, ...) run on **your own machine** and drive g5k remotely over SSH, on your behalf, strictly as an experiment testbed. Nothing agent- or LLM-shaped ever executes on g5k itself. Keep it that way.

## 3. Day/night boundaries (weekdays)

- Daytime is Mon-Fri 9:00-19:00 (French public holidays count as weekend).
- **Weekday jobs must not cross the 9:00 and 19:00 boundaries.** Two exceptions: a job submitted at or after 17:00 may cross 19:00 (the 17:00 to 19:00 portion is quota-free), and a same-day submission may cross 9:00 (the after-9:00 portion counts against the day quota).
- Max job length: 14 h on weeknights (19:00 to 9:00), 62 h on weekends (Friday 19:00 to Monday 9:00).

## 4. Daytime quota

During the day you may use the equivalent of **2 hours on all cores of a cluster, per user per day**. On a 100+ node cluster this is a generous 200+ node-hours; the binding constraints are usually the boundary rules and courtesy toward other users, not the quota itself.

Quota-free escape hatches, ideal for smoke tests and agent-driven iteration:

- Jobs of walltime <= 1 h submitted less than 10 minutes before their start are excluded from the quota. An immediate `oarsub ... -l host=1,walltime=1 "cmd"` qualifies.
- Walltime extensions of <= 1 h requested less than 10 minutes before the job ends are also quota-free and renewable. This keeps a debugging node alive across an iteration session. It is for iterating, not for smuggling a campaign into the day.

## 5. Reserved time counts, used or not

Idle reservations are still usage. Release what you don't need (`oardel <JOB_ID>`), don't hoard nodes, and check `oarstat -u $USER` for forgotten jobs at the start and end of every session. There is no hard cap on concurrent reservations; the quota and boundary rules are what govern usage.

## 6. Keep your home lean

Home directories are per-site NFS shares with quotas (see https://api.grid5000.fr/stable/users/). Repos, venvs, and dependencies live there; accumulated experiment outputs do not. Sync results back after each campaign, verify, then delete the remote copies. See `storage-and-sync.md`.

Never use the frontend `/tmp` (it is small and shared; filling it breaks things for everyone). Use `~/tmp` or a repo-local cache dir and export `TMPDIR`. Node-local `/tmp` inside a job is fine and is wiped at job end.

## 7. Self-audit

```bash
usagepolicycheck -t                      # current usage
usagepolicycheck -l --sites nancy        # violations on a site
usagepolicycheck -v --start '2026-02-10 09:00:00 +0100' --end '2026-02-17 09:00:00 +0100'
```

Run `-t` whenever a session felt borderline. A self-caught violation with a quick apology is a very different conversation from one the admins catch.
