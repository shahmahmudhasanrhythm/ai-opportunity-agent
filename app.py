import streamlit as st
import pandas as pd
import os
import subprocess
import sys
import time
import requests
import urllib.parse
import base64
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

st.set_page_config(page_title="Freshman AI Opportunity Agent", page_icon="🤖", layout="wide")

CSV_FILE = "AI_Opportunities_Groq_Smart.csv"
TOOLBOX_CSV = "AI_Toolbox_Data.csv"

# --- SECRETS MANAGEMENT (CLOUD SAFE) ---
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- CHAT MEMORY SETUP ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "text": "Hi Rhythm! I'm your embedded assistant. Ready to hunt for new AI opportunities?"}
    ]

# --- THE PERMANENT CLOUD DATABASE FUNCTION ---
def save_to_github(dataframe, filename):
    # 1. Save locally so the app updates instantly on screen
    dataframe.to_csv(filename, index=False, encoding='utf-8-sig')
    
    # 2. Push to GitHub so it survives server reboots permanently
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo = "shahmahmudhasanrhythm/ai-opportunity-agent"
        if not token: return
        
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        # Get current SHA (GitHub requires this to know which file we are overwriting)
        r_get = requests.get(url, headers=headers)
        sha = r_get.json().get('sha') if r_get.status_code == 200 else None
        
        # Convert dataframe to CSV string and encode to Base64
        csv_str = dataframe.to_csv(index=False, encoding='utf-8-sig')
        encoded_content = base64.b64encode(csv_str.encode('utf-8')).decode('utf-8')
        
        payload = {
            "message": f"🤖 Auto-saving {filename} to cloud storage",
            "content": encoded_content
        }
        if sha: payload["sha"] = sha
        
        requests.put(url, headers=headers, json=payload)
    except Exception:
        pass

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
    DO NOT output placeholders like "(Awaiting data)". You must provide actual company names, real lab structures, and actionable descriptions.
    
    Format exactly like this in Markdown:
    ### 🏛️ WESTLAKE & ASIA FOCUS
    [List 2 real or highly realistic lab opportunities]
    
    ### 🌍 GLOBAL GEMS
    [List 3 high-value internships in USA/Europe/Canada (e.g., Microsoft, Google, etc.)]
    
    ### 🚀 TRENDING
    [List 1-2 specialized AI courses or hackathons]
    
    Context from live search:
    {context}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception: continue
    return "⏳ Google's servers are currently overloaded (Error 503/429). Please wait a moment and click the radar button again!"

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
    try:
        query1 = f"{person_name} {context} LinkedIn"
        res1 = requests.get("https://serpapi.com/search.json", params={"engine": "google", "q": query1, "api_key": SERPAPI_KEY, "num": 3}, timeout=5).json()
        if "error" not in res1: 
            for item in res1.get("organic_results", []):
                if "linkedin.com/in/" in item.get("link", ""): return item["link"]
    except Exception: pass 
    try:
        query = f"{person_name} {context} LinkedIn"
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3)) 
            for item in results:
                link = item.get("href", "")
                if "linkedin.com/in/" in link: return link
    except Exception: return "Not Found"
    return "Not Found"

