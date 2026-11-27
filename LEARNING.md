# What changed in this upgrade, and why

Read this with the code open. Each section says what was wrong, what changed, and the idea to take away.

---

## 1. Your SerpAPI key was public (security). Do this first.

**Before:** `scraper.py` line 12 had the key written out, in a public repo. Bots scan GitHub for keys within minutes of a push.

**After:** the key comes from `os.environ["SERPAPI_KEY"]`. The app passes it to the scraper explicitly (`env=scraper_env`).

**⚠️ What you must still do:** the old key is in your **git history** forever. Deleting it from the file doesn't remove it from old commits. **Get a new key in the SerpAPI dashboard** and put the new one only in `.streamlit/secrets.toml` and the Streamlit Cloud secrets settings.

**Lesson:** a secret that was ever committed must be treated as leaked. Rotate it, don't just delete it.

## 2. The Gemini key was in every URL

**Before:** `...:generateContent?key=YOUR_KEY`. URLs get written into server logs, proxy logs and error messages.

**After:** `agent/gemini.py` sends it in the `x-goog-api-key` header. `tests/test_gemini.py` checks that the key never appears in a URL.

## 3. The Intelligence Feed was told to make things up

**Before:** the prompt said: *if the search is empty, generate a highly realistic report from your own knowledge… provide actual company names*. In other words, invent internships. For a tool you use to decide where to apply, that's the worst possible failure: a confident, specific, fake opportunity.

**After:** if the search returns nothing, the app says so. Otherwise the model may only use the search results, and every item must have its link.

**Lesson:** "never show a placeholder" and "never make things up" pull in opposite directions. In anything people act on, choose honesty.

## 4. The field parser silently failed on bold text

**Before:** `extract_field` used `line.upper().startswith("DEADLINE")`. Gemini often replies with `**DEADLINE:** March 1`. That line starts with `**`, so the result was "Not Found", with no error anywhere.

**After:** `parse_fields` in `agent/extraction.py` uses a regular expression that tolerates `**bold**`, bullets and lower case. See `tests/test_extraction.py::test_markdown_bold_and_bullets`.

**Study this:** read the regex `_FIELD_LINE` piece by piece. Try it at regex101.com with the test strings.

## 5. Searches were stuck in 2026

**Before:** every query had `"2026"` hard-coded, so from late 2026 you were searching for programs that had already happened.

**After:** `default_target_year()` targets next year from August onwards. It's tested with fixed dates so the test never goes stale.

## 6. The same code copied four times → modules

The Gemini call (build payload, loop over models, parse the reply) was copied in four functions. When something changed, like the API key fix above, you'd have had to fix it four times and would probably miss one.

The logic now lives in `agent/`, a plain Python package with **no Streamlit imports**. That's what makes it testable: `pytest` can import `agent.extraction` without starting a web app.

```
app.py      → UI only (buttons, tabs, layout)
agent/      → logic (can be tested, reused by scripts)
tests/      → 16 tests, run with `pytest`
```

**Lesson:** this split between UI and logic is the most common thing reviewers look for in a student's code.

## 7. New finds could vanish

**Before:** `scraper.py` wrote the local CSV but never saved to GitHub. If Streamlit Cloud restarted before your next swipe, the new opportunities were gone.

**After:** the app calls `save_to_github(...)` right after the gatherer finishes.

## 8. Measuring accuracy (your next job)

Right now nobody knows how often the eligibility or deadline extraction is right. `eval/` fixes that:

1. Copy `eval/labels_template.csv` to `eval/labels.csv`.
2. Find 30 real postings. Read each one **yourself** and write down the true eligibility, location, deadline and contact. These are your **gold labels**.
3. Run `python -m eval.evaluate_extraction` and put the numbers in the README.
4. Read `eval/mismatches.csv`. Change the prompt, run again, and see if the numbers go up.

Steps 3 and 4 are the loop real ML engineers use every day: **measure → change → measure again.** "Improved deadline extraction from 60% to 85% on 30 hand-labelled postings" is a great CV line. It must be a number you actually measured.

## Still to do (good next tasks for you)

- Every swipe makes a commit on `main`, which clutters your history. Move the data to SQLite or Supabase.
- Weekly email digest of new matches.
- Let other Westlake students use it: per-user data instead of one shared CSV.
