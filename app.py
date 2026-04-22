import streamlit as st
import pandas as pd
import os
import subprocess
import sys
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Must be the very first command
st.set_page_config(page_title="AI Command Center", page_icon="🌐", layout="wide")

# --- ADVANCED UI: CSS INJECTION ---
custom_css = """
<style>
    /* Global Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    
    /* Glassmorphism Cards for Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 10px;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        border: 1px solid transparent;
        transition: all 0.3s ease-in-out;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.2) !important;
        color: #38bdf8 !important;
        border: 1px solid #38bdf8;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
    
    /* Neon Interactive Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.6);
        border: none;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Glowing Text Inputs */
    .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.05);
        color: white;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: #38bdf8;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

CSV_FILE = "AI_Opportunities_Groq_Smart.csv"

# --- SECRETS MANAGEMENT ---
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- CHAT MEMORY SETUP ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "text": "Systems online. Welcome to the Command Center, Rhythm. What's our next objective?"}
    ]

# --- AI & SCRAPING FUNCTIONS ---
def get_live_intelligence():
    search_query = "AI research internships lab positions freshman sophomore 2026 summer"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=8))
        context = "\n".join([f"Title: {r['title']}\nSnippet: {r['body']}\nLink: {r['href']}" for r in results])
    except Exception:
        context = "" 
    
    prompt = f"""
    You are an elite intelligence agent for a freshman AI student at Westlake University.
    Create a 'Global Intelligence Feed' for today. 
    
    CRITICAL INSTRUCTION: If the Context below is empty, YOU MUST generate a highly realistic, detailed report based on your own internal knowledge of the 2026 AI industry. 
    
    Format exactly like this in Markdown:
    ### 🏛️ WESTLAKE & ASIA FOCUS
    [List 2 real or highly realistic lab opportunities]
    
    ### 🌍 GLOBAL GEMS
    [List 3 high-value internships in USA/Europe/Canada]
    
    ### 🚀 TRENDING
    [List 1-2 specialized AI courses or hackathons]
    
    Context from live search: 
    {context}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    models_to_try = [
        "gemini-2.5-flash", 
        "gemini-2.5-pro", 
        "gemini-2.5-flash-lite"
    ]
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200: 
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                continue
        except Exception: 
            continue
            
    return "⏳ Network anomaly. Signal lost. Please trigger radar again."

def scrape_website_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]): 
                script.extract()
            return soup.get_text(separator=' ', strip=True)[:15000] 
    except Exception: 
        pass
    return ""

def extract_field(ai_text, field_name):
    for line in ai_text.split('\n'):
        if line.upper().startswith(field_name): 
            return line.split(":", 1)[-1].strip()
    return "Not Found"

def find_linkedin_profile(person_name, context):
    if person_name in ["Unknown", "Not Found", "None", "N/A", "Error", ""]: 
        return "Not Found"
        
    try:
        query1 = f"{person_name} {context} LinkedIn"
        res1 = requests.get("https://serpapi.com/search.json", params={"engine": "google", "q": query1, "api_key": SERPAPI_KEY, "num": 3}, timeout=5).json()
        if "error" not in res1: 
            for item in res1.get("organic_results", []):
                if "linkedin.com/in/" in item.get("link", ""): 
                    return item["link"]
    except Exception: 
        pass 
        
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{person_name} {context} LinkedIn", max_results=3)) 
            for item in results:
                if "linkedin.com/in/" in item.get("href", ""): 
                    return item["href"]
    except Exception: 
        return "Not Found"
        
    return "Not Found"

