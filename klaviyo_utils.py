"""
Itza Yerba Mate - Klaviyo Integration Utilities
Centralized module for all Klaviyo-related functionality
"""
import os
import json
import time
import requests
import traceback
from datetime import datetime

# Klaviyo configuration
KLAVIYO_API_KEY = os.getenv('KLAVIYO_API_KEY', '')
KLAVIYO_LIST_ID = os.getenv('KLAVIYO_LIST_ID', '')  # For the main waitlist
KLAVIYO_NEXT_DROP_LIST_ID = os.getenv('KLAVIYO_NEXT_DROP_LIST_ID', '')  # For next drop waitlist

# Email queue directory (used as fallback if Klaviyo API is down)
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

def add_subscriber_to_klaviyo(email, list_id=None, profile_properties=None, next_drop=False):
    """Add a subscriber to a Klaviyo list
    
    Args:
        email: The email address to add
        list_id: Optional specific Klaviyo list ID (defaults to KLAVIYO_LIST_ID)
        profile_properties: Optional dictionary of profile properties to add
        next_drop: If True, add to the next drop list instead of the main list
        
    Returns:
        tuple: (success boolean, message string)
    """
    if not KLAVIYO_API_KEY:
        return False, "Klaviyo API key not configured"
    
    # Determine which list to use
    if not list_id:
        list_id = KLAVIYO_NEXT_DROP_LIST_ID if next_drop else KLAVIYO_LIST_ID
    
    if not list_id:
        return False, "Klaviyo list ID not configured"
    
    try:
        # Set up the API endpoint and headers
        url = f"https://a.klaviyo.com/api/v2/list/{list_id}/subscribe"
        headers = {
            "Content-Type": "application/json",
            "Api-Key": KLAVIYO_API_KEY
        }
        
        # Build the profile data
        profile = {
            "email": email,
            "$consent": ["email"]  # Explicit opt-in
        }
        
        # Add any additional profile properties
        if profile_properties and isinstance(profile_properties, dict):
            profile.update(profile_properties)
        
        # Build the request payload
        payload = {
            "profiles": [profile]
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"Successfully added {email} to Klaviyo list {list_id}")
            return True, "Subscriber added successfully"
        else:
            error_msg = f"Klaviyo API error: {response.status_code} - {response.text}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = log_error(e, "add_subscriber_to_klaviyo")
        return False, error_msg

def send_transactional_email(email, template_id, template_variables=None):
    """Send a transactional email using Klaviyo
    
    Args:
        email: Recipient email address
        template_id: Klaviyo email template ID
        template_variables: Optional dictionary of variables to use in the template
        
    Returns:
        tuple: (success boolean, message string)
    """
    if not KLAVIYO_API_KEY:
        return False, "Klaviyo API key not configured"
    
    try:
        # Set up the API endpoint and headers
        url = "https://a.klaviyo.com/api/v1/email"
        headers = {
            "Content-Type": "application/json",
            "Api-Key": KLAVIYO_API_KEY
        }
        
        # Build the payload
        payload = {
            "from_email": "hello@drinkitza.com",
            "from_name": "Itza Yerba Mate",
            "subject": "Message from Itza Yerba Mate",  # Default subject
            "to": [email],
            "template_id": template_id
        }
        
        # Add template variables if provided
        if template_variables and isinstance(template_variables, dict):
            payload["context"] = template_variables
            
            # Set subject from template variables if provided
            if "subject" in template_variables:
                payload["subject"] = template_variables["subject"]
        
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"Successfully sent email to {email} using Klaviyo template {template_id}")
            return True, "Email sent successfully"
        else:
            error_msg = f"Klaviyo API error: {response.status_code} - {response.text}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = log_error(e, "send_transactional_email")
        return False, error_msg

