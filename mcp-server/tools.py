from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

from sources.greenhouse import fetch_greenhouse_jobs
from sources.lever import fetch_lever_jobs
from supabase_client import supabase

# Initialize the MCP server
mcp = FastMCP("JobSearch")

@mcp.tool()
def fetch_greenhouse_postings(token: str, company_name: str) -> str:
    """Fetches jobs from Greenhouse API for a given board token and saves them to the database.
    
    Args:
        token: The Greenhouse board token (e.g. 'vercel')
        company_name: The human-readable company name (e.g. 'Vercel')
    """
    jobs = fetch_greenhouse_jobs(token)
    for job in jobs:
        job["company"] = company_name
    
    inserted = 0
    for job in jobs:
        try:
            res = supabase.table("postings").upsert(job, on_conflict="url", ignore_duplicates=True).execute()
            if res.data:
                inserted += 1
        except Exception as e:
            if "duplicate key value violates unique constraint" not in str(e):
                print(f"Error inserting {job['url']}: {e}")
    return f"Fetched and inserted {inserted} new jobs for {company_name} from Greenhouse."

@mcp.tool()
def fetch_lever_postings(token: str, company_name: str) -> str:
    """Fetches jobs from Lever API for a given board token and saves them to the database.
    
    Args:
        token: The Lever board token (e.g. 'figma')
        company_name: The human-readable company name (e.g. 'Figma')
    """
    jobs = fetch_lever_jobs(token)
    for job in jobs:
        job["company"] = company_name
    
    inserted = 0
    for job in jobs:
        try:
            res = supabase.table("postings").upsert(job, on_conflict="url", ignore_duplicates=True).execute()
            if res.data:
                inserted += 1
        except Exception as e:
            if "duplicate key value violates unique constraint" not in str(e):
                print(f"Error inserting {job['url']}: {e}")
    return f"Fetched and inserted {inserted} new jobs for {company_name} from Lever."

@mcp.tool()
def get_pending_postings() -> List[Dict[str, Any]]:
    """Gets job postings from the database that have not been scored yet (fit_score is null)."""
    response = supabase.table("postings").select("*").is_("fit_score", "null").execute()
    return response.data

@mcp.tool()
def save_posting_score(posting_id: str, fit_score: int, fit_reasoning: str, resume_variant: str) -> str:
    """Saves the AI-evaluated fit score and reasoning back to the job posting.
    
    Args:
        posting_id: The UUID of the job posting
        fit_score: Integer from 1-10 evaluating the candidate's fit
        fit_reasoning: A short explanation of the score
        resume_variant: 'swe' or 'data_ml'
    """
    status = "shortlisted" if fit_score >= 7 else "new"
    update_data = {
        "fit_score": fit_score,
        "fit_reasoning": fit_reasoning,
        "resume_variant": resume_variant,
        "status": status
    }
    response = supabase.table("postings").update(update_data).eq("id", posting_id).execute()
    return f"Successfully updated posting {posting_id} with score {fit_score}/10."
