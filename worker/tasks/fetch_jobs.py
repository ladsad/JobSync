import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.greenhouse import fetch_greenhouse_jobs
from sources.lever import fetch_lever_jobs
from supabase_client import supabase

def get_target_companies():
    # In a real setup, this might read from docs/company_sources.md or a DB table
    return [
        {"name": "Vercel", "type": "greenhouse", "token": "vercel"},
        {"name": "Figma", "type": "lever", "token": "figma"},
        # Add more real ones for testing later
    ]

def run_fetch_jobs_task():
    print("Starting fetch_jobs task...")
    companies = get_target_companies()
    all_jobs = []
    
    for company in companies:
        print(f"Fetching jobs for {company['name']} ({company['type']})...")
        if company["type"] == "greenhouse":
            jobs = fetch_greenhouse_jobs(company["token"])
        elif company["type"] == "lever":
            jobs = fetch_lever_jobs(company["token"])
        else:
            print(f"Unknown ATS type: {company['type']}")
            continue
        
        # Override the board token with the actual company name
        for job in jobs:
            job["company"] = company["name"]
            
        all_jobs.extend(jobs)
        
    print(f"Found {len(all_jobs)} total jobs.")
    
    # Insert into Supabase, handling duplicates
    inserted_count = 0
    for job in all_jobs:
        try:
            # Upsert using URL as the unique constraint
            # Note: The 'url' column must have a UNIQUE constraint in Postgres
            response = supabase.table("postings").upsert(
                job, 
                on_conflict="url",
                ignore_duplicates=True
            ).execute()
            
            # Upsert responses can be tricky to parse for "was it inserted vs ignored", 
            # but if it didn't throw an exception, it worked.
            if response.data:
                 inserted_count += 1
        except Exception as e:
            # If it's just a duplicate key error and ignore_duplicates didn't catch it for some reason, ignore.
            # Otherwise log it.
            if "duplicate key value violates unique constraint" not in str(e):
                print(f"Failed to insert {job.get('url')}: {e}")

    print(f"Fetch complete. Inserted {inserted_count} new postings.")
    
if __name__ == "__main__":
    run_fetch_jobs_task()