def deep_analyze(title, snippet, link, academic_level):
    page_content = scrape_website_text(link)
    if len(page_content) < 100: page_content = snippet 
    prompt = f"""
    You are an elite data extraction analyst advising a university student.
    
    STUDENT PROFILE: 
    - Nationality: Bangladeshi
    - Current Visa: Chinese X1 Student Visa
    - Location: Studying in China
    - Academic Level: {academic_level}
    
    Analyze this web content and extract data into EXACTLY this format:
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
    models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                resp = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                sponsor = extract_field(resp, "SPONSORSHIP")
                eligibility = extract_field(resp, "ELIGIBILITY")
                loc = extract_field(resp, "LOCATION")
                deadline = extract_field(resp, "DEADLINE")
                reqs = extract_field(resp, "REQUIREMENTS")
                contact = extract_field(resp, "CONTACT")
                return sponsor, eligibility, loc, deadline, reqs, contact, find_linkedin_profile(contact, title)
        except Exception: continue
    return "Error", "Error", "Error", "Error", "All models failed. Traffic is too high.", "Error", "Error"

def ask_gemini_chat(chat_history):
    formatted_contents = [{"role": "user" if msg["role"] == "user" else "model", "parts": [{"text": msg["text"]}]} for msg in chat_history]
    payload = {"contents": formatted_contents}
    headers = {'Content-Type': 'application/json'}
    models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200: return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429: continue 
        except Exception: continue
    return "⏳ Whoa there! We've hit the Google free-tier speed limit. Give it exactly 60 seconds to cool down, and try asking me again!"

def analyze_new_tool(url):
    page_content = scrape_website_text(url)
    prompt = f"""
    You are an AI tool analyst. A student wants to add this URL to their AI Toolbox.
    Based on the website content, extract exactly:
    NAME: [Name of the tool or company]
    CATEGORY: [Choose ONE: LLMs & Chatbots, Coding & Agents, Research & Data, Hardware & Simulation, Other]
    DESCRIPTION: [A punchy 1-2 sentence description of what it does and why an AI student needs it]
    Website Content: {page_content[:10000]}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    for model in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
        url_api = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url_api, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                resp = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                return extract_field(resp, "NAME"), extract_field(resp, "CATEGORY"), extract_field(resp, "DESCRIPTION")
        except Exception: continue
    return "Unknown Tool", "Other", "Could not analyze the website. It might be actively blocking AI scrapers."

def load_toolbox_data():
    if not os.path.exists(TOOLBOX_CSV):
        default_tools = pd.DataFrame([
            {"Name": "Claude", "URL": "https://claude.ai", "Category": "LLMs & Chatbots", "Description": "Currently the industry heavy-hitter for advanced coding and complex logic."},
            {"Name": "ChatGPT", "URL": "https://chatgpt.com", "Category": "LLMs & Chatbots", "Description": "OpenAI's flagship conversational AI and reasoning engine."},
            {"Name": "Groq", "URL": "https://groq.com", "Category": "LLMs & Chatbots", "Description": "The fastest AI inference engine on earth (powered by LPU hardware)."},
            {"Name": "Gemini", "URL": "https://gemini.google.com", "Category": "LLMs & Chatbots", "Description": "Google's multimodal AI, deeply integrated with Workspace tools."},
            {"Name": "Cursor IDE", "URL": "https://cursor.sh", "Category": "Coding & Agents", "Description": "An AI-first code editor that natively reads your entire codebase."},
            {"Name": "GitHub Copilot", "URL": "https://github.com/features/copilot", "Category": "Coding & Agents", "Description": "The ubiquitous AI pair programmer embedded directly in VS Code."},
            {"Name": "LangChain", "URL": "https://www.langchain.com", "Category": "Coding & Agents", "Description": "The industry standard framework for building AI agents that use tools."},
            {"Name": "Hugging Face", "URL": "https://huggingface.co", "Category": "Coding & Agents", "Description": "The GitHub of AI. Access open-source models, datasets, and server spaces."},
            {"Name": "Perplexity AI", "URL": "https://www.perplexity.ai", "Category": "Research & Data", "Description": "The ultimate AI search engine that browses the web and cites academic sources."},
            {"Name": "PapersWithCode", "URL": "https://paperswithcode.com", "Category": "Research & Data", "Description": "Tracks trending AI research papers and links directly to their GitHub repositories."},
            {"Name": "Elicit", "URL": "https://elicit.com", "Category": "Research & Data", "Description": "An AI research assistant that extracts data and findings from academic papers."},
            {"Name": "NVIDIA Isaac Sim", "URL": "https://developer.nvidia.com/isaac-sim", "Category": "Hardware & Simulation", "Description": "Photorealistic robotics simulation for testing drone and robotics logic."},
            {"Name": "Google Colab", "URL": "https://colab.research.google.com", "Category": "Hardware & Simulation", "Description": "Free cloud GPUs for training machine learning models in Jupyter notebooks."},
            {"Name": "Midjourney", "URL": "https://www.midjourney.com", "Category": "Other", "Description": "State-of-the-art AI image and creative asset generation."}
        ])
        save_to_github(default_tools, TOOLBOX_CSV)
        return default_tools
    try:
        return pd.read_csv(TOOLBOX_CSV, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=["Name", "URL", "Category", "Description"])

