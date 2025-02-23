# Version 2.3.2 - Fix GitHub integration
from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import requests
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import base64

app = Flask(__name__)

# GitHub configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'drinkitza'
REPO_NAME = 'drinkitza'
FILE_PATH = 'emails/waitlist.csv'

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_APP_PASSWORD')

def log_error(e, context=""):
    error_msg = f"""
    Error in {context}:
    Type: {type(e).__name__}
    Message: {str(e)}
    Traceback:
    {traceback.format_exc()}
    """
    print(error_msg)
    return error_msg

def send_confirmation_email(recipient_email):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Welcome to Itza's Waitlist!"

        body = """
        Thank you for joining Itza's waitlist!

        We're excited to have you on board. We'll notify you as soon as we launch.

        Best regards,
        The Itza Team
        """
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        log_error(e, "send_confirmation_email")
        return False

def sync_local_csv():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(['git', 'pull'], cwd=current_dir, check=True)
        return True
    except Exception as e:
        log_error(e, "sync_local_csv")
        return False

def check_duplicate_email(email):
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        current_file = response.json()
        
        if 'content' in current_file:
            content = base64.b64decode(current_file['content']).decode('utf-8')
            emails = [line.split(',')[0].lower() for line in content.splitlines() if line.strip()]
            return email.lower() in emails, current_file.get('sha')
        return False, current_file.get('sha')
    except Exception as e:
        log_error(e, "check_duplicate_email")
        return False, None

def save_to_github(email):
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        # Check for duplicates
        is_duplicate, sha = check_duplicate_email(email)
        if is_duplicate:
            return 'duplicate'
        
        # Get current content
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        current_file = response.json()
        
        # Add new email
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_email_line = f'{email},{timestamp}\n'
        
        if 'content' in current_file:
            content = base64.b64decode(current_file['content']).decode('utf-8')
            new_content = content + new_email_line
        else:
            new_content = new_email_line
        
        # Update file
        data = {
            'message': f'Add email: {email}',
            'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            'sha': sha
        }
        
        update_response = requests.put(url, headers=headers, json=data)
        update_response.raise_for_status()
        
        # Sync local CSV after successful GitHub update
        sync_local_csv()
        return 'success'
        
    except Exception as e:
        error_msg = log_error(e, "save_to_github")
        print(f"GitHub Token (first/last 4): {GITHUB_TOKEN[:4]}...{GITHUB_TOKEN[-4:]}")
        print(f"Response status: {getattr(response, 'status_code', 'N/A')}")
        print(f"Response content: {getattr(response, 'text', 'N/A')}")
        return 'error'

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/api/waitlist', methods=['POST'])
def submit_email():
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400

        email = data['email'].strip().lower()
        print(f"Processing email submission for: {email}")
        
        # Save email to GitHub
        result = save_to_github(email)
        
        if result == 'duplicate':
            return jsonify({
                'status': 'already_registered',
                'message': "You're already on our waitlist!"
            })
        elif result == 'success':
            # Send confirmation email
            if send_confirmation_email(email):
                return jsonify({
                    'status': 'success',
                    'message': "You're on the waitlist! Check your email for confirmation."
                })
            else:
                return jsonify({
                    'status': 'partial_success',
                    'message': "You're on the waitlist! (Email confirmation failed)"
                })
        else:
            return jsonify({'error': 'Failed to save email'}), 500

    except Exception as e:
        error_msg = log_error(e, "submit_email")
        return jsonify({'error': 'Failed to save email', 'details': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True)