def deep_analyze(title, snippet, link, academic_level):
    page_content = scrape_website_text(link)
    if len(page_content) < 100: 
        page_content = snippet 
        
    prompt = f"""
    Extract exactly: 
    SPONSORSHIP:
    ELIGIBILITY: (Bangladeshi X1 visa in China)
    LOCATION:
    DEADLINE:
    REQUIREMENTS:
    CONTACT:
    
    Title: {title}
    Content: {page_content}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    models_to_try = [
        "gemini-2.5-flash", 
        "gemini-2.5-pro", 
        "gemini-2.5-flash-lite"
    ]
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                resp = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                
                sponsor = extract_field(resp, "SPONSORSHIP")
                eligibility = extract_field(resp, "ELIGIBILITY")
                location = extract_field(resp, "LOCATION")
                deadline = extract_field(resp, "DEADLINE")
                reqs = extract_field(resp, "REQUIREMENTS")
                contact = extract_field(resp, "CONTACT")
                
                linkedin = find_linkedin_profile(contact, title)
                return sponsor, eligibility, location, deadline, reqs, contact, linkedin
        except Exception: 
            continue
            
    return "Error", "Error", "Error", "Error", "All models failed.", "Error", "Error"

def ask_gemini_chat(chat_history):
    formatted_contents = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        formatted_contents.append({"role": role, "parts": [{"text": msg["text"]}]})
        
    payload = {"contents": formatted_contents}
    headers = {'Content-Type': 'application/json'}
    
    models_to_try = [
        "gemini-2.5-flash", 
        "gemini-2.5-flash-lite", 
        "gemini-2.5-pro"
    ]
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200: 
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429: 
                continue 
        except Exception: 
            continue
            
    return "⏳ AI Co-processor cooling down. Please wait 60 seconds."

def load_data():
    if not os.path.exists(CSV_FILE): 
        return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
        expected_columns = [
            'Opportunity Name', 'Description Snippet', 'Direct Link', 'Status', 
            'Sponsorship', 'Eligibility', 'Location', 'Deadline', 
            'Requirements', 'Contact Name', 'LinkedIn', 'Analyzed'
        ]
        for col in expected_columns:
            if col not in df.columns: 
                df[col] = ""
        return df
    except Exception: 
        return pd.DataFrame()

# --- SIDEBAR (WITH AVATAR) ---
with st.sidebar:
    # Look for the uploaded profile picture
    if os.path.exists("profile.jpg"):
        st.image("profile.jpg", caption="Director: Rhythm", use_container_width=True)
    else:
        st.info("Upload 'profile.jpg' to the root folder to activate your avatar here.")
        
    st.markdown("---")
    st.header("Radar Filters")
    opp_type = st.selectbox("Classification:", ["Any", "Internship", "Research", "Fellowship", "Hackathon"])
    academic_level = st.selectbox("Clearance Level:", ["Freshman", "Sophomore", "Junior", "Senior", "Any Undergraduate"])
    country = st.text_input("Target Vector (Country):", value="Any")
    st.write("---")
    
    run_search = st.button("🚀 Initialize Gathering Sequence", use_container_width=True)

    st.write("---")
    current_df = load_data()
    if not current_df.empty:
        st.write(f"**Targets Acquired:** {len(current_df)}")
        st.write(f"🟢 Shortlisted: {len(current_df[current_df['Status'] == 'Shortlisted'])}")
    
    st.write("---")
    if st.button("🧨 Purge Database", type="primary", use_container_width=True):
        if os.path.exists(CSV_FILE): 
            os.remove(CSV_FILE)
        st.rerun()

# --- MAIN SCREEN LOGIC ---
if run_search:
    st.title("🛰️ Establishing Uplink...")
    log_container = st.empty()
    log_text = ""
    
    with st.spinner("Executing autonomous search protocols..."):
        process = subprocess.Popen(
            [sys.executable, "-u", "scraper.py", "--type", opp_type, "--country", country, "--level", academic_level], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1, 
            encoding='utf-8', 
            errors='replace'
        )
        for line in iter(process.stdout.readline, ''):
            log_text += line
            log_container.code(log_text, language="bash")
        process.wait()
        
    st.success("Sequence Complete. Routing to Deck...")
    time.sleep(2)
    st.rerun()

else:
    df = load_data()
    st.title("🌐 Main Command Interface")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Target Deck", 
        "🗄️ Database", 
        "📡 Intel Feed", 
        "🤖 Co-Pilot", 
        "🧰 Armory"
    ])

    with tab1:
        if df.empty:
            st.warning("Database empty. Initialize Gathering Sequence in the sidebar.")
        else:
            pending = df[(df['Status'] == "")]
            if pending.empty:
                st.success("All targets processed.")
                if st.button("Reset Matrix"):
                    df['Status'] = ""
                    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                    st.rerun()
            else:
                idx = pending.index[0]
                job = df.loc[idx]
                
                st.markdown(f"### {job.get('Opportunity Name', 'Unknown')}")
                st.caption(f"**Intercepted Data:** {job.get('Description Snippet', '')}")
                st.markdown(f"[Establish Direct Connection (Open Link)]({job.get('Direct Link', '#')})")
                
                if job.get('Analyzed', 'No') != "Yes":
                    if st.button("⚡ Run Deep Neural Analysis", use_container_width=True):
                        with st.spinner("Processing through Gemini Neural Net..."):
                            sponsor, elig, loc, dead, reqs, contact, link = deep_analyze(
                                job['Opportunity Name'], 
                                job['Description Snippet'], 
                                job['Direct Link'], 
                                academic_level
                            )
                            df.loc[idx, ['Sponsorship', 'Eligibility', 'Location', 'Deadline', 'Requirements', 'Contact Name', 'LinkedIn', 'Analyzed']] = [sponsor, elig, loc, dead, reqs, contact, link, "Yes" if sponsor != "Error" else "Failed"]
                            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                            st.rerun()
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Clearance:** {job.get('Eligibility', '')}")
                        st.write(f"**Visa:** {job.get('Sponsorship', '')}")
                        st.write(f"**Vector:** {job.get('Location', '')}")
                    with col2:
                        st.warning(f"**Countdown:** {job.get('Deadline', '')}")
                        st.write(f"**Specs:** {job.get('Requirements', '')}")
                    
                    st.markdown("---")
                    contact = str(job.get('Contact Name', '')).strip()
                    linkedin = str(job.get('LinkedIn', '')).strip()
                    
                    if contact and contact not in ["Unknown", "Not Found"]:
                        if linkedin.startswith("http"):
                            st.success(f"**Target Identified:** {contact} - [Access Profile]({linkedin})")
                        else:
                            st.warning(f"**Target Identified:** {contact} (No direct profile link)")
                    
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("❌ Discard", use_container_width=True):
                            df.at[idx, 'Status'] = 'Passed'
                            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                            st.rerun()
                    with c2:
                        if st.button("💚 Lock Target", use_container_width=True):
                            df.at[idx, 'Status'] = 'Shortlisted'
                            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                            st.rerun()

    with tab2: 
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.subheader("Live Planetary Sweep")
        if st.button("📡 Execute Radar Pulse", use_container_width=True):
            with st.spinner("Scanning global frequencies..."):
                report = get_live_intelligence()
                st.session_state.daily_report = report
                st.markdown(report)
        elif "daily_report" in st.session_state: 
            st.markdown(st.session_state.daily_report)

    with tab4:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): 
                st.markdown(msg["text"])
                
        if prompt := st.chat_input("Enter command..."):
            st.session_state.messages.append({"role": "user", "text": prompt})
            with st.chat_message("user"): 
                st.markdown(prompt)
            with st.chat_message("model"):
                with st.spinner("Processing..."):
                    resp = ask_gemini_chat(st.session_state.messages)
                    st.markdown(resp)
            st.session_state.messages.append({"role": "model", "text": resp})

    with tab5:
        st.subheader("Engineering Armory")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### LLMs\n* [Claude](https://claude.ai)\n* [Groq](https://groq.com/)\n### Agents\n* [Cursor IDE](https://cursor.sh/)\n* [LangChain](https://www.langchain.com/)")
        with c2:
            st.markdown("### Research\n* [Perplexity](https://www.perplexity.ai/)\n* [PapersWithCode](https://paperswithcode.com/)\n### Hardware\n* [NVIDIA Isaac Sim](https://developer.nvidia.com/isaac-sim)")
