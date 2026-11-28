import requests
import time
import os
import sys
import argparse
import pandas as pd

from agent.config import OPPORTUNITY_COLUMNS
from agent.search import build_queries

if sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

# The key used to be written here in plain text, in a public repo.
# Now it comes from the environment (Streamlit Cloud exposes secrets as env vars).
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
CSV_FILENAME = "AI_Opportunities_Groq_Smart.csv"

def run_fast_gatherer(opp_type, country, academic_level):
    print(f"\n========================================")
    print(f"   STRICT GATHERER: {academic_level.upper()} | {opp_type.upper()} | {country.upper()}")
    print(f"========================================\n")

    if os.path.exists(CSV_FILENAME):
        existing_df = pd.read_csv(CSV_FILENAME, dtype=str).fillna("")
        for col in OPPORTUNITY_COLUMNS:
            if col not in existing_df.columns: existing_df[col] = ""
        existing_links = set(existing_df['Direct Link'].astype(str).tolist())
    else:
        existing_df = pd.DataFrame()
        existing_links = set()

    url = "https://serpapi.com/search.json"
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY is not set. Add it to .streamlit/secrets.toml or export it in your shell.")
        return

    # Query building lives in agent/search.py so it can be unit-tested.
    search_queries = build_queries(opp_type, country, academic_level)
    
    new_findings = []

    for query in search_queries:
        print(f"\nExecuting Strict Search: '{query}'")
        
        # --- UPGRADE 2: THE 6-MONTH TIME LOCK ---
        # "tbs": "qdr:m6" guarantees we only see websites updated in the last 6 months
        for page_start in [0, 10, 20]: 
            params = {"engine": "google", "q": query, "hl": "en", "api_key": SERPAPI_KEY, "start": page_start, "tbs": "qdr:m6"}
            try:
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    results = response.json().get("organic_results", [])
                    if not results: break
                        
                    for item in results:
                        link = item.get("link", "")
                        if link in existing_links: continue 
                        
                        title = item.get("title", "")
                        safe_title = title.encode('ascii', 'ignore').decode('ascii') 
                        snippet = item.get("snippet", "")
                        
                        print(f"  [FOUND] -> {safe_title[:60]}...")
                        
                        new_findings.append({
                            "Opportunity Name": title, "Description Snippet": snippet, "Direct Link": link,
                            "Sponsorship": "", "Eligibility": "", "Location": "", "Deadline": "",
                            "Requirements": "", "Contact Name": "", "LinkedIn": "", 
                            "Status": "", "Analyzed": "No"
                        })
                        existing_links.add(link)
                            
            except Exception as e: 
                safe_error = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"  -> Connection issue: {safe_error}")
            time.sleep(1)

    if new_findings:
        new_df = pd.DataFrame(new_findings)
        final_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['Direct Link'], keep='first')
        try:
            final_df.to_csv(CSV_FILENAME, index=False, encoding='utf-8-sig')
            print(f"\nSUCCESS: Added {len(new_findings)} raw, undergrad-focused opportunities to the deck.")
        except PermissionError: print("\nERROR: Close the CSV file (Excel) and try again!")
    else: print("\nSweep complete. No new unique opportunities found under these strict parameters.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", type=str, default="Any")
    parser.add_argument("--country", type=str, default="Any")
    parser.add_argument("--level", type=str, default="Freshman")
    args = parser.parse_args()
    
    run_fast_gatherer(args.type, args.country, args.level)