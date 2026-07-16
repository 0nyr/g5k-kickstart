# Getting started with Grid'5000

Main upstream reference: [Getting Started](https://www.grid5000.fr/w/Getting_Started). This page condenses the practical path from a fresh account to a working experiment environment.

## Account and SSH key

1. Get an account through your team's Grid'5000 project (your supervisor or collaboration lead can sponsor you): https://www.grid5000.fr/w/Grid5000:Get_an_account
2. Upload your SSH public key in the account UI: https://api.grid5000.fr/ui/account
3. Your login below is written `<login>`.

## First connection

```bash
ssh <login>@access.grid5000.fr   # the global access machine
ssh nancy                        # from there, hop to a site frontend (nancy, lyon, rennes, ...)
```

The frontend (e.g. `fnancy`) is where you prepare experiments: clone repos, build, reserve nodes. It is **not** where you run them (see `usage-policy.md`).

## SSH aliases (do this once)

Add to your local `~/.ssh/config` (replace `<login>`):

```
Host g5k
  User <login>
  Hostname access.grid5000.fr
  ForwardAgent no

Host *.g5k
  User <login>
  ProxyCommand ssh g5k -W "$(basename %h .g5k):%p"
  ForwardAgent no
```

Now `ssh nancy.g5k`, `ssh lyon.g5k`, `scp file nancy.g5k:` and `rsync ... nancy.g5k:...` all work directly from your machine. Your home `/home/<login>/` on a site is shared between that site's frontend and its compute nodes (not across sites).

If a connection is refused, check the ssh-agent on your machine: `eval "$(ssh-agent -s)"`, `ssh-add -l`, and `ssh-add ~/.ssh/<key>` (the private key, not the `.pub`). GitHub access can work without the agent, Grid'5000 access generally does not.

## GitHub access from the frontend

To clone private repos on a frontend, generate a dedicated key there and add it to your GitHub account:

```bash
ssh-keygen -t ed25519 -C "github-g5k"
```

In scripts and agent-driven sessions, avoid depending on ssh-agent state; pin the key explicitly:

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes' git clone git@github.com:<org>/<repo>.git
```

Submodules cloned without credentials must use HTTPS URLs (SSH URLs fail).

## Choosing a site and cluster

Browse the [Hardware page](https://www.grid5000.fr/w/Hardware) and the per-site load Gantt (`https://intranet.grid5000.fr/oar/<Site>/drawgantt-svg/`). Take some time to check what hardware you need, how many nodes exist, and how busy they usually are. For CPU-bound single-thread solver sweeps, a large homogeneous cluster of many-core CPU nodes (e.g. `gros` at nancy: ~120 nodes x 18 cores, 96 GiB RAM) beats a small exotic one. Exotic clusters need `-t exotic` in `oarsub`.

## Python environment with uv

On the frontend:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.13
cd <your-project>          # contains pyproject.toml (and uv.lock if pinned)
uv sync --python 3.13      # add --frozen when a uv.lock is committed
```

Prefer `uv run python ...` over activating the venv; it is more robust in batch jobs. If you do want activation: `source .venv/bin/activate`.

## C/C++ toolchain

Frontends and nodes run Debian with an old default GCC. Load a modern one with `module load` (list with `module avail gcc`). Best practice: build on the frontend with the modern gcc and link with `-static-libstdc++`, so compute nodes need no module environment at run time. Otherwise every worker command must be wrapped as `bash -lc '. ./env.sh && exec ...'` to reproduce the module environment, or you will hit `GLIBCXX_... not found` at run time.

## Moving files

```bash
scp results.json nancy.g5k:                       # push a file to the home
scp nancy.g5k:my-exp/outputs/summary.csv ./       # pull a file back
rsync -az --info=progress2 nancy.g5k:my-exp/outputs/ ./outputs/   # pull a tree back
```

## Next steps

Read `usage-policy.md` (mandatory), then rehearse the full workflow with `../example/README.md` before running real experiments.
