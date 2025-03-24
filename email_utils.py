"""
Itza Yerba Mate - Email Utilities
Centralized module for all email-related functionality
"""
import os
import json
import time
import requests
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'drinkitza@gmail.com')
SENDER_APP_PASSWORD = os.getenv('SENDER_APP_PASSWORD', '')

# EmailJS configuration
EMAIL_SERVICE_URL = os.getenv('EMAIL_SERVICE_URL')
EMAIL_SERVICE_USER_ID = os.getenv('EMAIL_SERVICE_USER_ID')
EMAIL_SERVICE_TEMPLATE_ID = os.getenv('EMAIL_SERVICE_TEMPLATE_ID')
EMAIL_SERVICE_ACCESS_TOKEN = os.getenv('EMAIL_SERVICE_ACCESS_TOKEN')

# Email queue directory
EMAIL_QUEUE_DIR = os.path.join('emails', 'queue')
PROCESSED_DIR = os.path.join('emails', 'processed')
FAILED_DIR = os.path.join('emails', 'failed')

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

def ensure_directories():
    """Ensure all required email directories exist"""
    for directory in [EMAIL_QUEUE_DIR, PROCESSED_DIR, FAILED_DIR]:
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), directory), exist_ok=True)

def create_message(recipient_email, template_type='confirmation'):
    """Create a multipart email message with the appropriate template
    
    Args:
        recipient_email: The email address of the recipient
        template_type: The type of template to use (confirmation, educational, etc.)
        
    Returns:
        MIMEMultipart message object
    """
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    
    # Set subject based on template type
    subjects = {
        'confirmation': "Thanks for Joining Itza Yerba Mate's Pre-order Waitlist!",
        'educational': "Discover the Magic of Yerba Mate - Itza's Educational Guide",
        'brewing_guide': "How to Brew Yerba Mate + FREE Gourd & Bombilla Offer!",
        'milestone': "Celebrating 100 Customers! Your Free Gift is Confirmed",
        'update': "IMPORTANT: Ordering Available Tomorrow - Itza Yerba Mate"
    }
    
    msg['Subject'] = subjects.get(template_type, "Message from Itza Yerba Mate")
    
    # Get template path based on type
    template_files = {
        'confirmation': 'confirmation_template.html',
        'educational': 'educational_template.html',
        'brewing_guide': 'brewing_guide_template.html',
        'milestone': 'milestone_template.html',
        'update': 'update_template.html'
    }
    
    template_file = template_files.get(template_type, 'confirmation_template.html')
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', template_file)
    
    # Read the HTML template
    if not os.path.exists(template_path):
        print(f"Warning: Email template not found at {template_path}")
        html_content = f"<p>Message from Itza Yerba Mate to {recipient_email}</p>"
    else:
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    
    # Replace placeholders
    html_content = html_content.replace('{{email}}', recipient_email)
    
    # Create HTML version
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Also attach a plain text version for email clients that don't support HTML
    plain_text = f"Message from Itza Yerba Mate.\nTo view this email correctly, please use an HTML-compatible email client."
    text_part = MIMEText(plain_text, 'plain')
    msg.attach(text_part)
    
    return msg

def get_html_content(msg):
    """Extract HTML content from a multipart message
    
    Args:
        msg: MIMEMultipart message object
        
    Returns:
        str: HTML content of the message
    """
    for part in msg.get_payload():
        if part.get_content_type() == 'text/html':
            return part.get_payload()
    
    # Fallback if no HTML part found
    return "<p>HTML content not available</p>"

