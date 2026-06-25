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

@mcp.tool()
def add_contact(name: str, company: str, linkedin_url: str, relation: str) -> str:
    """Adds a new outreach contact to the database.
    
    Args:
        name: Name of the contact
        company: Company the contact works at
        linkedin_url: URL to their LinkedIn profile
        relation: e.g., 'alumni', 'near_peer', 'other'
    """
    data = {
        "name": name,
        "company": company,
        "linkedin_url": linkedin_url,
        "relation": relation,
        "message_sent": False
    }
    response = supabase.table("contacts").insert(data).execute()
    return f"Successfully added contact {name} at {company}."

@mcp.tool()
def save_message_draft(contact_id: str, message_draft: str) -> str:
    """Saves an AI-generated outreach message draft for a specific contact.
    
    Args:
        contact_id: UUID of the contact
        message_draft: The text of the personalized message to send
    """
    response = supabase.table("contacts").update({"message_draft": message_draft}).eq("id", contact_id).execute()
    return f"Successfully saved message draft for contact {contact_id}."

@mcp.tool()
def list_followups_due() -> List[Dict[str, Any]]:
    """Lists contacts that are due for a follow-up today or earlier."""
    from datetime import date
    today = date.today().isoformat()
    response = supabase.table("contacts").select("*").lte("follow_up_due", today).execute()
    return response.data

@mcp.tool()
def create_application(posting_id: str, resume_version: str) -> str:
    """Creates a new application record for a shortlisted job posting.
    
    Args:
        posting_id: UUID of the job posting
        resume_version: The version/variant of the resume used
    """
    data = {
        "posting_id": posting_id,
        "resume_version": resume_version,
        "status": "applied"
    }
    response = supabase.table("applications").insert(data).execute()
    supabase.table("postings").update({"status": "applied"}).eq("id", posting_id).execute()
    return f"Created application for posting {posting_id}."

@mcp.tool()
def update_application(application_id: str, status: str, next_action: str = None, next_action_date: str = None) -> str:
    """Updates the status and next action of a job application.
    
    Args:
        application_id: UUID of the application
        status: e.g., 'applied', 'interview_scheduled', 'interviewed', 'offer', 'rejected', 'ghosted'
        next_action: Free text describing the next step
        next_action_date: Date for the next action (YYYY-MM-DD)
    """
    data = {"status": status}
    if next_action is not None:
        data["next_action"] = next_action
    if next_action_date is not None:
        data["next_action_date"] = next_action_date
        
    response = supabase.table("applications").update(data).eq("id", application_id).execute()
    return f"Successfully updated application {application_id} to status {status}."
