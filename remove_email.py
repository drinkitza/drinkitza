import os
import base64
import requests
import csv
import sys

# GitHub configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'drinkitza'
REPO_NAME = 'drinkitza'
FILE_PATH = 'emails/waitlist.csv'

def remove_email_from_github(email_to_remove):
    """Remove an email from the GitHub repository waitlist"""
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        # Get current content
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        current_file = response.json()
        
        if 'content' not in current_file:
            print(f"Error: Could not find content in GitHub file")
            return False
            
        content = base64.b64decode(current_file['content']).decode('utf-8')
        
        # Filter out the email to remove
        lines = content.splitlines()
        new_lines = []
        removed = False
        
        for line in lines:
            if line.strip():
                email = line.split(',')[0].lower()
                if email != email_to_remove.lower():
                    new_lines.append(line)
                else:
                    removed = True
                    print(f"Found {email_to_remove} in GitHub waitlist - removing")
        
        if not removed:
            print(f"Email {email_to_remove} not found in GitHub waitlist")
            return False
            
        new_content = '\n'.join(new_lines) + '\n'
        
        # Update file
        data = {
            'message': f'Remove email: {email_to_remove}',
            'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            'sha': current_file['sha']
        }
        
        update_response = requests.put(url, headers=headers, json=data)
        update_response.raise_for_status()
        print(f"Successfully removed {email_to_remove} from GitHub waitlist")
        return True
        
    except Exception as e:
        print(f"Error removing email from GitHub: {str(e)}")
        return False

def remove_email_from_local(email_to_remove):
    """Remove an email from the local waitlist CSV file"""
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
    
    if not os.path.exists(local_path):
        print(f"Local waitlist file not found at {local_path}")
        return False
    
    # Read the current waitlist
    emails = []
    removed = False
    
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) >= 1:
                        email = parts[0].lower()
                        if email != email_to_remove.lower():
                            emails.append(line.strip())
                        else:
                            removed = True
                            print(f"Found {email_to_remove} in local waitlist - removing")
    except Exception as e:
        print(f"Error reading local waitlist: {str(e)}")
        return False
    
    if not removed:
        print(f"Email {email_to_remove} not found in local waitlist")
        return False
    
    # Write the updated waitlist
    try:
        with open(local_path, 'w', encoding='utf-8') as f:
            for email in emails:
                f.write(f"{email}\n")
        print(f"Successfully removed {email_to_remove} from local waitlist")
        return True
    except Exception as e:
        print(f"Error writing updated local waitlist: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remove_email.py <email_to_remove>")
        sys.exit(1)
    
    email_to_remove = sys.argv[1]
    
    # Remove from both GitHub and local
    github_result = remove_email_from_github(email_to_remove)
    local_result = remove_email_from_local(email_to_remove)
    
    if github_result and local_result:
        print(f"Successfully removed {email_to_remove} from both GitHub and local waitlists")
    elif github_result:
        print(f"Removed {email_to_remove} from GitHub waitlist only")
    elif local_result:
        print(f"Removed {email_to_remove} from local waitlist only")
    else:
        print(f"Could not find {email_to_remove} in either waitlist")
