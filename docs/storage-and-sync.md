# Storage hygiene and syncing results back

Grid'5000 home directories are per-site NFS shares with quotas (check yours at https://api.grid5000.fr/stable/users/). The home is shared between a site's frontend and its compute nodes, not across sites. The deal is simple: code and environments live on g5k while you work there; experiment outputs live in your own repos and only pass through g5k.

## Temp files

- **Never use the frontend `/tmp`.** It is small and shared; filling it breaks ssh-agent and logins for everyone on the site.
- Use `~/tmp` or a repo-local `.cache/tmp/` and export `TMPDIR` accordingly in launchers.
- Node-local `/tmp` inside a job is fine and is wiped when the job ends.

## The post-campaign protocol

Run this after **every** campaign (agents: do it without being asked):

1. **Sync back** to your local outputs tree:
   ```bash
   rsync -az --info=progress2 <site>.g5k:my-experiments/outputs/<run>/ ./outputs/<run>/
   ```
2. **Verify** the local copy before deleting anything remote:
   ```bash
   find ./outputs/<run> -type f | wc -l                      # compare with the same count remote
   ssh <site>.g5k 'find my-experiments/outputs/<run> -type f | wc -l'
   du -s ./outputs/<run>                                     # compare sizes too
   python -c "import json,glob; [json.load(open(f)) for f in glob.glob('outputs/<run>/**/*.json', recursive=True)[:5]]"  # spot-check parses
   ```
3. **Delete the remote run directory** (only directories created by this workflow; anything unexpected, ask first):
   ```bash
   ssh <site>.g5k 'rm -rf my-experiments/outputs/<run>'
   ```
4. **Audit the home** at session end and flag anything unexpectedly large:
   ```bash
   ssh <site>.g5k 'du -sh ~/* 2>/dev/null | sort -rh | head'
   ```

Temporary overshoot while a campaign is running is acceptable; a home that *stays* fat is not. Old venvs, stale build caches, dead run directories and superseded dependency trees are fair game for cleanup, but list them before removing anything you did not create in the current session.

## Handy size and count commands

```bash
find /path/to/dir -type f | wc -l                 # recursive file count
find /path/to/dir -maxdepth 1 -type f | wc -l     # non-recursive
du -sh --block-size=G /path/to/dir                # size in GiB
tail -n 20 /path/to/file                          # peek at a log
```
