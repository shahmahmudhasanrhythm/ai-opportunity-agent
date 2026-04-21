import streamlit as st
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# --- UI SETUP ---
st.set_page_config(page_title="AI Opportunity Agent", layout="wide")

# --- SECRETS MANAGEMENT (CLOUD SAFE) ---
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- CORE FUNCTIONS ---
def scrape_website_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]): script.extract()
            return soup.get_text(separator=' ', strip=True)[:15000] 
    except Exception: pass
    return ""

def extract_field(ai_text, field_name):
    for line in ai_text.split('\n'):
        if line.upper().startswith(field_name): return line.split(":", 1)[-1].strip()
    return "Not Found"

def find_linkedin_profile(person_name, context):
    if person_name in ["Unknown", "Not Found", "None", "N/A", "Error", ""]: return "Not Found"
    
    # --- TIER 1: SerpApi ---
    try:
        query1 = f"{person_name} {context} LinkedIn"
        res1 = requests.get("https://serpapi.com/search.json", params={"engine": "google", "q": query1, "api_key": SERPAPI_KEY, "num": 3}, timeout=5).json()
        
        if "error" not in res1: 
            for item in res1.get("organic_results", []):
                if "linkedin.com/in/" in item.get("link", ""): return item["link"]
                
            query2 = f'"{person_name}" university AI LinkedIn'
            res2 = requests.get("https://serpapi.com/search.json", params={"engine": "google", "q": query2, "api_key": SERPAPI_KEY, "num": 3}, timeout=5).json()
            for item in res2.get("organic_results", []):
                if "linkedin.com/in/" in item.get("link", ""): return item["link"]
            return "Not Found" 
    except Exception:
        pass 

    # --- TIER 2: DuckDuckGo ---
    try:
        query = f"{person_name} {context} LinkedIn"
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3)) 
            for item in results:
                link = item.get("href", "")
                if "linkedin.com/in/" in link: return link
        return "Not Found"
    except Exception: 
        return "Not Found"

# --- THE WEBSITE UI ---
st.title("🚀 AI Opportunity Agent (Cloud Edition)")
st.markdown("Analyze research internships and hunt down the supervisor's LinkedIn.")

link = st.text_input("Paste Opportunity Link:")
title = st.text_input("Opportunity Title (Optional):", "Research Internship")
academic_level = st.selectbox("Your Academic Level:", ["Undergraduate", "Masters", "PhD"])

if st.button("Deep Analyze"):
    if not link:
        st.warning("Please paste a link first!")
    else:
        with st.spinner("Scraping website and triggering Gemini AI..."):
            page_content = scrape_website_text(link)
            
            if len(page_content) < 100:
                st.error("🛡️ Firewall detected! The website blocked our scraper. Please try a different link or run it locally.")
            else:
                prompt = f"""
                You are an elite data extraction analyst advising a university student.
                
                STUDENT PROFILE: 
                - Nationality: Bangladeshi
                - Current Visa: Chinese X1 Student Visa
                - Location: Studying in China
                - Academic Level: {academic_level}
                
                Analyze this web content and extract data into EXACTLY this format (keep to a single line per field):
                SPONSORSHIP: [Mentions Visa sponsorship or International eligibility? 3-4 words or "Unknown"]
                ELIGIBILITY: [Can this specific student apply? Start with "Yes", "No", or "Unclear", followed by a 1-sentence reason based on their profile]
                LOCATION: [In-Person / Remote / Hybrid / Unknown]
                DEADLINE: [Extract Exact Date / "Rolling" / "Unknown"]
                REQUIREMENTS: [Highly concise list of requirements found. If none, write "Not explicitly listed"]
                CONTACT: [Extract ONLY the name of the supervising professor, PI, or director. If none, write "Unknown"]
                
                Title: {title}
                Website Content: {page_content}
                """
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                headers = {'Content-Type': 'application/json'}
                
                # Active 2026 Models
                models_to_try = [
                    "gemini-2.5-flash", 
                    "gemini-2.5-pro", 
                    "gemini-2.5-flash-lite"
                ]
                
                success = False
                for model in models_to_try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                    try:
                        response = requests.post(url, json=payload, headers=headers, timeout=15)
                        if response.status_code == 200:
                            data = response.json()
                            resp = data['candidates'][0]['content']['parts'][0]['text'].strip()
                            
                            st.success(f"Analysis Complete! (Powered by {model})")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Sponsorship:** {extract_field(resp, 'SPONSORSHIP')}")
                                st.markdown(f"**Eligibility:** {extract_field(resp, 'ELIGIBILITY')}")
                                st.markdown(f"**Location:** {extract_field(resp, 'LOCATION')}")
                            with col2:
                                st.markdown(f"**Deadline:** {extract_field(resp, 'DEADLINE')}")
                                st.markdown(f"**Requirements:** {extract_field(resp, 'REQUIREMENTS')}")
                            
                            contact = extract_field(resp, "CONTACT")
                            st.markdown("---")
                            st.markdown(f"**Supervising Contact:** {contact}")
                            
                            if contact not in ["Unknown", "Not Found", "None"]:
                                with st.spinner(f"Running Dual-Engine Radar for {contact}..."):
                                    linkedin = find_linkedin_profile(contact, title)
                                    if linkedin != "Not Found":
                                        st.link_button(f"🔗 Connect with {contact} on LinkedIn", linkedin)
                                    else:
                                        st.warning("Could not locate a public LinkedIn profile.")
                            success = True
                            break
                        else:
                            continue
                    except Exception:
                        continue
                
                if not success:
                    st.error("⚠️ All Gemini models are currently overloaded. Give it a minute and hit 'Deep Analyze' again.")
