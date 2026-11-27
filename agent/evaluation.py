"""Comparing the model's extracted fields with hand-written answers ("gold labels")."""
from __future__ import annotations

import re

import pandas as pd


def _norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def match_eligibility(pred: str, gold: str) -> bool:
    """Only the verdict word matters: Yes / No / Unclear."""
    first = lambda s: (re.findall(r"[a-z]+", _norm(s)) or [""])[0]
    return first(pred) == first(gold)


def match_location(pred: str, gold: str) -> bool:
    for word in ("hybrid", "remote", "in-person", "unknown"):
        if word in _norm(gold):
            return word in _norm(pred)
    return _norm(pred) == _norm(gold)


def match_deadline(pred: str, gold: str) -> bool:
    p, g = _norm(pred), _norm(gold)
    if g in ("rolling", "unknown"):
        return g in p
    try:
        return pd.to_datetime(p).date() == pd.to_datetime(g).date()
    except (ValueError, TypeError, OverflowError):
        return p == g


def match_contact(pred: str, gold: str) -> bool:
    """Match on surname-like tokens so 'Dr. Haoyang Li' == 'Haoyang Li'."""
    titles = {"dr", "prof", "professor", "mr", "ms", "mrs"}
    toks = lambda s: {t for t in re.findall(r"[a-z]+", _norm(s)) if t not in titles}
    g = toks(gold)
    if not g or g <= {"unknown"}:
        return toks(pred) <= {"unknown", "not", "found"}
    return g <= toks(pred)


MATCHERS = {
    "ELIGIBILITY": match_eligibility,
    "LOCATION": match_location,
    "DEADLINE": match_deadline,
    "CONTACT": match_contact,
}
