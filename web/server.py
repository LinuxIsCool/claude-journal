# plugins/claude-journal/web/server.py
"""claude-journal web server — thin satellite of claude_webui.WebuiKernel.

Read-only (Phase 1, task-4133): no MutationCatalog, kernel enforces hard-405.
Standard kernel routes only:
  /                 → static/index.html (SPA)
  /api/feed?…       → JournalAccessor.feed  (reverse-chron, journal-class default)
  /api/list?…       → JournalAccessor.list  (filtered, faceted)
  /api/detail/<id>  → JournalAccessor.detail (entry + newer/older neighbors)
  /api/stats        → JournalAccessor.stats
  /api/events       → SSE push (kernel-owned; signature poller)
  /healthz, /static/*  (shared chrome served via kernel Layer-2 fallback)

Mode A standalone:   python web/server.py --port 8865
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from claude_webui import MutationCatalog, WebuiKernel  # noqa: E402

from journal_accessor import NAMESPACE, JournalAccessor  # noqa: E402
from journal_mutations import register_handlers  # noqa: E402
from journal_synthesis import register_synthesis  # noqa: E402

STATIC_DIR: Path = HERE / "static"
DEFAULT_PORT = 8865


def build_kernel(
    port: int = DEFAULT_PORT,
    bind: str = "127.0.0.1",
    data_root: Path | None = None,
    read_only: bool = False,
) -> WebuiKernel:
    """Construct (don't start) the journal substrate kernel.

    Phase 4: a `crud` MutationCatalog provides the capture write surface
    (create_entry / append_today). Pass read_only=True to disable writes.
    """
    if data_root is None:
        data_root = Path.home() / ".claude" / "local" / "journal"
    accessor = JournalAccessor(data_root=data_root)
    catalog = None
    if not read_only:
        # Audit log lives OUTSIDE the journal root so its writes don't churn
        # the accessor's directory-mtime signature (same rule as the FTS cache).
        audit_dir = Path.home() / ".claude" / "local" / "journal-webui-cache" / "mutations"
        # 90s timeout: synthesis routes LLM calls through the catalog (the sole
        # POST path); writes still complete in ms, the ceiling just allows it.
        catalog = MutationCatalog(audit_dir=audit_dir, timeout_s=90.0, paradigm="crud")
        register_handlers(catalog)
        register_synthesis(catalog, accessor._load)  # display-only LLM synthesis
    return WebuiKernel(
        accessor=accessor,
        port=port,
        bind=bind,
        static_dir=STATIC_DIR,
        signature_fn=accessor.signature,
        watch_paths=[accessor.root] if accessor.root.is_dir() else None,
        poll_interval_s=3.0,
        mutation_catalog=catalog,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="claude-journal webui")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", DEFAULT_PORT)))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--data-root", default=None,
                        help="Override journal data root (default ~/.claude/local/journal)")
    parser.add_argument("--read-only", action="store_true",
                        help="Disable the write surface (kernel hard-405s /api/mutate)")
    args = parser.parse_args(argv)
    data_root = Path(args.data_root).expanduser() if args.data_root else None
    kernel = build_kernel(port=args.port, bind=args.bind, data_root=data_root,
                          read_only=args.read_only)
    s = kernel.accessor.stats()  # type: ignore[attr-defined]
    print(
        f"[journal-web] namespace={NAMESPACE} "
        f"root={kernel.accessor.root} "  # type: ignore[attr-defined]
        f"entries={s['total']} journal={s['key_metric']} "
        f"authors={len(s['by_author'])}",
        file=sys.stderr,
    )
    return kernel.serve()


if __name__ == "__main__":
    raise SystemExit(main())
