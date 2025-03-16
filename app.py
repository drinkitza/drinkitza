# Itza Yerba Mate - Waitlist Signup
from flask import Flask, request, jsonify, send_from_directory, render_template
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
import csv
import stripe

# Load environment variables from .env file if present
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

app = Flask(__name__)

# Stripe configuration
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Initialize Stripe
if not STRIPE_PUBLISHABLE_KEY or not STRIPE_SECRET_KEY:
    print("Warning: Stripe API keys not found in environment variables.")
    print("Please set STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY in your .env file or Vercel environment variables.")

stripe.api_key = STRIPE_SECRET_KEY

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

def send_confirmation_email(recipient_email, order_type=None, items=None):
    """Send the beautiful thank you email to new waitlist signups or order confirmations"""
    try:
        # First try EmailJS (primary method)
        email_service_url = os.getenv('EMAIL_SERVICE_URL', 'https://api.emailjs.com/api/v1.0/email/send')
        email_service_user_id = os.getenv('EMAIL_SERVICE_USER_ID')
        email_service_access_token = os.getenv('EMAIL_SERVICE_ACCESS_TOKEN')
        
        # Select the appropriate template based on order_type
        if order_type == "stripe":
            # Order confirmation template
            email_service_template_id = os.getenv('EMAIL_ORDER_TEMPLATE_ID', os.getenv('EMAIL_SERVICE_TEMPLATE_ID'))
            subject = "Your Itza Yerba Mate Order Confirmation"
            
            # Format items for the email
            items_html = ""
            total = 0
            
            if items:
                for item in items:
                    name = item.get('name', 'Product')
                    price = item.get('price', 0)
                    quantity = item.get('quantity', 1)
                    item_total = price * quantity
                    total += item_total
                    
                    price_display = "FREE" if price == 0 else f"${price/100:.2f}"
                    items_html += f"<tr><td>{name}</td><td>{quantity}</td><td>{price_display}</td></tr>"
                
                items_html = f"""
                <table border="0" cellpadding="8" cellspacing="0" style="width:100%">
                    <tr style="background-color:#f8f8f8">
                        <th align="left">Product</th>
                        <th align="left">Qty</th>
                        <th align="left">Price</th>
                    </tr>
                    {items_html}
                    <tr style="font-weight:bold">
                        <td colspan="2" align="right">Total:</td>
                        <td>${total/100:.2f}</td>
                    </tr>
                </table>
                """
            
            message = f"""
            <h2>Thank you for your order!</h2>
            <p>We're excited to bring you the authentic taste of Itza Yerba Mate with our premium loose leaf tea and traditional drinking accessories.</p>
            {items_html}
            <p>Your order will be shipped soon. We'll send you tracking information once it's on the way.</p>
            <p>Enjoy the natural ingredients in our yerba mate: yerba mate, ginger, mint, lemon peel, ginseng, and star anise.</p>
            """
        else:
            # Waitlist confirmation template (original behavior)
            email_service_template_id = os.getenv('EMAIL_SERVICE_TEMPLATE_ID')
            subject = "Welcome to the Itza Yerba Mate Waitlist!"
            message = """
            <h2>Thank you for joining our waitlist!</h2>
            <p>We're excited to bring you the authentic taste of Itza Yerba Mate.</p>
            <p>Our yerba mate features natural ingredients: yerba mate, ginger, mint, lemon peel, ginseng, and star anise.</p>
            <p>We'll notify you as soon as we launch!</p>
            """
        
        if email_service_user_id and email_service_template_id:
            payload = {
                'service_id': 'default_service',
                'template_id': email_service_template_id,
                'user_id': email_service_user_id,
                'accessToken': email_service_access_token,
                'template_params': {
                    'to_email': recipient_email,
                    'subject': subject,
                    'message': message
                }
            }
            
            response = requests.post(email_service_url, json=payload)
            
            if response.status_code == 200:
                print(f"Email sent successfully to {recipient_email}")
                return True
            else:
                print(f"Failed to send email via EmailJS: {response.text}")
                # Fall back to queue system
        
        # Fall back to queue system if EmailJS fails or is not configured
        queue_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'queue')
        os.makedirs(queue_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"{timestamp}_{recipient_email.replace('@', '_at_')}.json"
        file_path = os.path.join(queue_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'email': recipient_email,
                'timestamp': timestamp,
                'subject': subject,
                'message': message,
                'order_type': order_type,
                'items': items
            }, f)
        
        print(f"Email queued for {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_educational_email(recipient_email):
    """Send the educational email about yerba mate history and benefits"""
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
        msg['Subject'] = "Discover the Magic of Yerba Mate - Itza's Educational Guide"

        # Read the HTML template
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'educational_template.html')
        
        if not os.path.exists(template_path):
            print(f"Warning: Educational email template not found at {template_path}")
            html_content = "<p>Learn about the amazing benefits of yerba mate!</p>"
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
                print(f"Educational email sent successfully to {recipient_email} via SMTP")
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
        
        print(f"Educational email queued for {recipient_email} at {filepath}")
        return True
        
    except Exception as e:
        log_error(e, "send_educational_email")
        return False

