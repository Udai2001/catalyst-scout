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
