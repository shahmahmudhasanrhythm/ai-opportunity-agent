"""Building Google (SerpAPI) queries for undergraduate AI opportunities."""
from __future__ import annotations

from datetime import date

# Excludes pages meant for graduate students or full-time staff.
NEGATIVE_TERMS = '-phd -master -masters -postdoc -graduate -"full-time" -"senior"'


def default_target_year(today: date | None = None) -> int:
    """From August onwards, students are hunting for NEXT summer's programs.

    The old code hard-coded "2026", so from late 2026 it searched for
    opportunities that had already finished.
    """
    today = today or date.today()
    return today.year + 1 if today.month >= 8 else today.year


def build_queries(opp_type: str, country: str, academic_level: str, year: int | None = None) -> list[str]:
    year = year or default_target_year()
    type_str = "internship OR research OR fellowship OR hackathon" if opp_type.lower() == "any" else opp_type.lower()
    country_str = "" if country.strip().lower() in ("", "any") else f"in {country.strip()}"
    if academic_level == "Any Undergraduate":
        level_str = '("undergraduate" OR "bachelor" OR "bachelors")'
    else:
        level_str = f'("{academic_level}" OR "undergraduate")'
    yr = f'"{year}"'
    neg = NEGATIVE_TERMS
    t = opp_type.lower()

    if t in ("internship", "summer internship"):
        queries = [
            f"AI {level_str} {type_str} {yr} {country_str} site:linkedin.com/jobs {neg}",
            f"machine learning {type_str} {yr} {country_str} {level_str} site:builtin.com OR site:glassdoor.com {neg}",
            f"artificial intelligence {level_str} {type_str} {yr} {country_str} {neg}",
        ]
    elif t in ("research", "summer research", "summer school", "fellowship"):
        queries = [
            f"AI {level_str} {type_str} {yr} {country_str} site:.edu OR site:.ac.uk {neg}",
            f"machine learning research lab {country_str} {level_str} applications {yr} {neg}",
            f"artificial intelligence {type_str} summer {yr} {country_str} university {neg}",
        ]
    elif t == "hackathon":
        queries = [
            f"AI machine learning hackathon {yr} {country_str} {level_str} {neg}",
            f"university AI hackathon {country_str} {yr} site:devpost.com {neg}",
        ]
    else:
        queries = [
            f"AI {level_str} {type_str} {yr} {country_str} {neg}",
            f"machine learning {type_str} {yr} {country_str} university {level_str} {neg}",
        ]
    # Collapse double spaces left by empty parts
    return [" ".join(q.split()) for q in queries]
