"""How accurate is the Gemini extraction, really?

1. Copy eval/labels_template.csv to eval/labels.csv.
2. Fill in ~30 real postings. Read each page YOURSELF and write the true answer
   for each field. This hand-made answer key is called a "gold label".
3. Run:   GEMINI_API_KEY=... python -m eval.evaluate_extraction
          (from the repo root)

Page text is cached in eval/cache/ so re-runs compare prompts, not changing websites.
Outputs per-field accuracy and eval/mismatches.csv to read through.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd

from agent.evaluation import MATCHERS
from agent.extraction import build_analysis_prompt, parse_fields, scrape_website_text
from agent.gemini import generate

HERE = Path(__file__).parent
CACHE = HERE / "cache"


def cached_page(url: str) -> str:
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt")
    if f.exists():
        return f.read_text(encoding="utf-8")
    text = scrape_website_text(url)
    f.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Set GEMINI_API_KEY first.")
        return 1
    labels_path = HERE / "labels.csv"
    if not labels_path.exists():
        print("Create eval/labels.csv from eval/labels_template.csv first.")
        return 1

    labels = pd.read_csv(labels_path, dtype=str).fillna("")
    rows, mismatches = [], []
    for i, r in labels.iterrows():
        page = cached_page(r["url"])
        prompt = build_analysis_prompt(r["title"], page or r["title"], r["academic_level"] or "Freshman")
        reply = generate(prompt, key, timeout=30)
        if reply is None:
            print(f"[{i + 1}/{len(labels)}] model call failed, skipping")
            continue
        pred = parse_fields(reply)
        row = {"url": r["url"]}
        for field, match in MATCHERS.items():
            ok = match(pred[field], r[field])
            row[field] = ok
            if not ok:
                mismatches.append({"url": r["url"], "field": field, "gold": r[field], "predicted": pred[field]})
        rows.append(row)
        print(f"[{i + 1}/{len(labels)}] " + " ".join(f"{k}={'✓' if row[k] else '✗'}" for k in MATCHERS))

    if not rows:
        return 1
    df = pd.DataFrame(rows)
    print("\nAccuracy per field:")
    for field in MATCHERS:
        print(f"  {field:<12} {df[field].mean():.0%}  ({df[field].sum()}/{len(df)})")
    pd.DataFrame(mismatches).to_csv(HERE / "mismatches.csv", index=False)
    print(f"\nRead eval/mismatches.csv to see what it got wrong.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
