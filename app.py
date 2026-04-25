import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# --- SETUP ---
st.set_page_config(page_title="Catalyst Scout AI", layout="wide")
st.title("🚀 Catalyst AI: Talent Scouting & Engagement Agent")

# Ask the user for their API key on the sidebar
api_key = st.sidebar.text_input("Enter Google Gemini API Key:", type="password")

if not api_key:
    st.warning("Please enter your API Key in the sidebar to start.")
    st.stop()

genai.configure(api_key=api_key)

# --- AUTO-DETECT WORKING MODEL ---
# This asks Google for a list of valid models for your API key to prevent 404 errors.
@st.cache_resource
def get_working_model():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            if 'flash' in m.name.lower(): # Prefers the faster flash models
                return m.name
    # Fallback to standard 1.5 pro if flash isn't available
    return 'models/gemini-1.5-pro' 

# Initialize the model using the auto-detected name
try:
    valid_model_name = get_working_model()
    model = genai.GenerativeModel(valid_model_name)
    st.sidebar.success(f"Connected to model: {valid_model_name}")
except Exception as e:
    st.sidebar.error("Could not fetch models. Check your API key.")
    st.stop()


# --- MOCK DATABASE ---
candidates = [
    {"name": "Alice Chen", "title": "Senior Cloud Engineer", "skills": "AWS, Python, Kubernetes, Terraform", "vibe": "Looking for new challenges, loves automation."},
    {"name": "Bob Smith", "title": "RPA Developer", "skills": "UiPath, Blue Prism, Python, SQL, PowerShell", "vibe": "Happy where he is, but will move for a massive pay bump."},
    {"name": "Charlie Davis", "title": "Junior IT Support", "skills": "Windows, Active Directory, basic networking", "vibe": "Desperate for a job, will say yes to anything."}
]

# --- UI INPUT ---
st.subheader("1. Input Job Description")
jd = st.text_area("Paste the Job Description here:", height=150)

if st.button("Start AI Agent Pipeline") and jd:
    with st.spinner(f"Agent is analyzing JD and scouting using {valid_model_name}...") :
        results = []
        
        # --- THE AGENT LOOP ---
        for candidate in candidates:
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
            Then, assign an Interest Score from 0 to 100.
            Output strictly in this format:
            Reply: [Candidate's simulated message]
            Interest: [number]
            """
            
            try:
                # We put the actual API calls inside a try/except block to catch any remaining issues gracefully
                match_response = model.generate_content(match_prompt).text
                
                score_line = [line for line in match_response.split('\n') if "Score:" in line][0]
                reason_line = [line for line in match_response.split('\n') if "Reason:" in line][0]
                match_score = int(score_line.replace("Score:", "").strip())
                reason = reason_line.replace("Reason:", "").strip()
            except Exception as e:
                match_score = 0
                reason = f"Error evaluating: {str(e)}"

            try:
                engage_response = model.generate_content(engagement_prompt).text
                
                reply_line = [line for line in engage_response.split('\n') if "Reply:" in line][0]
                interest_line = [line for line in engage_response.split('\n') if "Interest:" in line][0]
                simulated_reply = reply_line.replace("Reply:", "").strip()
                interest_score = int(interest_line.replace("Interest:", "").strip())
            except Exception as e:
                interest_score = 0
                simulated_reply = "Simulation failed."
            
            # Save the data
            results.append({
                "Candidate": candidate['name'],
                "Current Title": candidate['title'],
                "Match Score": match_score,
                "Interest Score": interest_score,
                "Explainability": reason,
                "Simulated Chat": simulated_reply
            })
            time.sleep(2) # Increased sleep slightly to be safe with rate limits
            
        # --- OUTPUT ---
        st.success("Scouting Complete!")
        st.subheader("2. Ranked Shortlist")
        
        # Convert to a nice table and sort by combined scores
        df = pd.DataFrame(results)
        df['Total Score'] = df['Match Score'] + df['Interest Score']
        df = df.sort_values(by="Total Score", ascending=False).drop(columns=['Total Score'])
        
        st.dataframe(df, use_container_width=True)
