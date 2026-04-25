import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
import json
import random

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

# Updated logic to catch empty text AND gibberish
if st.button("Start AI Agent Pipeline"):
    # 1. Check if the box is completely empty
    if not jd.strip():
        st.warning("Action Required: Please paste a Job Description to initiate the scouting pipeline.")
    else:
        # 2. Heuristic check for "mumble jumble"
        words = jd.split()
        longest_word = max(len(w) for w in words) if words else 0
        
        # A real JD has more than 5 words, and real words aren't 35 characters long.
        if len(words) < 5 or longest_word > 35:
            st.error("Validation Error: The provided text does not appear to be a valid, structured Job Description. Please input standard role requirements.")
        else:
            # If it passes all checks, run the pipeline!
            candidates_to_screen = random.sample(all_candidates, num_to_screen)
            
            with st.spinner(f"Agent is scouting {num_to_screen} candidates using {valid_model_name}...") :
                results = []
            
            # --- THE AGENT LOOP ---
            # [The rest of your loop stays exactly the same from here down!]
        
# --- THE AGENT LOOP ---
        for candidate in candidates_to_screen:
            
            # --- THE BOUNCER (Global Pre-Check) ---
            import string
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
                    simulated_reply = "Thank you for reaching out! This role perfectly aligns with my current career goals. When can we chat?"
                    interest_reason = "Candidate is actively looking and highly receptive to new technical challenges."
                elif "passive" in vibe_lower or "comfortable" in vibe_lower:
                    interest_score = random.randint(40, 65)
                    simulated_reply = "I'm currently happy where I am, but I'd be willing to look at the compensation package."
                    interest_reason = "Passive candidate. Requires significant financial incentive to consider leaving current role."
                else:
                    interest_score = random.randint(70, 85)
                    simulated_reply = "Sounds interesting. Could you send over a bit more detail regarding the team structure?"
                    interest_reason = "Moderate interest based on professional curiosity; open to discussions."

            else:
                # --- LIVE API ENGINE ---
                match_prompt = f"""
                You are an AI hiring evaluator.

                Task:
                Evaluate how well the candidate matches the job description.

                Inputs:
                Job Description: {jd}
                Candidate Title: {candidate['title']}
                Candidate Skills: {candidate['skills']}

                Instructions:
                - Return a match score between 0 and 100 (integer only).
                - Base the score on skill overlap, relevance of title, and overall alignment.
                - Do not assume missing information.
                - Keep reasoning concise (max 15 words).

                Output format (strict, no extra text, no bolding):
                Score: <number>
                Reason: <short explanation>
                """
                
                engagement_prompt = f"""
                You are an AI recruiter.

                Task:
                Simulate a candidate's reply to an outreach message and calculate their interest level.

                Inputs:
                Candidate Name: {candidate['name']}
                Candidate Vibe/Status: {candidate['vibe']}
                Match Score: {match_score}

                Instructions:
                - Simulate a short, realistic email reply based solely on their vibe.
                - Return an Interest Score between 0 and 100 (integer only).
                - Keep reasoning concise (max 15 words).

                Output format (strict, no extra text, no bolding):
                Reply: <simulated message>
                Interest: <number>
                Reasoning: <short explanation>
                """
                
                try:
                    match_response = model.generate_content(match_prompt).text.replace("**", "").replace("*", "")
                    match_score = int([line for line in match_response.split('\n') if "Score:" in line][0].replace("Score:", "").strip())
                    match_reason = [line for line in match_response.split('\n') if "Reason:" in line][0].replace("Reason:", "").strip()
                except Exception as e:
                    match_score = 0
                    match_reason = f"API Error: {str(e)[:40]}"

                try:
                    engage_response = model.generate_content(engagement_prompt).text.replace("**", "").replace("*", "")
                    simulated_reply = [line for line in engage_response.split('\n') if "Reply:" in line][0].replace("Reply:", "").strip()
                    interest_score = int([line for line in engage_response.split('\n') if "Interest:" in line][0].replace("Interest:", "").strip())
                    interest_reason = [line for line in engage_response.split('\n') if "Reasoning:" in line][0].replace("Reasoning:", "").strip()
                except Exception as e:
                    interest_score = 0
                    simulated_reply = "Simulation failed."
                    interest_reason = f"API Error: {str(e)[:40]}"
                
                time.sleep(6)
            
            # Save the data
            results.append({
                "Candidate": candidate['name'],
                "Title": candidate['title'],
                "Match %": match_score,
                "Match Reason": match_reason,
                "Interest %": interest_score,
                "Simulated Chat": simulated_reply,
                "Interest Reason": interest_reason 
            })
            
# --- OUTPUT ---
        st.success("Scouting Complete!")
        st.subheader("2. Ranked Shortlist")
        
        df = pd.DataFrame(results)
        
        # Sort by scores, drop the jumbled index, and create a fresh one
        df = df.sort_values(by=["Match %", "Interest %"], ascending=[False, False]).reset_index(drop=True)
        
        # Shift the index to start at 1 instead of 0 for a natural ranking look
        df.index = df.index + 1 
        
        st.dataframe(df, use_container_width=True)
