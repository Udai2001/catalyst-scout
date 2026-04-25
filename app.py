import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
import json
import random

# --- SETUP ---
st.set_page_config(page_title="Catalyst Scout AI", layout="wide")
st.title("🚀 Catalyst AI: Talent Scouting & Engagement Agent")

api_key = st.sidebar.text_input("Enter Google Gemini API Key:", type="password")

if not api_key:
    st.warning("Please enter your API Key in the sidebar to start.")
    st.stop()

genai.configure(api_key=api_key)

# --- AUTO-DETECT WORKING MODEL ---
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

# The slider to prevent API rate limits and keep the demo fast
col1, col2 = st.columns([1, 2])
with col1:
    num_to_screen = st.slider("Select batch size to screen:", min_value=1, max_value=20, value=5)

if st.button("Start AI Agent Pipeline") and jd:
    # Randomly sample the requested number of candidates from the DB for the demo
    candidates_to_screen = random.sample(all_candidates, num_to_screen)
    
    with st.spinner(f"Agent is scouting {num_to_screen} candidates using {valid_model_name}...") :
        results = []
        
        # --- THE AGENT LOOP ---
        for candidate in candidates_to_screen:
            # Task 1: Match Score
            match_prompt = f"""
            Job Description: {jd}
            Candidate Profile: {candidate['title']}, Skills: {candidate['skills']}
            Calculate a Match Score from 0 to 100. 
            Output strictly in this format: 
            Score: [number]
            Reason: [1 short sentence explainability]
            """
            
            # Task 2: Simulated Engagement
            engagement_prompt = f"""
            You are an AI recruiter. You sent this candidate ({candidate['name']}) a message about the job.
            Based on their hidden vibe ({candidate['vibe']}), simulate a short reply from them.
            Then, assign an Interest Score from 0 to 100 and explain exactly how you calculated that score.
            Output strictly in this format:
            Reply: [Candidate's simulated message]
            Interest: [number]
            Reasoning: [1 short sentence explaining why this score was given based on their reply and vibe]
            """
            
            try:
                match_response = model.generate_content(match_prompt).text
                score_line = [line for line in match_response.split('\n') if "Score:" in line][0]
                reason_line = [line for line in match_response.split('\n') if "Reason:" in line][0]
                match_score = int(score_line.replace("Score:", "").strip())
                match_reason = reason_line.replace("Reason:", "").strip()
            except Exception as e:
                match_score = 0
                match_reason = f"Parsing Error"

            try:
                engage_response = model.generate_content(engagement_prompt).text
                reply_line = [line for line in engage_response.split('\n') if "Reply:" in line][0]
                interest_line = [line for line in engage_response.split('\n') if "Interest:" in line][0]
                reasoning_line = [line for line in engage_response.split('\n') if "Reasoning:" in line][0]
                
                simulated_reply = reply_line.replace("Reply:", "").strip()
                interest_score = int(interest_line.replace("Interest:", "").strip())
                interest_reason = reasoning_line.replace("Reasoning:", "").strip()
            except Exception as e:
                interest_score = 0
                simulated_reply = "Simulation failed."
                interest_reason = "Could not calculate."
            
            results.append({
                "Candidate": candidate['name'],
                "Title": candidate['title'],
                "Match %": match_score,
                "Match Reason": match_reason,
                "Interest %": interest_score,
                "Simulated Chat": simulated_reply,
                "Interest Reason": interest_reason 
            })
            time.sleep(2) 
            
        # --- OUTPUT ---
        st.success("Scouting Complete!")
        st.subheader("2. Ranked Shortlist")
        
        df = pd.DataFrame(results)
        df['Total Score'] = df['Match %'] + df['Interest %']
        df = df.sort_values(by="Total Score", ascending=False).drop(columns=['Total Score'])
        
        st.dataframe(df, use_container_width=True)
