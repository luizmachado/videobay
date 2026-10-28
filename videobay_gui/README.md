# VideoBay GUI

A lightweight CustomTkinter interface for yt-dlp, living in an isolated folder of the
[videobay](https://github.com/luizmachado/videobay) fork so that upstream merges never conflict.

## Commands (run inside `videobay_gui/`)
| Command | What it does |
|---|---|
| `make run` | Opens the GUI from source (`uv run videobay-gui`) |
| `make ci` | Lint + format + pyright + headless tests + 100% coverage of `core/` |
| `make test-ui` | View smoke tests under Xvfb in a rootless Podman container |
| `make binary` | PyInstaller onefile in Podman → `dist/<git-sha>/videobay-gui` |
| `make install` / `make rollback` | Atomic symlink switch at `~/.local/bin/videobay-gui` |

## Keeping the fork up to date
```bash
git fetch upstream && git merge upstream/master
```
The `videobay-upstream-sync` workflow does this daily. One-time setup on GitHub:
1. Create the secret `VIDEOBAY_UPSTREAM_SYNC_TOKEN` (a fine-grained PAT with Contents + Workflows write on this repo).
2. In the Actions tab, disable the upstream workflows (`build`, `core`, `release*`, `quick-test`, …).
   Only the `videobay-*` workflows should run.

Docs: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/BACKLOG.md`](docs/BACKLOG.md), [`docs/adr/`](docs/adr/).