def send_brewing_guide(recipient_email):
    """Send the brewing guide email"""
    try:
        # First try EmailJS (primary method)
        if EMAIL_SERVICE_URL and EMAIL_SERVICE_USER_ID and EMAIL_SERVICE_TEMPLATE_ID and EMAIL_SERVICE_ACCESS_TOKEN:
            try:
                # Read the HTML template
                template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'brewing_guide_template.html')
                
                if not os.path.exists(template_path):
                    print(f"Warning: Brewing guide email template not found at {template_path}")
                    html_content = "<p>Learn how to brew yerba mate!</p>"
                else:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                
                # Replace placeholders
                html_content = html_content.replace('{{email}}', recipient_email)
                
                emailjs_data = {
                    'service_id': EMAIL_SERVICE_URL,
                    'template_id': EMAIL_SERVICE_TEMPLATE_ID,
                    'user_id': EMAIL_SERVICE_USER_ID,
                    'template_params': {
                        'to_email': recipient_email,
                        'subject': "How to Brew Yerba Mate + FREE Gourd & Bombilla Offer!",
                        'html_content': html_content
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
                    print(f"Brewing guide email sent successfully to {recipient_email} via EmailJS")
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
        msg['Subject'] = "How to Brew Yerba Mate + FREE Gourd & Bombilla Offer!"

        # Read the HTML template
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'brewing_guide_template.html')
        
        if not os.path.exists(template_path):
            print(f"Warning: Brewing guide email template not found at {template_path}")
            html_content = "<p>Learn how to brew yerba mate!</p>"
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        
        # Replace placeholders
        html_content = html_content.replace('{{email}}', recipient_email)
        
        # Create HTML version
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Try to send email via SMTP as second option
        if SENDER_EMAIL and SENDER_APP_PASSWORD:
            try:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                server.send_message(msg)
                server.quit()
                print(f"Brewing guide email sent successfully to {recipient_email} via SMTP")
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
            'html': html_content,
            'type': 'brewing_guide'
        }
        
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_brewing_guide_{recipient_email.replace('@', '_at_')}.json"
        filepath = os.path.join(queue_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2)
        
        print(f"Brewing guide email queued for {recipient_email} at {filepath}")
        return True
        
    except Exception as e:
        print(f"Error sending brewing guide email: {str(e)}")
        log_error(e, "send_brewing_guide")
        return False

