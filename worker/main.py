import time
from tasks.fetch_jobs import run_fetch_jobs_task
from tasks.score_postings import run_score_postings_task

def run_loop():
    print("Starting worker loop...")
    while True:
        try:
            print("Running scheduled tasks...")
            run_fetch_jobs_task()
            run_score_postings_task()
            
            print("Sleeping for 60 seconds...")
            time.sleep(60)
        except KeyboardInterrupt:
            print("Worker stopped manually.")
            break
        except Exception as e:
            print(f"Unexpected error in worker loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_loop()