def queue_email(recipient_email, template_id, template_variables=None, email_type="confirmation"):
    """Save email to queue for later processing
    
    Args:
        recipient_email: Email address of the recipient
        template_id: Klaviyo template ID
        template_variables: Template variables to pass to Klaviyo
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
            'template_id': template_id,
            'template_variables': template_variables,
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

def send_waitlist_confirmation_email(email, next_drop=False):
    """Send confirmation email to new waitlist subscribers
    
    Args:
        email: The subscriber's email address
        next_drop: Whether this is for the next drop waitlist
        
    Returns:
        tuple: (success boolean, message string)
    """
    # Template IDs for different email types (these would be the actual IDs from your Klaviyo account)
    TEMPLATE_IDS = {
        'waitlist_confirmation': os.getenv('KLAVIYO_WAITLIST_TEMPLATE_ID', ''),
        'next_drop_confirmation': os.getenv('KLAVIYO_NEXT_DROP_TEMPLATE_ID', ''),
    }
    
    template_id = TEMPLATE_IDS['next_drop_confirmation'] if next_drop else TEMPLATE_IDS['waitlist_confirmation']
    
    if not template_id:
        return False, "Klaviyo template ID not configured"
    
    # First add the subscriber to the appropriate list
    list_success, list_message = add_subscriber_to_klaviyo(
        email, 
        next_drop=next_drop,
        profile_properties={
            "Source": "Website Waitlist",
            "Joined_Next_Drop_Waitlist": next_drop
        }
    )
    
    if not list_success:
        print(f"Warning: Failed to add {email} to Klaviyo list: {list_message}")
    
    # Set up template variables
    template_variables = {
        "email": email,
        "subject": "Thanks for Joining Itza Yerba Mate's Waitlist!",
        "first_name": email.split('@')[0]  # Basic personalization as fallback
    }
    
    # Send the email
    success, message = send_transactional_email(
        email,
        template_id,
        template_variables
    )
    
    # If sending fails, queue it for later
    if not success:
        queue_success, queue_path = queue_email(
            email,
            template_id,
            template_variables,
            "waitlist_confirmation" if not next_drop else "next_drop_confirmation"
        )
        
        if queue_success:
            return False, f"Email queued for later processing: {queue_path}"
        else:
            return False, f"Failed to send and queue email: {queue_path}"
    
    return success, message

def send_educational_email(email, template_id=None):
    """Send educational email about yerba mate
    
    Args:
        email: Recipient email address
        template_id: Optional specific template ID
        
    Returns:
        tuple: (success boolean, message string)
    """
    # Use the default educational template ID if none provided
    if not template_id:
        template_id = os.getenv('KLAVIYO_EDUCATIONAL_TEMPLATE_ID', '')
    
    if not template_id:
        return False, "Klaviyo educational template ID not configured"
    
    # Set up template variables
    template_variables = {
        "email": email,
        "subject": "Discover the Magic of Yerba Mate - Itza's Educational Guide",
        "first_name": email.split('@')[0]
    }
    
    # Send the email
    success, message = send_transactional_email(
        email,
        template_id,
        template_variables
    )
    
    # Queue for later if sending fails
    if not success:
        queue_success, queue_path = queue_email(
            email,
            template_id,
            template_variables,
            "educational"
        )
        
        if queue_success:
            return False, f"Email queued for later processing: {queue_path}"
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
            template_id = email_data.get('template_id')
            template_variables = email_data.get('template_variables', {})
            
            print(f"Processing email to {to_email}")
            
            # Attempt to send the email via Klaviyo
            success, message = send_transactional_email(
                to_email,
                template_id,
                template_variables
            )
            
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

# Additional helper functions for specific campaign types

def send_brewing_guide_email(email, template_id=None):
    """Send brewing guide email
    
    Args:
        email: Recipient email address
        template_id: Optional specific template ID
        
    Returns:
        tuple: (success boolean, message string)
    """
    # Use the default brewing guide template ID if none provided
    if not template_id:
        template_id = os.getenv('KLAVIYO_BREWING_GUIDE_TEMPLATE_ID', '')
    
    if not template_id:
        return False, "Klaviyo brewing guide template ID not configured"
    
    # Set up template variables
    template_variables = {
        "email": email,
        "subject": "How to Brew Yerba Mate + FREE Gourd & Bombilla Offer!",
        "first_name": email.split('@')[0]
    }
    
    # Send the email
    return send_transactional_email(
        email,
        template_id,
        template_variables
    )

def send_milestone_email(email, template_id=None):
    """Send milestone celebration email
    
    Args:
        email: Recipient email address
        template_id: Optional specific template ID
        
    Returns:
        tuple: (success boolean, message string)
    """
    # Use the default milestone template ID if none provided
    if not template_id:
        template_id = os.getenv('KLAVIYO_MILESTONE_TEMPLATE_ID', '')
    
    if not template_id:
        return False, "Klaviyo milestone template ID not configured"
    
    # Set up template variables
    template_variables = {
        "email": email,
        "subject": "Celebrating 100 Customers! Your Free Gift is Confirmed",
        "first_name": email.split('@')[0]
    }
    
    # Send the email
    return send_transactional_email(
        email,
        template_id,
        template_variables
    )

def send_update_email(email, template_id=None):
    """Send update email
    
    Args:
        email: Recipient email address
        template_id: Optional specific template ID
        
    Returns:
        tuple: (success boolean, message string)
    """
    # Use the default update template ID if none provided
    if not template_id:
        template_id = os.getenv('KLAVIYO_UPDATE_TEMPLATE_ID', '')
    
    if not template_id:
        return False, "Klaviyo update template ID not configured"
    
    # Set up template variables
    template_variables = {
        "email": email,
        "subject": "IMPORTANT: Ordering Available Tomorrow - Itza Yerba Mate",
        "first_name": email.split('@')[0]
    }
    
    # Send the email
    return send_transactional_email(
        email,
        template_id,
        template_variables
    )

def send_order_announcement_email(email, template_id=None):
    """Send order announcement email
    
    Args:
        email: Recipient email address
        template_id: Optional specific template ID
        
    Returns:
        tuple: (success boolean, message string)
    """
    # Use the default order template ID if none provided
    if not template_id:
        template_id = os.getenv('KLAVIYO_ORDER_TEMPLATE_ID', '')
    
    if not template_id:
        return False, "Klaviyo order template ID not configured"
    
    # Set up template variables
    template_variables = {
        "email": email,
        "subject": "Itza Yerba Mate - Ordering is LIVE!",
        "first_name": email.split('@')[0],
        "order_url": "https://buy.stripe.com/8wM7tff4LfEg6EUbII"  # Update this with your actual order URL
    }
    
    # Send the email
    return send_transactional_email(
        email,
        template_id,
        template_variables
    )
