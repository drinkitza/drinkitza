#!/usr/bin/env python
# Itza Yerba Mate - Email Queue Processor
# This script processes any emails that were queued due to sending failures

import os
import json
import time
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# Email configuration - SMTP fallback
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'drinkitza@gmail.com'
SENDER_APP_PASSWORD = ''

# EmailJS configuration (primary method)
EMAIL_SERVICE_URL = 'https://api.emailjs.com/api/v1.0/email/send'
EMAIL_SERVICE_USER_ID = 'user_7vN9gJQJbgGZR5LpJqRBt'
EMAIL_SERVICE_TEMPLATE_ID = 'template_confirmation'
EMAIL_SERVICE_ACCESS_TOKEN = ''
EMAIL_SERVICE_ID = 'service_itza'

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

def send_email_via_emailjs(to_email, html_content):
    """Send email using EmailJS service"""
    try:
        if not all([EMAIL_SERVICE_URL, EMAIL_SERVICE_USER_ID, EMAIL_SERVICE_TEMPLATE_ID]):
            return False, "EmailJS configuration incomplete"
        
        emailjs_data = {
            'service_id': EMAIL_SERVICE_ID,
            'template_id': EMAIL_SERVICE_TEMPLATE_ID,
            'user_id': EMAIL_SERVICE_USER_ID,
            'template_params': {
                'to_email': to_email,
                'email': to_email  # For template replacement
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
            print(f"Email sent successfully to {to_email} via EmailJS")
            return True, "Success"
        else:
            error_msg = f"EmailJS sending failed with status {response.status_code}: {response.text}"
            print(error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = log_error(e, "send_email_via_emailjs")
        return False, error_msg

def send_email_via_smtp(to_email, subject, html_content):
    """Send email using SMTP"""
    try:
        if not SENDER_APP_PASSWORD:
            return False, "SMTP password not configured"
        
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email} via SMTP")
        return True, "Success"
    except Exception as e:
        error_msg = log_error(e, "send_email_via_smtp")
        return False, error_msg

def process_queue():
    """Process all queued emails"""
    queue_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'queue')
    processed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'processed')
    failed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'failed')
    
    # Create directories if they don't exist
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(failed_dir, exist_ok=True)
    
    if not os.path.exists(queue_dir):
        print(f"Queue directory not found: {queue_dir}")
        return
    
    # Get all queued email files
    queued_files = [f for f in os.listdir(queue_dir) if f.endswith('.json')]
    
    if not queued_files:
        print("No emails in queue")
        return
    
    print(f"Found {len(queued_files)} emails in queue")
    
    for filename in queued_files:
        filepath = os.path.join(queue_dir, filename)
        
        try:
            # Read email data
            with open(filepath, 'r', encoding='utf-8') as f:
                email_data = json.load(f)
            
            to_email = email_data.get('to')
            subject = email_data.get('subject', "Thanks for Joining Itza Yerba Mate's Pre-order Waitlist!")
            html_content = email_data.get('html', '')
            
            print(f"Processing email to {to_email}")
            
            # Try EmailJS first
            success, message = send_email_via_emailjs(to_email, html_content)
            
            # If EmailJS fails, try SMTP
            if not success:
                print(f"EmailJS failed: {message}. Trying SMTP...")
                success, message = send_email_via_smtp(to_email, subject, html_content)
            
            # Move file to appropriate directory
            if success:
                target_dir = processed_dir
                print(f"Successfully sent email to {to_email}")
            else:
                target_dir = failed_dir
                print(f"Failed to send email to {to_email}: {message}")
            
            target_path = os.path.join(target_dir, filename)
            os.rename(filepath, target_path)
            
        except Exception as e:
            log_error(e, f"processing {filename}")
            # Move to failed directory
            try:
                failed_path = os.path.join(failed_dir, filename)
                os.rename(filepath, failed_path)
            except Exception as move_error:
                log_error(move_error, f"moving {filename} to failed directory")

if __name__ == "__main__":
    print("Starting email queue processing...")
    process_queue()
    print("Email queue processing complete")