def load_data():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
        for col in ['Opportunity Name', 'Description Snippet', 'Direct Link', 'Status', 'Sponsorship', 'Eligibility', 'Location', 'Deadline', 'Requirements', 'Contact Name', 'LinkedIn', 'Analyzed']:
            if col not in df.columns: df[col] = ""
        return df
    except Exception: return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("profile.jpg"):
        st.image("profile.jpg", caption="Director: Rhythm", use_container_width=True)
    
    st.header("Search Filters")
    opp_type = st.selectbox("Opportunity Type:", ["Any", "Internship", "Summer School", "Summer Internship", "Course", "Fellowship", "Research", "Summer Research", "Hackathon"])
    academic_level = st.selectbox("Academic Level:", ["Freshman", "Sophomore", "Junior", "Senior", "Any Undergraduate"])
    country = st.text_input("Country (Type 'Any' for global):", value="Any")
    st.write("---")
    
    run_search = st.button("🔍 1. Run Fast Gatherer", use_container_width=True)

    st.write("---")
    current_df = load_data()
    if not current_df.empty:
        st.write(f"**Total in Deck:** {len(current_df)}")
        st.write(f"✅ Shortlisted: {len(current_df[current_df['Status'] == 'Shortlisted'])}")
        st.write(f"❌ Passed: {len(current_df[current_df['Status'] == 'Passed'])}")
    
    st.write("### ⚠️ Danger Zone")
    if st.button("🗑️ Wipe Database", type="primary", use_container_width=True):
        with st.spinner("Purging Cloud Database..."):
            # 1. Create a perfectly blank matrix with the right column headers
            empty_df = pd.DataFrame(columns=['Opportunity Name', 'Description Snippet', 'Direct Link', 'Status', 'Sponsorship', 'Eligibility', 'Location', 'Deadline', 'Requirements', 'Contact Name', 'LinkedIn', 'Analyzed'])
            
            # 2. Push the blank matrix straight to GitHub to overwrite the old one!
            save_to_github(empty_df, CSV_FILE)
            
            st.success("Cloud Purge Complete! The opportunity deck is permanently wiped.")
            time.sleep(1.5)
            st.rerun()
            
    st.caption("AI Command Center v25.0 (Permanent DB Edition)")

