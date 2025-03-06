import os
import json
from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import sys
import time

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'drinkitza@gmail.com')
SENDER_APP_PASSWORD = os.getenv('SENDER_APP_PASSWORD', '')

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
        # Create a multipart message
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Thanks for Joining Itza Yerba Mate's Pre-order Waitlist!"

        # Read the HTML template
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'confirmation_template.html')
        print(f"Loading email template from: {template_path}")
        
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
        
        # Try to send email via SMTP
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
        
        # Queue the email if SMTP fails or no password
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

def add_to_local_waitlist(email):
    """Add email directly to the local waitlist file"""
    from datetime import datetime
    
    waitlist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        with open(waitlist_path, 'a', encoding='utf-8') as f:
            f.write(f"{email},{timestamp}\n")
        print(f"Added {email} to local waitlist")
        return True
    except Exception as e:
        print(f"Error adding to local waitlist: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bypass_duplicate_check.py <email>")
        sys.exit(1)
    
    email = sys.argv[1].strip().lower()
    print(f"Processing email: {email}")
    
    # Add to local waitlist
    add_to_local_waitlist(email)
    
    # Send confirmation email
    if send_confirmation_email(email):
        print(f"Success! Added {email} to waitlist and sent confirmation email")
    else:
        print(f"Added {email} to waitlist but failed to send confirmation email")
