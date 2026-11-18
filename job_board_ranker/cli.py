"""Command line: python -m job_board_ranker boards.json [--db postings.db] [--place "Los Angeles"]"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from .boards import Board, fetch_board
from .rank import rank_all
from .store import new_only, open_db

log = logging.getLogger("job_board_ranker")


def load_boards(path: str) -> list[Board]:
    with open(path, encoding="utf8") as f:
        return [Board(**row) for row in json.load(f)]


def run(boards: list[Board], db_path: str, places: tuple[str, ...], only_new: bool, get=None) -> list:
    postings = []
    for b in boards:
        try:
            postings += fetch_board(b, get) if get else fetch_board(b)
        except Exception as exc:  # a dead board must not stop the run
            log.error("skipping %s (%s): %s", b.company, b.source, exc)
    if only_new:
        postings = new_only(open_db(db_path), postings)
    return rank_all(postings, places)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="job_board_ranker", description=__doc__)
    ap.add_argument("boards", help='JSON file: [{"source": "greenhouse", "token": "...", "company": "..."}]')
    ap.add_argument("--db", default="postings.db")
    ap.add_argument("--place", action="append", default=[], help="a place to prefer (repeatable)")
    ap.add_argument("--all", action="store_true", help="show everything, not only postings new since last run")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ranked = run(load_boards(args.boards), args.db, tuple(args.place), not args.all)
    for r in ranked[: args.top]:
        p = r.posting
        print(f"{r.score:>3}  {p.company} - {p.title} ({p.location or 'no location'})\n"
              f"     {p.url}\n     why: {'; '.join(r.reasons)}")
    print(f"\n{len(ranked)} internship-type postings ranked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
