# Version 2.3 - Add email confirmation
from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import requests
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import csv
from io import StringIO

app = Flask(__name__)

# GitHub configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'drinkitza'
REPO_NAME = 'drinkitza'
FILE_PATH = 'emails/waitlist.csv'

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SENDER_EMAIL')  # Your Gmail address
SENDER_PASSWORD = os.getenv('SENDER_APP_PASSWORD')  # Your Gmail App Password

def send_confirmation_email(recipient_email):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Welcome to Itza's Waitlist!"

        # Email content
        body = """
        Thank you for joining Itza's waitlist!

        We're excited to have you on board. We'll notify you as soon as we launch.

        Best regards,
        The Itza Team
        """
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False

def sync_local_csv():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(['git', 'pull'], cwd=current_dir, check=True)
        return True
    except Exception as e:
        print(f"Error syncing local CSV: {e}")
        return False

def get_current_emails():
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
            reader = csv.reader(StringIO(content))
            emails = {row[0].lower() for row in reader if row}  # Use set for O(1) lookup
            return emails, current_file.get('sha')
    except Exception as e:
        print(f"Error getting current emails: {e}")
    
    return set(), None

def save_to_github(email):
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        # Get current emails and check for duplicates
        current_emails, sha = get_current_emails()
        if email.lower() in current_emails:
            return 'duplicate'
        
        # Add new email
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_content = f'{email},{timestamp}\n'
        
        if current_emails:
            # Reconstruct the file content with the new email
            content = '\n'.join(f'{email},{timestamp}' for email, timestamp in 
                              [line.split(',') for line in 
                               base64.b64decode(requests.get(url, headers=headers).json()['content'])
                               .decode('utf-8').splitlines() if line.strip()])
            new_content = content + '\n' + new_content
        
        # Update file
        data = {
            'message': f'Add email: {email}',
            'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            'sha': sha
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Sync local CSV after successful GitHub update
        sync_local_csv()
        return 'success'
        
    except Exception as e:
        print(f"GitHub Error: {e}")
        return 'error'

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/api/waitlist', methods=['POST', 'OPTIONS'])
def submit_email():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400

        email = data['email'].strip().lower()
        
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
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to save email'}), 500

if __name__ == '__main__':
    app.run(debug=True)
