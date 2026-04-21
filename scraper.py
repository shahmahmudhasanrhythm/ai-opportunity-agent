import requests
import time
import os
import sys
import argparse
import pandas as pd

if sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

SERPAPI_KEY = "4135a7f707639cbaf7eb64499c133556faf5cf1698323af84437dcc9a59a51f9"
CSV_FILENAME = "AI_Opportunities_Groq_Smart.csv"

def run_fast_gatherer(opp_type, country, academic_level):
    print(f"\n========================================")
    print(f"   STRICT GATHERER: {academic_level.upper()} | {opp_type.upper()} | {country.upper()}")
    print(f"========================================\n")

    if os.path.exists(CSV_FILENAME):
        existing_df = pd.read_csv(CSV_FILENAME, dtype=str).fillna("")
        for col in ["Sponsorship", "Eligibility", "Location", "Deadline", "Requirements", "Contact Name", "LinkedIn", "Status", "Analyzed"]:
            if col not in existing_df.columns: existing_df[col] = ""
        existing_links = set(existing_df['Direct Link'].astype(str).tolist())
    else:
        existing_df = pd.DataFrame()
        existing_links = set()

    url = "https://serpapi.com/search.json"
    
    # --- UPGRADE 1: THE NEGATIVE FILTER BOUNCER ---
    # This physically forces Google to hide pages meant for grads or full-time employees
    neg_terms = '-phd -master -masters -postdoc -graduate -"full-time" -"senior"'
    
    type_str = "internship OR research OR fellowship OR hackathon" if opp_type.lower() == "any" else opp_type.lower()
    country_str = "" if country.lower() == "any" else f"in {country}"
    
    # Force exact match phrasing for the academic level
    if academic_level == "Any Undergraduate":
        level_str = '("undergraduate" OR "bachelor" OR "bachelors")'
    else:
        level_str = f'("{academic_level}" OR "undergraduate")'
    
    search_queries = []
    
    if opp_type.lower() in ["internship", "summer internship"]:
        search_queries = [
            f"AI {level_str} {type_str} \"2026\" {country_str} site:linkedin.com/jobs {neg_terms}",
            f"machine learning {type_str} \"2026\" {country_str} {level_str} site:builtin.com OR site:glassdoor.com {neg_terms}",
            f"artificial intelligence {level_str} {type_str} \"2026\" {country_str} {neg_terms}"
        ]
    elif opp_type.lower() in ["research", "summer research", "summer school", "fellowship"]:
        search_queries = [
            f"AI {level_str} {type_str} \"2026\" {country_str} site:.edu OR site:.ac.uk {neg_terms}",
            f"machine learning research lab {country_str} {level_str} applications \"2026\" {neg_terms}",
            f"artificial intelligence {type_str} summer \"2026\" {country_str} university {neg_terms}"
        ]
    elif opp_type.lower() == "hackathon":
        search_queries = [
            f"AI machine learning hackathon \"2026\" {country_str} {level_str} {neg_terms}",
            f"university AI hackathon {country_str} \"2026\" site:devpost.com {neg_terms}"
        ]
    else:
        search_queries = [
            f"AI {level_str} {type_str} \"2026\" {country_str} {neg_terms}",
            f"machine learning {type_str} \"2026\" {country_str} university {level_str} {neg_terms}"
        ]
        
    search_queries = [" ".join(q.split()) for q in search_queries]
    
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