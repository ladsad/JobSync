import requests
from typing import List, Dict, Any

def fetch_lever_jobs(board_token: str) -> List[Dict[str, Any]]:
    """
    Fetches open job postings from a Lever public job board.
    API: https://api.lever.co/v0/postings/{board_token}?mode=json
    """
    url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for job in data:
            jobs.append({
                "source": "lever",
                "company": board_token,
                "role_title": job.get("text", ""),
                "location": job.get("categories", {}).get("location", ""),
                "url": job.get("hostedUrl", ""),
                "raw_description": job.get("descriptionPlain", ""), # Lever sometimes includes this directly
            })
        return jobs
    except Exception as e:
        import sys
        print(f"Error fetching lever jobs for {board_token}: {e}", file=sys.stderr)
        return []
