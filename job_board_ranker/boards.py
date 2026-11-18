"""Fetch postings from the official public job-board APIs of Greenhouse, Lever and Ashby.

These platforms publish JSON feeds so candidates and job boards can read openings.
No login, scraping or browser automation is involved. A board that disappears is
skipped with a logged error instead of stopping the run.
"""
from __future__ import annotations

import html
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

USER_AGENT = "job-board-ranker/0.1 (personal job search tool)"


@dataclass(frozen=True)
class Board:
    source: str   # greenhouse | lever | ashby
    token: str    # the company's board id on that platform
    company: str


@dataclass
class Posting:
    """One job, normalized across the three platforms."""

    source: str
    external_id: str
    company: str
    title: str
    location: str
    remote: bool
    url: str
    posted: str | None
    employment_type: str = ""
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


_TAG = re.compile(r"<[^>]+>")
Getter = Callable[[str], Any]


def html_to_text(s: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", html.unescape(html.unescape(s or "")))).strip()


def _iso_ms(ms: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, UTC).date().isoformat()
    except (TypeError, ValueError):
        return None


def _http_get(url: str) -> Any:
    r = httpx.get(url, timeout=30, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def fetch_board(board: Board, get: Getter = _http_get) -> list[Posting]:
    """List a board's postings. `get` is injectable so tests never touch the network."""
    out: list[Posting] = []
    if board.source == "greenhouse":
        data = get(f"https://boards-api.greenhouse.io/v1/boards/{board.token}/jobs")
        for j in data.get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            out.append(Posting("greenhouse", str(j["id"]), board.company, j.get("title", ""), loc,
                               "remote" in loc.lower(), j.get("absolute_url", ""),
                               (j.get("updated_at") or "")[:10] or None,
                               extra={"token": board.token}))
    elif board.source == "lever":
        for j in get(f"https://api.lever.co/v0/postings/{board.token}?mode=json"):
            cats = j.get("categories") or {}
            locs = cats.get("allLocations") or [cats.get("location", "")]
            loc = "; ".join(x for x in locs if x)
            remote = j.get("workplaceType") == "remote" or "remote" in loc.lower()
            out.append(Posting("lever", j["id"], board.company, j.get("text", ""), loc, remote,
                               j.get("hostedUrl", ""), _iso_ms(j.get("createdAt")),
                               cats.get("commitment", ""),
                               " ".join(filter(None, [j.get("descriptionPlain", ""),
                                                      j.get("additionalPlain", "")]))))
    elif board.source == "ashby":
        data = get(f"https://api.ashbyhq.com/posting-api/job-board/{board.token}")
        for j in data.get("jobs", []):
            locs = [j.get("location", "")] + [s.get("location", "") for s in
                                              j.get("secondaryLocations") or []]
            loc = "; ".join(x for x in locs if x)
            # Ashby's isRemote is set even for city-only roles, so trust only an
            # explicit Remote workplace type or the word in the location text.
            remote = (str(j.get("workplaceType", "")).lower() == "remote"
                      or "remote" in loc.lower())
            out.append(Posting("ashby", j["id"], board.company, j.get("title", ""), loc, remote,
                               j.get("jobUrl", ""), (j.get("publishedAt") or "")[:10] or None,
                               j.get("employmentType", ""), j.get("descriptionPlain", "")))
    return out


def fetch_description(p: Posting, get: Getter = _http_get) -> str:
    """Greenhouse lists omit descriptions; fetch one only for shortlisted jobs."""
    if p.description or p.source != "greenhouse":
        return p.description
    data = get(f"https://boards-api.greenhouse.io/v1/boards/{p.extra['token']}/jobs/{p.external_id}")
    return html_to_text(data.get("content", ""))
