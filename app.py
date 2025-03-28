# Itza Yerba Mate - Waitlist Signup
from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import requests
import traceback
import base64
import json
import time
import csv
# Import the centralized email utilities
import klaviyo_utils

app = Flask(__name__)

# GitHub configuration for waitlist storage
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'drinkitza'
REPO_NAME = 'drinkitza'
FILE_PATH = 'emails/waitlist.csv'

# Simple admin authentication (for demo purposes only - use proper auth in production)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'billions')

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

def send_confirmation_email(recipient_email, next_drop=False):
    """Send the beautiful thank you email to new waitlist signups"""
    try:
        success, message = klaviyo_utils.send_waitlist_confirmation_email(recipient_email, next_drop)
        print(f"Klaviyo email result: {success}, {message}")
        return success
    except Exception as e:
        log_error(e, "send_confirmation_email")
        return False

def send_educational_email(recipient_email):
    """Send the educational email about yerba mate history and benefits"""
    try:
        success, message = klaviyo_utils.send_educational_email(recipient_email)
        print(f"Klaviyo educational email result: {success}, {message}")
        return success
    except Exception as e:
        log_error(e, "send_educational_email")
        return False

def send_brewing_guide(recipient_email):
    """Send the brewing guide email"""
    try:
        success, message = klaviyo_utils.send_brewing_guide_email(recipient_email)
        print(f"Klaviyo brewing guide email result: {success}, {message}")
        return success
    except Exception as e:
        log_error(e, "send_brewing_guide")
        return False

def send_milestone_email(recipient_email):
    """Send the 100 milestone celebration email"""
    try:
        success, message = klaviyo_utils.send_milestone_email(recipient_email)
        print(f"Klaviyo milestone email result: {success}, {message}")
        return success
    except Exception as e:
        log_error(e, "send_milestone_email")
        return False

def send_update_email(recipient_email):
    """Send an update email about ordering availability"""
    try:
        success, message = klaviyo_utils.send_update_email(recipient_email)
        print(f"Klaviyo update email result: {success}, {message}")
        return success
    except Exception as e:
        log_error(e, "send_update_email")
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

def get_all_emails_from_csv():
    """Get all emails from the local CSV file"""
    emails = []
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
    
    if not os.path.exists(csv_path):
        return emails
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'email' in row and 'timestamp' in row:
                    emails.append({
                        'email': row['email'],
                        'timestamp': row['timestamp']
                    })
    except Exception as e:
        log_error(e, "get_all_emails_from_csv")
    
    return emails

def remove_email_from_csv(email_to_remove):
    """Remove an email from the local CSV file"""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
    
    print(f"Attempting to remove email: {email_to_remove}")
    print(f"CSV path: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found at: {csv_path}")
        return False
    
    temp_path = csv_path + '.temp'
    removed = False
    
    try:
        # Read all existing emails
        all_emails = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"Reading row: {row}")
                all_emails.append(row)
        
        # Filter out the email to remove
        filtered_emails = []
        for email_data in all_emails:
            if email_data['email'].lower() != email_to_remove.lower():
                filtered_emails.append(email_data)
            else:
                removed = True
                print(f"Found and removing email: {email_to_remove}")
        
        # Write back the filtered emails
        with open(temp_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['email', 'timestamp'])
            writer.writeheader()
            for email_data in filtered_emails:
                writer.writerow(email_data)
        
        if removed:
            print(f"Email found and removed, replacing {temp_path} with {csv_path}")
            os.replace(temp_path, csv_path)
        else:
            print(f"Email not found, removing temp file: {temp_path}")
            os.remove(temp_path)
    except Exception as e:
        error_msg = log_error(e, "remove_email_from_csv")
        print(f"Error in remove_email_from_csv: {error_msg}")
        return False
    
    return removed

# Routes
@app.route('/')
def root():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')

@app.route('/waitlist')
def waitlist():
    """Serve the waitlist page"""
    return send_from_directory('.', 'waitlist.html')

