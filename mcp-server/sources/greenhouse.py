import requests
from typing import List, Dict, Any

def fetch_greenhouse_jobs(board_token: str) -> List[Dict[str, Any]]:
    """
    Fetches open job postings from a Greenhouse public job board.
    API: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for job in data.get("jobs", []):
            jobs.append({
                "source": "greenhouse",
                "company": board_token, # Might need a separate mapping for display name
                "role_title": job.get("title", ""),
                "location": job.get("location", {}).get("name", ""),
                "url": job.get("absolute_url", ""),
                "raw_description": "", # The basic endpoint doesn't return full description, might need to hit specific job endpoint if needed, or scrape the raw HTML
            })
        return jobs
    except Exception as e:
        print(f"Error fetching greenhouse jobs for {board_token}: {e}")
        return []

# If we need the full description, we might need to hit:
# https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}
