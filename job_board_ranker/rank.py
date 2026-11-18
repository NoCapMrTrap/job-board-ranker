"""Rank postings with plain rules, and say why. No model, no network."""
from __future__ import annotations

from dataclasses import dataclass

from .boards import Posting

INTERN_WORDS = ("intern", "internship", "co-op", "student", "university", "new grad")
SENIOR_WORDS = ("senior", "staff", "principal", "director", "manager", "lead ", "vp ", "head of")
TOPIC_WORDS = {
    "ai": 3, "machine learning": 3, "ml": 2, "llm": 3, "data": 2, "python": 2,
    "research": 2, "software": 2, "automation": 1, "analytics": 2,
}


@dataclass
class Ranked:
    posting: Posting
    score: int
    reasons: list[str]


def rank_posting(p: Posting, places: tuple[str, ...] = (), want_remote: bool = True) -> Ranked | None:
    """Return a score and the reasons for it, or None when the posting is not an internship."""
    title = p.title.lower()
    text = f"{title} {p.description.lower()}"
    if not any(w in title for w in INTERN_WORDS):
        return None
    if any(w in title for w in SENIOR_WORDS):
        return None
    score, reasons = 1, ["internship-type title"]
    for word, pts in TOPIC_WORDS.items():
        if f" {word} " in f" {text} ":
            score += pts
            reasons.append(f"mentions {word} (+{pts})")
    loc = p.location.lower()
    if p.remote and want_remote:
        score += 2
        reasons.append("remote (+2)")
    for place in places:
        if place.lower() in loc:
            score += 3
            reasons.append(f"near {place} (+3)")
            break
    return Ranked(p, score, reasons)


def rank_all(postings: list[Posting], places: tuple[str, ...] = (), want_remote: bool = True) -> list[Ranked]:
    ranked = [r for p in postings if (r := rank_posting(p, places, want_remote))]
    return sorted(ranked, key=lambda r: (-r.score, r.posting.company, r.posting.title))