# --- MAIN SCREEN LOGIC ---
if run_search:
    st.title("⚙️ Gathering Links...")
    log_container = st.empty()
    log_text = ""
    with st.spinner("Scraping Google..."):
        process = subprocess.Popen([sys.executable, "-u", "scraper.py", "--type", opp_type, "--country", country, "--level", academic_level], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace')
        for line in iter(process.stdout.readline, ''):
            log_text += line
            log_container.code(log_text, language="bash")
        process.wait()
    st.success("Gathering Complete! Loading Deck...")
    time.sleep(2)
    st.rerun()

else:
    df = load_data()
    st.title("🔥 AI Command Center")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🃏 Swipe Deck", "📊 Master Sheet", "📡 Intelligence Feed", "💬 AI Assistant", "🧰 AI Toolbox"])

    with tab1:
        if df.empty:
            st.warning("Database empty. Use the sidebar to start a fast gather!")
        else:
            pending_jobs = df[(df['Status'] == "")]
            if pending_jobs.empty:
                st.success("🎉 All caught up on swiping!")
                if st.button("Reset All Swipes"):
                    df['Status'] = ""
                    save_to_github(df, CSV_FILE)
                    st.rerun()
            else:
                current_index = pending_jobs.index[0]
                current_job = df.loc[current_index]
                link_url = str(current_job.get('Direct Link', '#'))

                st.header(str(current_job.get("Opportunity Name", "Unknown Title")))
                st.write(f"**Snippet:** {current_job.get('Description Snippet', 'No snippet available.')}")
                st.markdown(f"**[🔗 Open Full Website in New Tab]({link_url})**")
                
                analyzed = str(current_job.get('Analyzed', 'No'))
                
                if analyzed != "Yes":
                    if analyzed == "Failed":
                        st.error("⚠️ The last AI analysis attempt failed due to traffic. You can try again.")
                    else:
                        st.info("💡 **Raw Opportunity.** The AI has not extracted the requirements or checked your visa eligibility yet.")
                    
                    if st.button("🧠 Deep Analyze & Check Eligibility", use_container_width=True, type="primary"):
                        with st.spinner("Cascading through Gemini Models to check your visa status..."):
                            sponsor, eligibility, loc, deadline, reqs, contact, linkedin = deep_analyze(current_job['Opportunity Name'], current_job['Description Snippet'], current_job['Direct Link'], academic_level)
                            df.at[current_index, 'Sponsorship'] = sponsor
                            df.at[current_index, 'Eligibility'] = eligibility
                            df.at[current_index, 'Location'] = loc
                            df.at[current_index, 'Deadline'] = deadline
                            df.at[current_index, 'Requirements'] = reqs
                            df.at[current_index, 'Contact Name'] = contact
                            df.at[current_index, 'LinkedIn'] = linkedin
                            df.at[current_index, 'Analyzed'] = "Failed" if sponsor == "Error" else "Yes"
                            
                            save_to_github(df, CSV_FILE)
                            st.rerun()
                else:
                    eligibility_text = str(current_job.get("Eligibility", "Unknown"))
                    if eligibility_text.startswith("Yes"): st.success(f"**✅ Can I Apply?** {eligibility_text}")
                    elif eligibility_text.startswith("No"): st.error(f"**❌ Can I Apply?** {eligibility_text}")
                    else: st.warning(f"**🤔 Can I Apply?** {eligibility_text}")
                    
                    sponsor = str(current_job.get("Sponsorship", "Unknown"))
                    if sponsor == "No Sponsorship": st.error("🚩 RED FLAG: This program likely DOES NOT sponsor visas.")
                    elif sponsor == "International Friendly": st.success("🌍 GLOBAL: Explicitly open to international students!")
                    
                    st.write(f"**🗓️ Deadline:** {current_job.get('Deadline', 'Not found')}")
                    st.write(f"**📋 Requirements:** {current_job.get('Requirements', 'Not found')}")
                    loc = str(current_job.get("Location", "Unknown"))
                    if loc != "Unknown" and loc != "": st.write(f"📍 **Format/Location:** {loc}")
                    
                    st.write("---")
                    st.subheader("💼 Networking & Contacts")
                    contact_name = str(current_job.get('Contact Name', 'Unknown')).strip()
                    linkedin_url = str(current_job.get('LinkedIn', 'Not Found')).strip()
                    
                    if contact_name not in ["Unknown", "Not Found", "nan", "Error", ""] and linkedin_url.startswith("http"):
                        st.success(f"**Target Acquired:** {contact_name} — **[🔗 Connect on LinkedIn]({linkedin_url})**")
                    elif contact_name not in ["Unknown", "Not Found", "nan", "Error", ""]:
                        st.warning(f"**Target Identified:** {contact_name} *(Profile not auto-linked)*")
                        if st.button(f"🔍 Run Deep LinkedIn Radar for {contact_name}"):
                            with st.spinner("Deploying aggressive secondary search agent..."):
                                new_link = find_linkedin_profile(contact_name, current_job['Opportunity Name'])
                                df.at[current_index, 'LinkedIn'] = new_link if new_link != "Not Found" else "No Public Profile"
                                save_to_github(df, CSV_FILE)
                                st.rerun()
                    else:
                        st.info("The AI could not find a specific professor or recruiter name in the text.")
                        safe_query = urllib.parse.quote(current_job.get('Opportunity Name', 'AI Internship'))
                        st.link_button("🔍 Search Organization on LinkedIn", f"https://www.linkedin.com/search/results/all/?keywords={safe_query}", type="primary")

                st.write("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("❌ Pass", use_container_width=True):
                        df.at[current_index, 'Status'] = 'Passed'
                        save_to_github(df, CSV_FILE)
                        st.rerun()
                with col2:
                    if st.button("💚 Shortlist", use_container_width=True):
                        df.at[current_index, 'Status'] = 'Shortlisted'
                        save_to_github(df, CSV_FILE)
                        st.rerun()

    with tab2:
        st.write("### 🗄️ Your Full Opportunity Database")
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.subheader("📡 Live Global Intelligence Radar")
        st.info("This tab scans the live web for the newest postings from the past 24 hours.")
        if st.button("🚀 Trigger Live Global Radar", use_container_width=True):
            with st.spinner("Intercepting global signals..."):
                report = get_live_intelligence()
                st.session_state.daily_report = report
                st.markdown(report)
        elif "daily_report" in st.session_state:
            st.markdown(st.session_state.daily_report)

    with tab4:
        st.subheader("🧠 Your Personal AI Sandbox")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["text"])
                
        if prompt := st.chat_input("Ask me to write Python code, brainstorm MUN strategies, or draft an email..."):
            st.session_state.messages.append({"role": "user", "text": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("model"):
                with st.spinner("Thinking..."):
                    response_text = ask_gemini_chat(st.session_state.messages)
                    st.markdown(response_text)
            st.session_state.messages.append({"role": "model", "text": response_text})

    with tab5:
        st.subheader("🧰 Dynamic AI Toolbox")
        st.markdown("Your custom, growing library of AI agents, LLMs, and research tools.")
        
        with st.expander("➕ Add a New Tool to Your Library", expanded=False):
            new_tool_url = st.text_input("Paste the URL of a new AI tool you found:")
            if st.button("Analyze & Add Tool"):
                if new_tool_url:
                    with st.spinner("Agent is reading the website and extracting data..."):
                        t_name, t_cat, t_desc = analyze_new_tool(new_tool_url)
                        if t_name not in ["Error", "Unknown Tool"]:
                            new_row = pd.DataFrame([{"Name": t_name, "URL": new_tool_url, "Category": t_cat, "Description": t_desc}])
                            tb_df = load_toolbox_data()
                            tb_df = pd.concat([tb_df, new_row], ignore_index=True)
                            
                            # THE MAGIC: Pushes directly to GitHub
                            save_to_github(tb_df, TOOLBOX_CSV)
                            
                            st.success(f"Successfully scraped and permanently saved! Added **{t_name}** to {t_cat}.")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(t_desc)
                            
        tb_df = load_toolbox_data()
        if not tb_df.empty:
            categories = tb_df['Category'].unique()
            for cat in categories:
                st.write(f"### {cat}")
                cat_tools = tb_df[tb_df['Category'] == cat]
                cols = st.columns(3)
                for i, row in cat_tools.reset_index().iterrows():
                    with cols[i % 3]:
                        st.markdown(f"**{row['Name']}**")
                        st.caption(row['Description'])
                        st.link_button(f"🚀 Launch {row['Name']}", row['URL'], use_container_width=True)
                st.write("---")
