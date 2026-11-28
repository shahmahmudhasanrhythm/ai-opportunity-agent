"""Turning a web page into structured fields with an LLM."""
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .config import ANALYSIS_FIELDS, DEFAULT_PROFILE

NOT_FOUND = "Not Found"


def scrape_website_text(url: str, max_chars: int = 15000) -> str:
    """Download a page and return its visible text ('' on failure)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.extract()
        return soup.get_text(separator=" ", strip=True)[:max_chars]
    except requests.RequestException:
        return ""


def build_analysis_prompt(title: str, page_text: str, academic_level: str, profile: dict | None = None) -> str:
    p = {**DEFAULT_PROFILE, **(profile or {})}
    return f"""
You are a careful data extraction analyst advising a university student.
Only use information that appears in the website content. If something is not stated, say "Unknown".

STUDENT PROFILE:
- Nationality: {p['nationality']}
- Current visa: {p['visa']}
- Location: {p['location']}
- Academic level: {academic_level}

Extract data into EXACTLY this format, one field per line:
SPONSORSHIP: [Mentions visa sponsorship or international eligibility? 3-4 words or "Unknown"]
ELIGIBILITY: [Start with "Yes", "No", or "Unclear", then a 1-sentence reason based on the profile]
LOCATION: [In-Person / Remote / Hybrid / Unknown]
DEADLINE: [Exact date / "Rolling" / "Unknown"]
REQUIREMENTS: [Concise list of requirements found, or "Not explicitly listed"]
CONTACT: [ONLY the name of the supervising professor, PI or director, or "Unknown"]

Title: {title}
Website Content: {page_text}
""".strip()


# Matches lines like "DEADLINE: ...", "**DEADLINE:** ...", "- Deadline - ..." etc.
_FIELD_LINE = re.compile(r"^[\s*_\-#>•]*([A-Za-z ]+?)[\s*_]*[:\-–]\s*[*_]*\s*(.*)$")


def parse_fields(ai_text: str, fields: list[str] = ANALYSIS_FIELDS) -> dict[str, str]:
    """Pull 'FIELD: value' lines out of the model's reply.

    The old version used line.upper().startswith(field), which broke whenever
    Gemini added markdown bold ("**DEADLINE:** May 1") and silently returned
    "Not Found". This version tolerates bold, bullets and different case.
    """
    wanted = {f.upper() for f in fields}
    found: dict[str, str] = {}
    for line in (ai_text or "").splitlines():
        m = _FIELD_LINE.match(line)
        if not m:
            continue
        key = m.group(1).strip().upper()
        if key in wanted and key not in found:
            value = m.group(2).strip().strip("*_ ").strip()
            found[key] = value or NOT_FOUND
    return {f.upper(): found.get(f.upper(), NOT_FOUND) for f in fields}
