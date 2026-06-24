import sys
import os
import json
import google.generativeai as genai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GEMINI_API_KEY
from supabase_client import supabase

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Define a mock resume for now
MOCK_RESUME = """
Software Engineer with 2 years of experience.
Skills: Python, React, Postgres, Node.js.
Previous: Built scalable APIs, optimized database queries, frontend with Vite.
Education: BS Computer Science.
"""

def score_job(role_title, description):
    prompt = f"""
    You are an expert technical recruiter matching a candidate to a job.
    
    Candidate Resume:
    {MOCK_RESUME}
    
    Job Title: {role_title}
    Job Description: {description}
    
    Please evaluate the fit of this candidate for this job.
    Provide your response as a JSON object with exactly these three keys:
    "fit_score": an integer from 1 to 10 (10 being a perfect fit).
    "fit_reasoning": a 1-2 sentence string explaining why you gave this score.
    "resume_variant": a string, either "swe" or "data_ml" depending on what the role focuses on more.
    
    Return ONLY valid JSON. No markdown formatting, no comments.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up in case the model returns markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        result = json.loads(text.strip())
        return result
    except Exception as e:
        print(f"Error scoring job: {e}")
        return None

def run_score_postings_task():
    print("Starting score_postings task...")
    
    # Fetch unscored postings
    response = supabase.table("postings").select("*").is_("fit_score", "null").execute()
    unscored_postings = response.data
    
    print(f"Found {len(unscored_postings)} unscored postings.")
    
    for posting in unscored_postings:
        print(f"Scoring {posting['company']} - {posting['role_title']}...")
        
        # If raw_description is empty, we might need a fallback or just use title
        description = posting.get('raw_description', '')
        if not description:
            description = "No description available."
            
        score_data = score_job(posting['role_title'], description)
        
        if score_data:
            try:
                # Update the posting with scores
                update_data = {
                    "fit_score": score_data.get("fit_score"),
                    "fit_reasoning": score_data.get("fit_reasoning"),
                    "resume_variant": score_data.get("resume_variant"),
                    "status": "shortlisted" if score_data.get("fit_score", 0) >= 7 else "new"
                }
                supabase.table("postings").update(update_data).eq("id", posting["id"]).execute()
                print(f"Successfully scored {posting['company']} ({update_data['fit_score']}/10)")
            except Exception as e:
                print(f"Failed to update posting {posting['id']} in Supabase: {e}")

    print("Scoring complete.")

if __name__ == "__main__":
    run_score_postings_task()
