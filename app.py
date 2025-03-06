# Itza Yerba Mate - Waitlist Signup
from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import base64
import json
import time

app = Flask(__name__)

# GitHub configuration for waitlist storage
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'drinkitza'
REPO_NAME = 'drinkitza'
FILE_PATH = 'emails/waitlist.csv'

# Email configuration - SMTP fallback
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'drinkitza@gmail.com')
SENDER_APP_PASSWORD = os.getenv('SENDER_APP_PASSWORD', '')

# EmailJS configuration (primary method)
EMAIL_SERVICE_URL = os.getenv('EMAIL_SERVICE_URL')
EMAIL_SERVICE_USER_ID = os.getenv('EMAIL_SERVICE_USER_ID')
EMAIL_SERVICE_TEMPLATE_ID = os.getenv('EMAIL_SERVICE_TEMPLATE_ID')
EMAIL_SERVICE_ACCESS_TOKEN = os.getenv('EMAIL_SERVICE_ACCESS_TOKEN')

def log_error(e, context=""):
    """Log errors with context for easier debugging"""
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
    """Send the beautiful thank you email to new waitlist signups"""
    try:
        # First try EmailJS (primary method)
        if EMAIL_SERVICE_URL and EMAIL_SERVICE_USER_ID and EMAIL_SERVICE_TEMPLATE_ID:
            try:
                emailjs_data = {
                    'service_id': EMAIL_SERVICE_URL,
                    'template_id': EMAIL_SERVICE_TEMPLATE_ID,
                    'user_id': EMAIL_SERVICE_USER_ID,
                    'template_params': {
                        'to_email': recipient_email,
                        'email': recipient_email  # For template replacement
                    },
                    'accessToken': EMAIL_SERVICE_ACCESS_TOKEN
                }
                
                headers = {'Content-Type': 'application/json'}
                response = requests.post(
                    'https://api.emailjs.com/api/v1.0/email/send',
                    headers=headers,
                    json=emailjs_data
                )
                
                if response.status_code == 200:
                    print(f"Email sent successfully to {recipient_email} via EmailJS")
                    return True
                else:
                    print(f"EmailJS sending failed with status {response.status_code}: {response.text}")
                    # Fall back to SMTP or queue
            except Exception as e:
                print(f"EmailJS error: {str(e)}")
                # Fall back to SMTP or queue
        
        # Create a multipart message for SMTP or queue
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Thanks for Joining Itza Yerba Mate's Pre-order Waitlist!"

        # Read the HTML template
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'confirmation_template.html')
        
        if not os.path.exists(template_path):
            print(f"Warning: Email template not found at {template_path}")
            html_content = "<p>Thanks for joining Itza Yerba Mate's pre-order waitlist!</p>"
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        
        # Replace placeholders
        html_content = html_content.replace('{{email}}', recipient_email)
        
        # Create HTML version
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Try to send email via SMTP as second option
        if SENDER_APP_PASSWORD:
            try:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                server.send_message(msg)
                server.quit()
                print(f"Email sent successfully to {recipient_email} via SMTP")
                return True
            except Exception as e:
                print(f"SMTP sending failed: {str(e)}")
                # Fall back to queue
        
        # Queue the email if both EmailJS and SMTP fail
        queue_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'queue')
        os.makedirs(queue_dir, exist_ok=True)
        
        email_data = {
            'to': recipient_email,
            'from': SENDER_EMAIL,
            'subject': msg['Subject'],
            'html': html_content
        }
        
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{recipient_email.replace('@', '_at_')}.json"
        filepath = os.path.join(queue_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2)
        
        print(f"Email queued for {recipient_email} at {filepath}")
        return True
        
    except Exception as e:
        log_error(e, "send_confirmation_email")
        return False

def check_duplicate_email(email):
    """Check if email already exists in the waitlist"""
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
    """Save email to GitHub repository"""
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
        
        # Also save to local CSV for backup
        save_to_local_csv(email, timestamp)
        return 'success'
        
    except Exception as e:
        error_msg = log_error(e, "save_to_github")
        # Try to save locally as fallback
        save_to_local_csv(email)
        return 'error'

def save_to_local_csv(email, timestamp=None):
    """Save email to local CSV file as backup"""
    try:
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        with open(csv_path, 'a', encoding='utf-8') as f:
            f.write(f'{email},{timestamp}\n')
        return True
    except Exception as e:
        log_error(e, "save_to_local_csv")
        return False

# Routes
@app.route('/')
def root():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')

@app.route('/waitlist')
def waitlist():
    """Serve the waitlist page"""
    return send_from_directory('.', 'waitlist.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/waitlist', methods=['POST'])
def submit_email():
    """Handle email submission for waitlist"""
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
        elif result == 'success' or result == 'error':
            # Even if GitHub save failed, we still try to send confirmation
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
