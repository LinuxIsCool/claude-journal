---
description: "Launch the claude-journal webui (Legion house stack, port 8865) and open the browser"
---

# /journal-web Command

Launch the read-only claude-journal webui — a quiet reading surface over the
journal corpus: reverse-chron feed, by-day grid, single-entry reader with
older/newer navigation, persona + source-class filters, tag facets, full-text
search, and a reading mode that hides chrome.

Canonical Legion house-stack webui (Python stdlib server + single `index.html`,
no Node/Bun build step). As of Phase 4 it has a **capture write surface**
(`✍ write`): composer, templates, daily-prompt, and quick-capture (append-to-today).
Launch with `--read-only` to disable writes (kernel hard-405s `/api/mutate`).

## Action

Start the server in the background and open the browser. The kernel injects the
shared `claude-webui` package on `sys.path` automatically via `server.py`'s
sibling-plugin import, but standalone runs need the webui plugin importable:

```bash
PLUG=~/.claude/plugins/local/legion-plugins/plugins/claude-journal
export PYTHONPATH="$HOME/.claude/plugins/local/legion-plugins/plugins/claude-webui:$PYTHONPATH"
if [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8865/healthz 2>/dev/null)" = "200" ]; then
  echo "already serving on 8865"
else
  python3 "$PLUG/web/server.py" --port 8865 > /tmp/journal-web.log 2>&1 &
  sleep 3
fi
xdg-open http://127.0.0.1:8865/ 2>/dev/null || echo "open http://127.0.0.1:8865/"
```

## What it serves

| Route | Purpose |
|-------|---------|
| `/` | SPA — Feed + By-day, entry reader |
| `/api/feed?author=&tag=&q=&source_class=&limit=&offset=` | Reverse-chron stream (journal-class by default) |
| `/api/list?author=&source_class=&tag=&from=&to=&q=&limit=&offset=` | Filtered, faceted records |
| `/api/detail/<id>` | Full entry (rendered markdown) + older/newer neighbors |
| `/api/stats` | Counts by author / source_class / day + top tags |
| `/api/events` | SSE live-refresh push (3s dir-mtime poller) |
| `/healthz` | Health shape |

## Notes

- **Read-only**: POST/PUT/DELETE/PATCH return 405. Capture + synthesis land in Phase 4.
- **Bind**: `127.0.0.1` only (journal is private). `--bind 0.0.0.0` warns.
- **Source classes**: `journal` (default feed) · `pipeline-alert` · `transcript` · `legacy`.
  Switch via the Source rail; `all` shows everything.
- **Authors**: inferred from the top-level dir (matt / legion / darren / bondometer /
  transcripts), normalized — frontmatter author is unreliable (Phase 0 finding).
- **Tolerant parsing**: entries with missing/partial frontmatter still render; timestamp
  falls back to path → filename → mtime. ~112 newest unfenced entries render fine.
- **State** (view / author / class / tag / search / reading) persists in `localStorage`.
- Data root: `~/.claude/local/journal/` — read on demand, never copied.
