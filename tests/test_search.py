from datetime import date

from agent.search import build_queries, default_target_year


def test_target_year_rolls_over_in_autumn():
    assert default_target_year(date(2026, 3, 1)) == 2026
    assert default_target_year(date(2026, 11, 27)) == 2027


def test_internship_queries():
    qs = build_queries("Internship", "Singapore", "Freshman", year=2027)
    assert len(qs) == 3
    assert all('"2027"' in q for q in qs)
    assert all("in Singapore" in q for q in qs)
    assert all("-phd" in q for q in qs)
    assert any("site:linkedin.com/jobs" in q for q in qs)


def test_any_country_leaves_no_double_spaces():
    qs = build_queries("Research", "Any", "Any Undergraduate", year=2027)
    for q in qs:
        assert "  " not in q
        assert "in Any" not in q
    assert any('"bachelor"' in q for q in qs)


def test_hackathon_and_fallback():
    assert len(build_queries("Hackathon", "Any", "Sophomore", year=2027)) == 2
    assert len(build_queries("Course", "China", "Junior", year=2027)) == 2