def send_milestone_email(recipient_email):
    """Send the 100 milestone celebration email"""
    try:
        # First try EmailJS (primary method)
        if EMAIL_SERVICE_URL and EMAIL_SERVICE_USER_ID and EMAIL_SERVICE_TEMPLATE_ID and EMAIL_SERVICE_ACCESS_TOKEN:
            try:
                # Read the HTML template
                template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'milestone_template.html')
                
                if not os.path.exists(template_path):
                    print(f"Warning: Milestone email template not found at {template_path}")
                    html_content = "<p>Congratulations on being part of our first 100 customers!</p>"
                else:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                
                # Replace placeholders
                html_content = html_content.replace('{{email}}', recipient_email)
                
                emailjs_data = {
                    'service_id': EMAIL_SERVICE_URL,
                    'template_id': EMAIL_SERVICE_TEMPLATE_ID,
                    'user_id': EMAIL_SERVICE_USER_ID,
                    'template_params': {
                        'to_email': recipient_email,
                        'subject': "Celebrating 100 Customers! Your Free Gift is Confirmed",
                        'html_content': html_content
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
                    print(f"Milestone email sent successfully to {recipient_email} via EmailJS")
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
        msg['Subject'] = "Celebrating 100 Customers! Your Free Gift is Confirmed"

        # Read the HTML template
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'milestone_template.html')
        
        if not os.path.exists(template_path):
            print(f"Warning: Milestone email template not found at {template_path}")
            html_content = "<p>Congratulations on being part of our first 100 customers!</p>"
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        
        # Replace placeholders
        html_content = html_content.replace('{{email}}', recipient_email)
        
        # Create HTML version
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Try to send email via SMTP as second option
        if SENDER_EMAIL and SENDER_APP_PASSWORD:
            try:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                server.send_message(msg)
                server.quit()
                print(f"Milestone email sent successfully to {recipient_email} via SMTP")
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
            'html': html_content,
            'type': 'milestone'
        }
        
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_milestone_{recipient_email.replace('@', '_at_')}.json"
        filepath = os.path.join(queue_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2)
        
        print(f"Milestone email queued for {recipient_email} at {filepath}")
        return True
        
    except Exception as e:
        print(f"Error sending milestone email: {str(e)}")
        log_error(e, "send_milestone_email")
        return False

def send_update_email(recipient_email):
    """Send an update email about ordering availability"""
    try:
        # First try to send via EmailJS
        if EMAIL_SERVICE_URL and EMAIL_SERVICE_USER_ID and EMAIL_SERVICE_TEMPLATE_ID and EMAIL_SERVICE_ACCESS_TOKEN:
            # Read the update email template
            with open('emails/update_template.html', 'r', encoding='utf-8') as file:
                template_content = file.read()
            
            # Replace placeholders with actual values
            email_content = template_content.replace('{{email}}', recipient_email)
            
            # Prepare the EmailJS payload
            payload = {
                'service_id': 'service_itza',
                'template_id': 'template_update',
                'user_id': EMAIL_SERVICE_USER_ID,
                'accessToken': EMAIL_SERVICE_ACCESS_TOKEN,
                'template_params': {
                    'to_email': recipient_email,
                    'html_content': email_content,
                    'subject': 'IMPORTANT: Ordering Available Tomorrow - Itza Yerba Mate'
                }
            }
            
            # Send the request to EmailJS
            response = requests.post(EMAIL_SERVICE_URL, json=payload)
            
            if response.status_code == 200:
                print(f"Update email sent to {recipient_email} via EmailJS")
                return True, "Email sent successfully via EmailJS"
            else:
                print(f"Failed to send update email via EmailJS: {response.text}")
                # Fall back to SMTP
        
        # If EmailJS fails or is not configured, try SMTP
        if SENDER_EMAIL and SENDER_APP_PASSWORD:
            # Create the email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'IMPORTANT: Ordering Available Tomorrow - Itza Yerba Mate'
            msg['From'] = SENDER_EMAIL
            msg['To'] = recipient_email
            
            # Read the update email template
            with open('emails/update_template.html', 'r', encoding='utf-8') as file:
                template_content = file.read()
            
            # Replace placeholders with actual values
            email_content = template_content.replace('{{email}}', recipient_email)
            
            # Attach the HTML content
            msg.attach(MIMEText(email_content, 'html'))
            
            # Connect to the SMTP server and send the email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                server.send_message(msg)
            
            print(f"Update email sent to {recipient_email} via SMTP")
            return True, "Email sent successfully via SMTP"
        
        # If both EmailJS and SMTP fail, save to queue
        queue_dir = os.path.join('emails', 'queue')
        os.makedirs(queue_dir, exist_ok=True)
        
        # Generate a unique filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"update_{timestamp}_{recipient_email.replace('@', '_at_')}.html"
        filepath = os.path.join(queue_dir, filename)
        
        # Read the update email template
        with open('emails/update_template.html', 'r', encoding='utf-8') as file:
            template_content = file.read()
        
        # Replace placeholders with actual values
        email_content = template_content.replace('{{email}}', recipient_email)
        
        # Save the email to the queue
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(email_content)
        
        print(f"Update email queued for {recipient_email}")
        return False, "Email queued for later delivery"
    
    except Exception as e:
        error_msg = log_error(e, "send_update_email")
        return False, f"Failed to send update email: {str(e)}"

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

