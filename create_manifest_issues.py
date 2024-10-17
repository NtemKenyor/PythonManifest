import requests
import os
import random
import logging
from dotenv import load_dotenv
import string
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# GitHub configuration
organization_name = os.getenv("repo_owner")
repo_name = os.getenv("repo_name")
github_token = os.getenv("access_token")

# GitHub API headers
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json"
}



def generate_unique_code():
    # Get current time in seconds since the epoch
    timestamp = int(time.time())
    
    # Generate a random string of 6 characters (letters and digits)
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    # Combine the random string and the timestamp to form the unique code
    # unique_code = f"{random_string}{timestamp}"
    
    return random_string, timestamp


def fetch_script_urls():
    """
    Fetch the list of Python scripts from the GitHub repository.
    :return: List of script URLs.
    """
    github_api_url = f"https://api.github.com/repos/{organization_name}/{repo_name}/contents/scripts/english"
    try:
        response = requests.get(github_api_url, headers=headers)
        response.raise_for_status()
        files = response.json()
        # print(files)
        script_urls = [file['download_url'] for file in files if file['name'].endswith('.md')]
        logging.info(f"Fetched {len(script_urls)} scripts from GitHub.")
        return script_urls
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch script files from GitHub: {e}")
        return None

def read_last_issue_number(state_file="state.txt"):
    """
    Read the last issue number from the state file.
    :param state_file: The path to the state file.
    :return: The last issue number.
    """
    try:
        with open(state_file, "r") as file:
            last_issue = int(file.read().strip())
        logging.info(f"Last posted issue number is {last_issue}.")
        return last_issue
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Error reading the state file: {e}. Defaulting to issue number 0.")
        return 0

def write_last_issue_number(issue_number, state_file="state.txt"):
    """
    Write the updated issue number to the state file.
    :param issue_number: The issue number to be written.
    :param state_file: The path to the state file.
    """
    try:
        with open(state_file, "w") as file:
            file.write(str(issue_number))
        logging.info(f"Updated state file with issue number {issue_number}.")
    except Exception as e:
        logging.error(f"Failed to write to the state file: {e}")

def create_github_issue(script_url, issue_number):
    """
    Create a new GitHub issue using the script URL.
    :param script_url: The URL of the script to include in the issue.
    :param issue_number: The issue number for tracking.
    :return: True if the issue was created successfully, False otherwise.
    """
    try:
        # Read issue template
        with open("issue_template.txt", "r") as template_file:
            issue_body_template = template_file.read()
        script_name = [z for z in script_url.split("/") if ".md" in z]
        print(script_name)
        # Prepare the issue body and title
        issue_title = f"Create a Python video from the script #{issue_number if len(script_name) == 0 else script_name[0]}"
        issue_body = f"Check out this Python script and create a short video explaining how it works:\n\n{script_url}\n\n" + issue_body_template
        labels = ["good first issue", "first-timers-only", "auto-review","no-code", "easy", "GSOC", "hacktoberfest", "GSOC-2024"]
        random.shuffle(labels)

        # Create issue payload
        payload = {
            "title": issue_title,
            "body": issue_body,
            "labels": labels
        }

        # Post the issue to GitHub
        url = f"https://api.github.com/repos/{organization_name}/{repo_name}/issues"
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        logging.info(f"Issue created successfully: {response.json()['html_url']}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create GitHub issue: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error while creating the issue: {e}")
        return False

def main():
    # Step 1: Fetch script URLs
    script_urls = fetch_script_urls()
    if not script_urls:
        logging.error("Script URLs could not be fetched. Exiting...")
        return

    # Step 2: Read last issue number
    last_posted_issue = read_last_issue_number()
    last_posted_issue = 0 if last_posted_issue >= len(script_urls) else last_posted_issue

    # Step 3: Process next script URL
    script_url = script_urls[last_posted_issue % len(script_urls)]
    logging.info(f"Processing script URL: {script_url}")

    # Step 4: Create GitHub issue
    if create_github_issue(script_url, last_posted_issue + 1):
        # Step 5: Update state file only if issue creation succeeds
        print("sssue created successfully...")
        write_last_issue_number(last_posted_issue + 1)
    else:
        logging.error("Failed to create the issue. No changes will be made to the state file.")

if __name__ == "__main__":
    main()