@app.route('/admin')
def admin():
    """Serve the admin page"""
    return send_from_directory('.', 'admin.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files"""
    return send_from_directory('static', path)

# Admin API endpoints
@app.route('/api/admin/emails', methods=['GET'])
def admin_get_emails():
    """Get all emails in the waitlist"""
    # Authentication is now handled on the frontend
    emails = get_all_emails_from_csv()
    return jsonify({'emails': emails})

@app.route('/api/admin/resend', methods=['POST'])
def admin_resend_email():
    """Resend confirmation email to a specific address"""
    # Authentication is now handled on the frontend
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Check if email exists in waitlist
    emails = get_all_emails_from_csv()
    email_exists = any(e['email'].lower() == email.lower() for e in emails)
    
    if not email_exists:
        return jsonify({'error': 'Email not found in waitlist'}), 404
    
    # Resend confirmation email
    success = send_confirmation_email(email)
    
    if success:
        return jsonify({'message': f'Confirmation email resent to {email}'})
    else:
        return jsonify({'error': 'Failed to send confirmation email'}), 500

@app.route('/api/admin/remove', methods=['POST'])
def admin_remove_email():
    """Remove an email from the waitlist"""
    # Authentication is now handled on the frontend
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Remove from local CSV
    removed_from_csv = remove_email_from_csv(email)
    
    # Remove from GitHub (if configured)
    removed_from_github = False
    if GITHUB_TOKEN:
        try:
            # Get current content
            is_duplicate, sha = check_duplicate_email(email)
            if is_duplicate:
                # Remove the email from GitHub
                github_url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
                headers = {
                    'Authorization': f'token {GITHUB_TOKEN}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                # Get current content
                response = requests.get(github_url, headers=headers)
                if response.status_code == 200:
                    content_data = response.json()
                    current_content = base64.b64decode(content_data['content']).decode('utf-8')
                    
                    # Remove the email line
                    new_content = ''
                    for line in current_content.splitlines():
                        if not line.lower().startswith(email.lower() + ','):
                            new_content += line + '\n'
                    
                    # Update the file on GitHub
                    update_data = {
                        'message': f'Remove email {email} from waitlist',
                        'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
                        'sha': content_data['sha']
                    }
                    
                    update_response = requests.put(github_url, headers=headers, json=update_data)
                    removed_from_github = update_response.status_code in (200, 201)
        except Exception as e:
            log_error(e, "remove_email_from_github")
    
    if removed_from_csv or removed_from_github:
        return jsonify({'message': f'Email {email} removed from waitlist'})
    else:
        return jsonify({'error': 'Email not found or could not be removed'}), 404

@app.route('/api/admin/send-educational-email', methods=['POST'])
def admin_send_educational_email():
    """Send educational email to all subscribers or a specific email"""
    # Authentication is handled on the frontend
    data = request.json
    target_email = data.get('email')  # Optional, if None, send to all
    
    success_count = 0
    failure_count = 0
    
    # Read all emails from CSV
    all_emails = []
    try:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_emails.append(row['email'])
    except Exception as e:
        log_error(e, "admin_send_educational_email - reading CSV")
        return jsonify({'error': 'Failed to read email list'}), 500
    
    # If target email is specified, only send to that email
    if target_email:
        if target_email in all_emails:
            if send_educational_email(target_email):
                success_count += 1
            else:
                failure_count += 1
        else:
            return jsonify({'error': 'Email not found in waitlist'}), 404
    else:
        # Send to all emails
        for email in all_emails:
            if send_educational_email(email):
                success_count += 1
            else:
                failure_count += 1
    
    return jsonify({
        'message': f'Educational email sent to {success_count} recipients',
        'success_count': success_count,
        'failure_count': failure_count,
        'total_count': len(all_emails) if not target_email else 1
    })

@app.route('/api/admin/send-brewing-guide', methods=['POST'])
def admin_send_brewing_guide():
    """Send brewing guide email to all subscribers or a specific email"""
    # Authentication is handled on the frontend
    data = request.json
    target_email = data.get('email')  # Optional, if None, send to all
    
    success_count = 0
    failure_count = 0
    
    # Read all emails from CSV
    all_emails = []
    try:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header row if it exists
            for row in reader:
                if row and len(row) > 0 and '@' in row[0]:
                    all_emails.append(row[0])
    except Exception as e:
        log_error(e, "admin_send_brewing_guide - reading CSV")
        return jsonify({'error': f'Failed to read email list: {str(e)}'}), 500
    
    # If target email is specified, only send to that email
    if target_email:
        if send_brewing_guide(target_email):
            success_count += 1
        else:
            failure_count += 1
    else:
        # Send to all emails
        for email in all_emails:
            if send_brewing_guide(email):
                success_count += 1
            else:
                failure_count += 1
    
    return jsonify({
        'message': f'Brewing guide email sent to {success_count} recipients',
        'success_count': success_count,
        'failure_count': failure_count,
        'total_count': len(all_emails) if not target_email else 1
    })

@app.route('/api/admin/send-milestone-email', methods=['POST'])
def admin_send_milestone_email():
    """Send milestone celebration email to all subscribers or a specific email"""
    # Authentication is handled on the frontend
    data = request.json
    target_email = data.get('email')  # Optional, if None, send to all
    
    success_count = 0
    failure_count = 0
    
    # Read all emails from CSV
    all_emails = []
    try:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header row if it exists
            for row in reader:
                if row and len(row) > 0 and '@' in row[0]:
                    all_emails.append(row[0])
    except Exception as e:
        log_error(e, "admin_send_milestone_email - reading CSV")
        return jsonify({'error': f'Failed to read email list: {str(e)}'}), 500
    
    # If target email is specified, only send to that email
    if target_email:
        if send_milestone_email(target_email):
            success_count += 1
        else:
            failure_count += 1
    else:
        # Send to all emails
        for email in all_emails:
            if send_milestone_email(email):
                success_count += 1
            else:
                failure_count += 1
    
    return jsonify({
        'message': f'Milestone celebration email sent to {success_count} recipients',
        'success_count': success_count,
        'failure_count': failure_count,
        'total_count': len(all_emails) if not target_email else 1
    })

@app.route('/api/admin/send-update-email', methods=['POST'])
def admin_send_update_email():
    """Send update email to all subscribers or a specific email"""
    # Authentication is handled on the frontend
    data = request.json
    target_email = data.get('email')  # Optional, if None, send to all
    
    success_count = 0
    failure_count = 0
    
    # Read all emails from CSV
    all_emails = []
    try:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header row if it exists
            for row in reader:
                if row and len(row) > 0 and '@' in row[0]:
                    all_emails.append(row[0])
    except Exception as e:
        log_error(e, "admin_send_update_email - reading CSV")
        return jsonify({'error': f'Failed to read email list: {str(e)}'}), 500
    
    # If target email is specified, only send to that email
    if target_email:
        success, _ = send_update_email(target_email)
        if success:
            success_count += 1
        else:
            failure_count += 1
    else:
        # Send to all emails
        for email in all_emails:
            success, _ = send_update_email(email)
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
    
    return jsonify({
        'message': f'Update email sent to {success_count} recipients',
        'success_count': success_count,
        'failure_count': failure_count,
        'total_count': len(all_emails) if not target_email else 1
    })

@app.route('/api/waitlist', methods=['POST'])
def submit_email():
    """Handle email submission for waitlist"""
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400

        email = data['email'].strip().lower()
        print(f"Processing email submission for: {email}")
        
        # Check if this is for the next drop waitlist
        next_drop = data.get('next_drop', True)  # Default to next drop since we're sold out
        
        # Save email to GitHub
        result = save_to_github(email)
        
        if result == 'duplicate':
            return jsonify({
                'status': 'already_registered',
                'message': "You're already on our waitlist!"
            })
        elif result == 'success' or result == 'error':
            # Even if GitHub save failed, we still try to send confirmation
            if send_confirmation_email(email, next_drop):
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
