import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_navigation_contract_matches_bookmarkable_webui_views() -> None:
    contract = json.loads((ROOT / "navigation.json").read_text())
    html = (ROOT / "web" / "static" / "index.html").read_text()
    assert contract["schema_version"] == 1
    assert contract["app"] == "journal"
    assert [item["id"] for item in contract["destinations"]] == [
        "feed", "days", "calendar", "insights", "onthisday",
        "synthesis", "constellation", "wrapped", "write",
    ]
    assert "requestedView" in html
    assert 'window.addEventListener("popstate"' in html
