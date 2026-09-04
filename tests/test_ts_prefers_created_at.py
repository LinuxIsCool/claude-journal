"""The feed's timestamp comes from the entry, not from its filename.

legion.journal/v3 made `created_at` the canonical timestamp, and the skill tells
authors NOT to write `created`, `date` or `time`. The accessor's alias chain
still read only ("timestamp", "created", "date"), so a schema-correct entry
matched nothing, fell through to the path/filename branch, and was served at
minute precision stamped +00:00 rather than the author's local offset. Every
displayed time was seven hours out on this machine.

Nothing failed while that was true. The ts chain is *designed* to fall through,
so a schema change plus a graceful degradation produced confidently wrong data
with no error anywhere, and the feed still looked correctly sorted because every
entry degraded the same way.

These call the real `_parse_file` against real files on disk. An earlier draft
of this file reimplemented the resolution loop in a helper and passed against
the UNFIXED accessor, which is the same defect class the fix is about: a test
that transcribes the implementation stops testing it.
"""
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))

import journal_accessor as ja  # noqa: E402


@pytest.fixture()
def corpus(tmp_path: Path):
    """A journal root, and a writer that puts an entry at a v3-shaped path.

    The path matters: `YYYY/MM/DD/HH-MM-slug.md` is exactly what the fallback
    branch reads, so every entry here has a filename-derived answer available.
    A test whose file could not fall through would prove nothing.
    """
    day = tmp_path / "legion" / "2026" / "09" / "03"
    day.mkdir(parents=True)

    def write(frontmatter: str, name: str = "15-39-an-entry.md") -> dict:
        (day / name).write_text(f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n\nBody.\n")
        acc = ja.JournalAccessor.__new__(ja.JournalAccessor)
        acc.root = tmp_path
        return acc._parse_file(day / name)

    return write


def test_created_at_is_used_rather_than_the_filename(corpus):
    """The regression. Without the fix this returns 2026-09-03T15:39:00+00:00,
    read off the filename, because created_at was in no alias chain."""
    rec = corpus("created_at: '2026-09-03T15:39:36-07:00'")
    assert rec["ts"] == "2026-09-03T15:39:36-07:00"


def test_the_authors_offset_and_seconds_survive(corpus):
    """The user-visible half: the filename branch can only ever yield minute
    precision at +00:00, which on this machine is seven hours wrong."""
    rec = corpus("created_at: '2026-09-03T15:39:36-07:00'")
    assert rec["ts"].endswith("-07:00")
    assert rec["ts"][17:19] == "36"


def test_created_at_beats_the_legacy_aliases(corpus):
    """A migrated entry carries both; the canonical field is the one to trust."""
    rec = corpus(
        """
        created_at: '2026-09-03T15:39:36-07:00'
        created: '2020-01-01T00:00:00-07:00'
        date: '2019-01-01'
        """
    )
    assert rec["ts"].startswith("2026-09-03")


def test_an_unquoted_created_at_is_normalised_not_stringified(corpus):
    """The trap that makes the isinstance guard load-bearing.

    Unquoted, yaml.safe_load yields a datetime whose str() renders a SPACE
    instead of "T". _load() sorts ts lexicographically and ' ' < 'T', so a
    stringified datetime sorts before every quoted sibling and lands in the
    wrong place in the feed. isoformat() keeps one canonical spelling.
    """
    rec = corpus("created_at: 2026-09-03T15:39:36-07:00")  # no quotes
    assert "T" in rec["ts"], f"expected canonical ISO, got {rec['ts']!r}"
    assert " " not in rec["ts"], f"a space here corrupts chronological order: {rec['ts']!r}"


def test_legacy_entries_still_resolve(corpus):
    """Control. Entries predating v3 carry timestamp/created/date and no
    created_at, and must keep resolving exactly as they did."""
    assert corpus("timestamp: '2024-05-06T07:08:09-07:00'")["ts"].startswith("2024-05-06")
    assert corpus("created: '2024-05-06T07:08:09-07:00'")["ts"].startswith("2024-05-06")


def test_an_entry_with_no_timestamp_still_falls_back_to_its_path(corpus):
    """Control, and the reason the fallback must not be removed: an entry with
    no frontmatter timestamp still needs a place in the feed."""
    rec = corpus("title: 'No timestamp anywhere'")
    assert rec["ts"].startswith("2026-09-03T15:39")
