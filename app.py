import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
import json
import random
import string

# --- SETUP ---
st.set_page_config(page_title="Catalyst Scout AI", page_icon="🎯", layout="wide")
st.title("🎯 Catalyst AI: Talent Scouting & Engagement Agent")

st.sidebar.header("Agent Configuration")
api_key = st.sidebar.text_input("Enter Google Gemini API Key:", type="password")
# THE HACKATHON LIFESAVER: Demo Mode Toggle
demo_mode = st.sidebar.checkbox("Enable Demo Mode (Bypass API Limits)", value=True, help="Uses local heuristics for instant demo recording without API quotas.")

if not api_key and not demo_mode:
    st.warning("Please enter your API Key or enable Demo Mode in the sidebar to start.")
    st.stop()

if not demo_mode:
    genai.configure(api_key=api_key)
    @st.cache_resource
    def get_working_model():
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower(): 
                    return m.name
        return 'models/gemini-1.5-pro' 

    try:
        valid_model_name = get_working_model()
        model = genai.GenerativeModel(valid_model_name)
        st.sidebar.success(f"Connected to model: {valid_model_name}")
    except Exception as e:
        st.sidebar.error("Could not fetch models. Check your API key.")
        st.stop()
else:
    valid_model_name = "Local Heuristic Engine (Demo Mode)"
    st.sidebar.success("Demo Mode Active. API bypassed.")

# --- LOAD DATABASE ---
@st.cache_data
def load_candidates():
    try:
        with open("candidates.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Could not find candidates.json. Ensure it is uploaded to the repository.")
        st.stop()

all_candidates = load_candidates()
st.sidebar.info(f"Database loaded: {len(all_candidates)} total candidates available.")

# --- UI INPUT ---
st.subheader("1. Input Job Description")
jd = st.text_area("Paste the Job Description here:", height=150)

col1, col2 = st.columns([1, 2])
with col1:
    num_to_screen = st.slider("Select batch size to screen:", min_value=1, max_value=20, value=5)

# --- PIPELINE EXECUTION ---
if st.button("Start AI Agent Pipeline"):
    if not jd.strip():
        st.warning("Action Required: Please paste a Job Description to initiate the scouting pipeline.")
    else:
        candidates_to_screen = random.sample(all_candidates, num_to_screen)
        
        with st.spinner(f"Agent is scouting {num_to_screen} candidates using {valid_model_name}...") :
            results = []
            
            # --- THE AGENT LOOP ---
            for candidate in candidates_to_screen:
                
                # --- THE BOUNCER (Global Pre-Check) ---
                # Clean punctuation so we only match exact whole words
                jd_clean = jd.translate(str.maketrans('', '', string.punctuation)).lower()
                jd_words = set(jd_clean.split())
                
                # Our strict list of required whole words
                tech_keywords = {'developer', 'engineer', 'cloud', 'rpa', 'automation', 'it', 'data', 'software', 'ai', 'tech', 'programmer', 'scripting'}
                is_tech_jd = bool(jd_words.intersection(tech_keywords))

                if not is_tech_jd:
                    # If it's a Retail or HR job, instantly reject. No API calls needed!
                    match_score = 0
                    match_reason = "Complete mismatch. Non-technical JD."
                    interest_score = 0
                    simulated_reply = "I believe you have the wrong person. My background is strictly in technical engineering."
                    interest_reason = "Candidate immediately rejected the irrelevant outreach."
                    time.sleep(0.5)
                    
                elif demo_mode:
                    # --- LOCAL DEMO ENGINE ---
                    time.sleep(0.8) 
                    skills_lower = candidate['skills'].lower()
                    
                    if "uipath" in skills_lower or "python" in skills_lower or "automation" in skills_lower:
                        match_score = random.randint(85, 98)
                        match_reason = f"Strong alignment. Candidate possesses key skills like {candidate['skills'].split(',')[0]} required for the automation workflows."
                    else:
                        match_score = random.randint(30, 55)
                        match_reason = f"Partial match. Lacks core automation stack experience, offering mostly {candidate['skills'].split(',')[0]}."

                    vibe_lower = candidate['vibe'].lower()
                    if "desperate" in vibe_lower or "motivated" in vibe_lower or "startup" in vibe_lower:
                        interest_score = random.randint(88, 99)
                        simulated_reply = "Thank you for reaching out! This role perfectly aligns with
