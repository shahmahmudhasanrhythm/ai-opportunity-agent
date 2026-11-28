"""Settings that used to be hard-coded in several places."""

# Tried in order; if one is rate-limited or down, the next one is used.
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]

# Who the eligibility check is for. Override any of these in
# .streamlit/secrets.toml under a [profile] section so other students can use the app.
DEFAULT_PROFILE = {
    "nationality": "Bangladeshi",
    "visa": "Chinese X1 student visa",
    "location": "Studying in China",
}

OPPORTUNITY_COLUMNS = [
    "Opportunity Name", "Description Snippet", "Direct Link", "Status",
    "Sponsorship", "Eligibility", "Location", "Deadline", "Requirements",
    "Contact Name", "LinkedIn", "Analyzed",
]

ANALYSIS_FIELDS = ["SPONSORSHIP", "ELIGIBILITY", "LOCATION", "DEADLINE", "REQUIREMENTS", "CONTACT"]