@app.route('/checkout')
def checkout():
    """Serve the checkout page"""
    return send_from_directory('.', 'checkout.html')

@app.route('/order-confirmation')
def order_confirmation():
    """Serve the order confirmation page"""
    return send_from_directory('.', 'order-confirmation.html')

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

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """Process a payment through Stripe"""
    try:
        data = request.json
        payment_method_id = data.get('paymentMethodId')
        amount = data.get('amount', 2479)  # Default to $24.79 in cents
        currency = data.get('currency', 'usd')
        country = data.get('country', 'US')
        email = data.get('email')
        
        # Create metadata for the order items
        metadata = {
            'product_1': 'Itza Yerba Mate Loose Leaf - $24.79',
            'product_2': 'Traditional Mate Gourd - FREE',
            'product_3': 'Stainless Steel Bombilla - FREE',
            'total_amount': '$24.79'
        }
        
        # Set automatic_payment_methods to True to enable Express Checkout options
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
            metadata=metadata,
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'always'
            },
            receipt_email=email
        )
        
        if payment_intent.status == 'requires_action':
            # The payment requires additional actions, such as 3D Secure authentication
            return jsonify({
                'requires_action': True,
                'clientSecret': payment_intent.client_secret,
                'paymentIntentId': payment_intent.id
            })
        elif payment_intent.status == 'succeeded':
            # The payment was successful
            return jsonify({
                'success': True
            })
        else:
            # The payment failed for some other reason
            return jsonify({
                'error': 'Payment failed. Please try again.'
            })
    except stripe.error.CardError as e:
        # The card was declined
        return jsonify({
            'error': e.user_message
        })
    except Exception as e:
        # Something else went wrong
        return jsonify({
            'error': str(e)
        })

@app.route('/api/payment-methods', methods=['GET'])
def get_payment_methods():
    """
    Get available payment methods based on country and currency
    """
    country = request.args.get('country', 'US')
    currency = request.args.get('currency', 'usd')
    
    # Get available payment methods for the country and currency
    payment_methods = {
        'card': True,  # Cards are available everywhere
        'apple_pay': True,  # Enable Apple Pay
        'google_pay': True,  # Enable Google Pay
        'link': True,  # Enable Link (Stripe's saved payment info)
    }
    
    # Add country-specific payment methods
    if country == 'US':
        payment_methods['afterpay_clearpay'] = currency.lower() in ['usd', 'aud', 'cad', 'nzd', 'gbp']
    elif country in ['GB', 'FR', 'DE', 'ES', 'IT', 'NL', 'BE', 'AT']:
        payment_methods['klarna'] = True
    elif country in ['AU', 'NZ']:
        payment_methods['afterpay_clearpay'] = True
    
    return jsonify(payment_methods)

@app.route('/api/config', methods=['GET'])
def get_stripe_config():
    """Return the Stripe publishable key to the frontend"""
    return jsonify({
        'publishableKey': STRIPE_PUBLISHABLE_KEY
    })

@app.route('/api/confirm-payment', methods=['POST'])
def confirm_payment():
    """Confirm a payment after a required action like 3D Secure authentication"""
    try:
        data = request.json
        payment_intent_id = data.get('paymentIntentId')
        
        if not payment_intent_id:
            return jsonify({'error': 'Payment intent ID is required'}), 400
        
        # Retrieve and confirm the PaymentIntent
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Check if the payment intent needs confirmation
        if intent.status == 'requires_confirmation':
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
        
        # Handle different payment statuses
        if intent.status == 'succeeded':
            # Payment was successful
            return jsonify({
                'success': True,
                'status': intent.status
            })
        elif intent.status == 'requires_action':
            # Further action is needed
            return jsonify({
                'requires_action': True,
                'status': intent.status,
                'clientSecret': intent.client_secret,
                'paymentIntentId': intent.id
            })
        else:
            # Other status (processing, etc.)
            return jsonify({
                'success': True,
                'status': intent.status
            })
            
    except stripe.error.CardError as e:
        return jsonify({'error': e.user_message}), 400
    except Exception as e:
        log_error(e, "confirm_payment")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
