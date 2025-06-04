import os
import subprocess
from datetime import datetime
import json
import time

# Assuming these are correctly imported from your Flask app's __init__.py or app.py
from app import app, db
from app import ScrapeJob, ScrapedProfile, UserSettings # Assuming these are your SQLAlchemy models

# --- RQ Queue setup (usually done in app.py or a config, but kept here for context if needed elsewhere) ---
# from redis import Redis
# from rq import Queue
# redis_connection = Redis(host='localhost', port=6379, db=0)
# default_queue = Queue('default', connection=redis_connection)
# --- End RQ Queue setup ---


def run_instagram_scraper(user_id, job_id, user_settings_dict):
    """
    Executes the Instagram scraper as a subprocess for a given job.
    Updates job status in the database.
    """
    with app.app_context(): # Ensure database operations happen within Flask app context
        job = ScrapeJob.query.get(job_id)
        if not job:
            print(f"[{datetime.now()}] Job {job_id} not found, aborting.")
            return

        # Prevent re-running if job is already in a final state or currently running
        if job.status not in ['pending', 'terminated']:
            print(f"[{datetime.now()}] Job {job_id} is already {job.status}, not starting.")
            return

        print(f"[{datetime.now()}] Starting scrape job {job_id} for user {user_id}...")
        job.status = 'running'
        job.start_time = datetime.utcnow()
        db.session.commit() # Commit status change

        print(f"[{datetime.now()}] User Settings for job {job_id}: {user_settings_dict}")

        # --- PATH CONSTRUCTION (CRITICAL FIX) ---
        # Get the directory where tasks.py is located (.../instagram-scraper-webapp)
        current_tasks_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Go up one level to the project root directory (.../latam-instagram-whatsapp-scraper-1)
        project_root_dir = os.path.dirname(current_tasks_dir)
        
        # Construct the full path to main.py, which is in the project root
        scraper_script_path = os.path.join(project_root_dir, 'main.py')

        # Define the directory where scraper output data should be stored
        # Assuming a 'data' folder directly in the project root
        data_output_dir = os.path.join(project_root_dir, 'data')
        os.makedirs(data_output_dir, exist_ok=True) # Ensure 'data' directory exists

        # Define the specific output filename for this job
        output_filename = f"instagram_leads_job_{job_id}.{user_settings_dict['export_format']}"
        scraper_output_file = os.path.join(data_output_dir, output_filename)
        # --- END PATH CONSTRUCTION ---

        # Prepare arguments for the scraper subprocess
        # Use 'python3' for WSL compatibility
        scraper_args = [
            'python3',
            scraper_script_path,
            '--seed_usernames', user_settings_dict['seed_usernames'],
            '--keywords', user_settings_dict['keywords'],
            '--scrape_limit', str(user_settings_dict['scrape_limit']),
            '--recursion_depth', str(user_settings_dict['recursion_depth']),
            '--export_format', user_settings_dict['export_format'],
            '--output_file', scraper_output_file, # Pass the full output path to the scraper
        ]

        # Add --visible_browser flag if enabled
        if user_settings_dict.get('visible_browser'): # Use .get() for safety
            scraper_args.append('--visible_browser')

        # Calculate subprocess timeout based on user setting
        scrape_timeout_seconds = user_settings_dict['scrape_duration_hours'] * 3600
        print(f"[{datetime.now()}] Scraper will be terminated after {scrape_timeout_seconds} seconds ({user_settings_dict['scrape_duration_hours']:.2f} hours).")

        process = None # Initialize process variable
        try:
            # Run the scraper as a subprocess
            print(f"[{datetime.now()}] Running scraper subprocess: {' '.join(scraper_args)}")
            process = subprocess.run(
                scraper_args,
                capture_output=True, # Capture stdout and stderr
                text=True,           # Decode output as text
                check=False,         # Do not raise CalledProcessError for non-zero exit codes immediately
                timeout=scrape_timeout_seconds # Set timeout for the subprocess
            )

            # Check subprocess return code
            if process.returncode != 0:
                print(f"[{datetime.now()}] [SCRAPER ERROR] Scraper exited with code {process.returncode}")
                print(f"[{datetime.now()}] [SCRAPER STDOUT]\n{process.stdout}")
                print(f"[{datetime.now()}] [SCRAPER STDERR]\n{process.stderr}")
                job.status = 'failed'
            else:
                print(f"[{datetime.now()}] Scraper process for job {job_id} completed naturally.")
                if process.stdout:
                    print(f"[{datetime.now()}] [SCRAPER STDOUT]\n{process.stdout}")
                if process.stderr: # Scrapers sometimes print info/warnings to stderr
                    print(f"[{datetime.now()}] [SCRAPER STDERR]\n{process.stderr}")
                job.status = 'completed'

            # Handle cases where the process might have been killed (e.g., by system or external timeout)
            # Common negative return codes for being killed by signal
            if process.returncode in [-9, -15]:
                print(f"[{datetime.now()}] Scraper process for job {job_id} was terminated (possibly by timeout or external signal).")
                job.status = 'terminated'

        except subprocess.TimeoutExpired:
            print(f"[{datetime.now()}] Scraper process for job {job_id} timed out after {scrape_timeout_seconds} seconds.")
            job.status = 'terminated'
            if process and process.poll() is None: # If process is still running after timeout, terminate it
                process.terminate()
                # process.wait() # Wait for it to actually terminate if needed
        except Exception as e:
            print(f"[{datetime.now()}] An unexpected error occurred during scraper execution: {e}")
            job.status = 'failed'

        job.end_time = datetime.utcnow() # Record end time regardless of outcome

        # --- Handle results file ---
        if job.status in ['completed', 'terminated'] and os.path.exists(scraper_output_file):
            job.results_file_path = scraper_output_file
            print(f"[{datetime.now()}] Scraper results file found and path stored: {scraper_output_file}")
            
            # Optional: Load profiles into DB if export_format is JSON and structure matches
            if user_settings_dict['export_format'] == 'json':
                try:
                    with open(scraper_output_file, 'r', encoding='utf-8') as f:
                        scraped_data = json.load(f)
                        for profile_data in scraped_data:
                            # Assuming profile_data has keys like 'username', 'full_name', 'whatsapp_number', 'type'
                            profile = ScrapedProfile(
                                job=job,
                                username=profile_data.get('username'),
                                full_name=profile_data.get('full_name'),
                                whatsapp_number=profile_data.get('whatsapp_number'),
                                type=profile_data.get('type')
                            )
                            db.session.add(profile)
                        db.session.commit()
                        print(f"[{datetime.now()}] Loaded {len(scraped_data)} profiles into DB from job {job_id}.")
                except json.JSONDecodeError as e:
                    print(f"[{datetime.now()}] Error decoding JSON from scraper output for job {job_id}: {e}")
                    db.session.rollback()
                except Exception as e:
                    print(f"[{datetime.now()}] Error loading profiles from JSON to DB for job {job_id}: {e}")
                    db.session.rollback()
        elif job.status in ['completed', 'terminated'] and not os.path.exists(scraper_output_file):
            print(f"[{datetime.now()}] Warning: Scraper status is {job.status} but output file not found at {scraper_output_file}")
            # If status says completed/terminated but no file, it's likely a silent failure
            job.status = 'failed' # Re-mark as failed
        else:
            print(f"[{datetime.now()}] No results file expected for job {job_id} with status {job.status}.")

        db.session.commit() # Final commit for job status and results_file_path
        print(f"[{datetime.now()}] Scrape job {job_id} overall process concluded! Final status: {job.status}")

# --- You can keep other tasks or functions here if you have them ---
# For example, a simple test task:
# def test_task(message):
#     print(f"Test task received: {message}")
#     time.sleep(5) # Simulate work
#     print("Test task completed.")