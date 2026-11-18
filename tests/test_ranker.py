"""Offline tests: every network call goes through an injected fake getter."""
from job_board_ranker.boards import Board, Posting, fetch_board, html_to_text
from job_board_ranker.cli import run
from job_board_ranker.rank import rank_all, rank_posting
from job_board_ranker.store import new_only, open_db

GH = {"jobs": [
    {"id": 1, "title": "Machine Learning Intern", "location": {"name": "Remote - USA"},
     "absolute_url": "https://example.test/1", "updated_at": "2026-10-01T00:00:00Z"},
    {"id": 2, "title": "Senior Software Engineer", "location": {"name": "Los Angeles"},
     "absolute_url": "https://example.test/2", "updated_at": "2026-10-02T00:00:00Z"},
]}
LEVER = [{"id": "a", "text": "Data Intern", "categories": {"location": "Los Angeles", "commitment": "Intern"},
          "workplaceType": "onsite", "hostedUrl": "https://example.test/a", "createdAt": 1790000000000,
          "descriptionPlain": "Python and analytics"}]
ASHBY = {"jobs": [{"id": "x", "title": "Research Intern", "location": "San Francisco",
                   "isRemote": True, "workplaceType": "Hybrid", "jobUrl": "https://example.test/x",
                   "publishedAt": "2026-10-03T00:00:00Z", "descriptionPlain": "research in AI"}]}


def fake_get(url):
    if "greenhouse" in url:
        return GH
    if "lever" in url:
        return LEVER
    return ASHBY


def test_each_platform_is_normalized():
    for source in ("greenhouse", "lever", "ashby"):
        posts = fetch_board(Board(source, "t", "Co"), fake_get)
        assert posts and all(isinstance(p, Posting) and p.url for p in posts)


def test_ashby_is_remote_only_when_explicit():
    (p,) = fetch_board(Board("ashby", "t", "Co"), fake_get)
    assert p.remote is False  # isRemote is ignored on purpose


def test_seniors_and_non_interns_are_dropped():
    posts = fetch_board(Board("greenhouse", "t", "Co"), fake_get)
    ranked = rank_all(posts)
    assert [r.posting.title for r in ranked] == ["Machine Learning Intern"]


def test_reasons_are_given_and_place_helps():
    (p,) = [x for x in fetch_board(Board("lever", "t", "Co"), fake_get)]
    with_place = rank_posting(p, ("Los Angeles",))
    without = rank_posting(p)
    assert with_place.score == without.score + 3
    assert any("near Los Angeles" in r for r in with_place.reasons)


def test_seen_postings_are_not_shown_twice(tmp_path):
    conn = open_db(str(tmp_path / "t.db"))
    posts = fetch_board(Board("greenhouse", "t", "Co"), fake_get)
    assert len(new_only(conn, posts)) == 2
    assert new_only(conn, posts) == []


def test_a_dead_board_is_skipped(tmp_path):
    def boom(url):
        raise RuntimeError("404")

    assert run([Board("greenhouse", "gone", "Gone")], str(tmp_path / "t.db"), (), False, boom) == []


def test_html_to_text():
    assert html_to_text("&lt;p&gt;Hello  <b>world</b>&lt;/p&gt;") == "Hello world"
