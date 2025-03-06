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
EMAIL_SERVICE_URL = os.getenv('EMAIL_SERVICE_URL', 'https://api.emailjs.com/api/v1.0/email/send')
EMAIL_SERVICE_USER_ID = os.getenv('EMAIL_SERVICE_USER_ID', 'your_user_id')
EMAIL_SERVICE_TEMPLATE_ID = os.getenv('EMAIL_SERVICE_TEMPLATE_ID', 'your_template_id')
EMAIL_SERVICE_ACCESS_TOKEN = os.getenv('EMAIL_SERVICE_ACCESS_TOKEN', 'your_access_token')

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
        # Read the HTML template
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'confirmation_template.html')
        print(f"Loading email template from: {template_path}")
        
        if not os.path.exists(template_path):
            print(f"Warning: Email template not found at {template_path}")
            # Fallback to simple HTML if template is missing
            html_content = f"""
            <html>
            <body>
                <h1>Thanks for Joining Itza Yerba Mate's Pre-order Waitlist!</h1>
                <p>We're excited to have you join our tribe of natural energy seekers.</p>
                <p>Itza is nature's pre-workout - no powders, no bullshit, just as the gods intended.</p>
                <p>Best regards,<br>The Itza Team</p>
            </body>
            </html>
            """
        else:
            with open(template_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
                print(f"Email template loaded successfully ({len(html_content)} characters)")
            
        # Replace placeholder with recipient email
        html_content = html_content.replace('{{email}}', recipient_email)
        
        # Option 1: Use EmailJS service (no password required, but needs account setup)
        try:
            # Prepare the payload for EmailJS
            payload = {
                'user_id': EMAIL_SERVICE_USER_ID,
                'service_id': 'default_service',
                'template_id': EMAIL_SERVICE_TEMPLATE_ID,
                'template_params': {
                    'to_email': recipient_email,
                    'html_content': html_content
                },
                'accessToken': EMAIL_SERVICE_ACCESS_TOKEN
            }
            
            # Send the request to EmailJS
            response = requests.post(EMAIL_SERVICE_URL, json=payload)
            
            if response.status_code == 200:
                print(f"Email sent successfully to {recipient_email} via EmailJS!")
                return True
            else:
                print(f"Failed to send email via EmailJS: {response.text}")
                # Fall back to option 2 if EmailJS fails
                raise Exception("EmailJS failed, falling back to alternative method")
                
        except Exception as e:
            print(f"EmailJS error: {str(e)}")
            # Fall back to option 2
            
            # Option 2: Store the email in a queue file for processing later
            # This approach doesn't send the email immediately but stores it for later sending
            queue_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'queue')
            os.makedirs(queue_dir, exist_ok=True)
            
            email_data = {
                'to': recipient_email,
                'subject': "Thanks for Joining Itza Yerba Mate's Pre-order Waitlist!",
                'html': html_content,
                'timestamp': datetime.now().isoformat()
            }
            
            # Create a unique filename
            filename = f"{int(datetime.now().timestamp())}_{recipient_email.replace('@', '_at_')}.json"
            file_path = os.path.join(queue_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(email_data, f)
                
            print(f"Email queued for later sending: {file_path}")
            return True
            
    except Exception as e:
        log_error(e, "send_confirmation_email")
        print(f"Failed to send confirmation email to {recipient_email}: {str(e)}")
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

@app.route('/test')
def test_form():
    return send_from_directory('.', 'test_form.html')

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