def send_via_emailjs(recipient_email, subject=None, template_type=None, custom_template=None):
    """Send email using EmailJS service
    
    Args:
        recipient_email: Email address of the recipient
        subject: Optional subject for the email (for template replacement)
        template_type: Optional template type identifier (e.g., 'educational', 'brewing', etc.)
        custom_template: Optional HTML template content (not typically used with EmailJS)
    
    Returns:
        tuple: (success boolean, message string)
    """
    try:
        # Check if EmailJS configuration is available
        if not all([EMAIL_SERVICE_URL, EMAIL_SERVICE_USER_ID, EMAIL_SERVICE_TEMPLATE_ID]):
            print(f"EmailJS configuration incomplete for: {recipient_email}")
            return False, "EmailJS configuration incomplete"
        
        # Prepare API request
        headers = {'Content-Type': 'application/json'}
        if EMAIL_SERVICE_ACCESS_TOKEN:
            headers['Authorization'] = f'Bearer {EMAIL_SERVICE_ACCESS_TOKEN}'
        
        # Set up the template parameters
        template_params = {
            'to_email': recipient_email,
            'email': recipient_email  # For template replacement
        }
        
        # Add additional parameters if provided
        if subject:
            template_params['subject'] = subject
        if template_type:
            template_params['template_type'] = template_type
        
        payload = {
            'service_id': EMAIL_SERVICE_URL,
            'template_id': EMAIL_SERVICE_TEMPLATE_ID,
            'user_id': EMAIL_SERVICE_USER_ID,
            'template_params': template_params,
        }
        
        if EMAIL_SERVICE_ACCESS_TOKEN:
            payload['accessToken'] = EMAIL_SERVICE_ACCESS_TOKEN
        
        # Send the request to EmailJS API
        response = requests.post(
            'https://api.emailjs.com/api/v1.0/email/send',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            print(f"EmailJS: Email sent successfully to {recipient_email}")
            return True, "Email sent successfully via EmailJS"
        else:
            error = f"EmailJS API error ({response.status_code}): {response.text}"
            print(f"EmailJS error for {recipient_email}: {error}")
            return False, error
    
    except Exception as e:
        error_msg = f"EmailJS exception: {str(e)}"
        print(f"Error sending email to {recipient_email}: {error_msg}")
        return False, error_msg

def send_via_smtp(recipient_email, subject, html_content, text_content=None):
    """Send email using SMTP (Gmail)
    
    Args:
        recipient_email: Email address of the recipient
        subject: Subject line for the email
        html_content: HTML version of the email content
        text_content: Optional plain text version of the email
    
    Returns:
        tuple: (success boolean, message string)
    """
    if not SENDER_APP_PASSWORD:
        print(f"SMTP: App password not configured for: {recipient_email}")
        return False, "SMTP App Password not configured"
    
    try:
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        
        # Personalize the template
        personalized_html = html_content.replace('{{email}}', recipient_email)
        
        # Create plain text version if not provided
        if not text_content:
            text_content = "This email contains HTML content that your email client does not support."
        
        # Attach parts to the message
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(personalized_html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Login and send email
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        
        print(f"SMTP: Email sent successfully to {recipient_email}")
        return True, "Email sent successfully via SMTP"
    
    except Exception as e:
        error_msg = f"SMTP error: {str(e)}"
        print(f"SMTP error for {recipient_email}: {error_msg}")
        return False, error_msg

def queue_email(recipient_email, subject, html_content, email_type="confirmation"):
    """Save email to queue for later processing
    
    Args:
        recipient_email: Email address of the recipient
        subject: Subject line for the email
        html_content: HTML content of the email
        email_type: Type of email (e.g., 'confirmation', 'educational', 'order')
    
    Returns:
        tuple: (success boolean, filepath string)
    """
    ensure_directories()
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{email_type}_{timestamp}_{recipient_email.replace('@', '_at_')}.json"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), EMAIL_QUEUE_DIR, filename)
        
        # Prepare email data
        email_data = {
            'to': recipient_email,
            'subject': subject,
            'html': html_content.replace('{{email}}', recipient_email),
            'timestamp': timestamp,
            'type': email_type,
            'attempts': 0
        }
        
        # Save to queue file
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(email_data, file, indent=2)
        
        print(f"Email queued for {recipient_email} at {filepath}")
        return True, filepath
    
    except Exception as e:
        error_msg = log_error(e, "queue_email")
        return False, error_msg

def send_email(recipient_email, subject, template_path=None, html_content=None, template_type=None):
    """Send an email using all available methods in order of preference
    
    Args:
        recipient_email: Email address of the recipient
        subject: Subject line for the email
        template_path: Path to HTML template file (optional)
        html_content: Direct HTML content (optional, used if template_path is None)
        template_type: Type of template for EmailJS (optional)
    
    Returns:
        tuple: (success boolean, message string)
    """
    # Get the HTML content from template if provided
    if not html_content and template_path:
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            except Exception as e:
                log_error(e, f"reading template {template_path}")
                html_content = f"<p>Error loading template: {str(e)}</p>"
        else:
            html_content = f"<p>Template not found at {template_path}</p>"
    
    # If we still don't have HTML content, create a simple message
    if not html_content:
        html_content = f"<p>Message from Itza Yerba Mate to {recipient_email}</p>"
    
    # Try EmailJS first (primary method)
    success, message = send_via_emailjs(recipient_email, subject, template_type)
    
    # If EmailJS fails, try SMTP
    if not success:
        print(f"EmailJS failed: {message}. Trying SMTP...")
        success, message = send_via_smtp(recipient_email, subject, html_content)
    
    # If both fail, queue the email for later
    if not success:
        print(f"SMTP failed: {message}. Queuing email...")
        queue_success, queue_path = queue_email(recipient_email, subject, html_content)
        if queue_success:
            return False, f"Email queued at {queue_path}"
        else:
            return False, f"Failed to send and queue email: {queue_path}"
    
    return success, message

def process_email_queue():
    """Process all queued emails"""
    ensure_directories()
    
    queue_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), EMAIL_QUEUE_DIR)
    processed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), PROCESSED_DIR)
    failed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), FAILED_DIR)
    
    # Get all queued email files
    queued_files = [f for f in os.listdir(queue_dir) if f.endswith('.json')]
    
    if not queued_files:
        print("No emails in queue")
        return 0
    
    print(f"Found {len(queued_files)} emails in queue")
    
    processed_count = 0
    for filename in queued_files:
        filepath = os.path.join(queue_dir, filename)
        
        try:
            # Read email data
            with open(filepath, 'r', encoding='utf-8') as f:
                email_data = json.load(f)
            
            to_email = email_data.get('to')
            subject = email_data.get('subject', "Message from Itza Yerba Mate")
            html_content = email_data.get('html', '')
            
            print(f"Processing email to {to_email}")
            
            # Try EmailJS first
            success, message = send_via_emailjs(to_email, subject)
            
            # If EmailJS fails, try SMTP
            if not success:
                print(f"EmailJS failed: {message}. Trying SMTP...")
                success, message = send_via_smtp(to_email, subject, html_content)
            
            # Move file to appropriate directory
            if success:
                target_dir = processed_dir
                print(f"Successfully sent email to {to_email}")
                processed_count += 1
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
    
    return processed_count
