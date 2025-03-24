import os
import csv
import json
import time
import requests
import traceback
from datetime import datetime
import dotenv
# Import the centralized email utilities
import klaviyo_utils

# Load environment variables
dotenv.load_dotenv()

def read_waitlist():
    """Read emails from the waitlist.csv file"""
    waitlist_path = os.path.join('emails', 'waitlist.csv')
    
    if not os.path.exists(waitlist_path):
        print(f"Waitlist file not found: {waitlist_path}")
        return []
    
    try:
        emails = []
        with open(waitlist_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                emails.append(row['email'])
        
        print(f"Read {len(emails)} emails from waitlist")
        return emails
    except Exception as e:
        print(f"Error reading waitlist: {str(e)}")
        return []

def read_email_template():
    """Read the HTML email template file"""
    template_path = os.path.join('emails', 'order_now_template.html')
    
    if not os.path.exists(template_path):
        print(f"Email template not found: {template_path}")
        return None
    
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()
        return template
    except Exception as e:
        print(f"Error reading email template: {str(e)}")
        return None

def send_announcement_emails(test_mode=False, specific_email=None, start_index=0, batch_size=None):
    """Send announcement emails to everyone on the waitlist"""
    print("\n--- Itza Yerba Mate - Order Announcement Emails ---")
    
    # Get the Klaviyo order template ID
    template_id = os.getenv('KLAVIYO_ORDER_TEMPLATE_ID', '')
    if not template_id:
        print("Warning: KLAVIYO_ORDER_TEMPLATE_ID not configured. Will attempt to send anyway.")
    
    # Determine recipients
    if specific_email:
        # Send to a specific email address only
        emails = [specific_email]
        print(f"Sending order announcement to specific email: {specific_email}")
    else:
        # Get all emails from the waitlist
        emails = read_waitlist()
        if not emails:
            print("No emails found in waitlist. Exiting.")
            return
        
        # Apply batch limits if specified
        if batch_size is not None:
            end_index = min(start_index + batch_size, len(emails))
            batch_emails = emails[start_index:end_index]
            print(f"Processing batch from index {start_index} to {end_index-1} ({len(batch_emails)} emails)")
            emails = batch_emails
    
    # Check if we're in test mode
    if test_mode:
        print("TEST MODE: No emails will be sent. Email addresses:")
        for i, email in enumerate(emails):
            print(f"  {i+1}. {email}")
        return
    
    # Send emails to each recipient
    success_count = 0
    failure_count = 0
    queue_count = 0
    
    for i, email in enumerate(emails):
        print(f"\nProcessing {i+1}/{len(emails)}: {email}")
        
        # Prepare template variables
        template_variables = {
            "email": email,
            "subject": "Itza Yerba Mate - Ordering is LIVE!",
            "first_name": email.split('@')[0],  # Basic personalization
            "order_url": "https://buy.stripe.com/8wM7tff4LfEg6EUbII"  # Update this with your actual order URL
        }
        
        # Use Klaviyo to send the email
        success, message = klaviyo_utils.send_order_announcement_email(email, template_id)
        
        if success:
            success_count += 1
            print(f"Successfully sent to {email}: {message}")
        elif "queued" in str(message).lower():
            queue_count += 1
            print(f"Queued email for {email}: {message}")
        else:
            failure_count += 1
            print(f"Failed to send to {email}: {message}")
        
        # Brief pause between sends to avoid rate limits
        if i < len(emails) - 1:
            time.sleep(1)
    
    # Print summary
    print("\n--- Email Sending Summary ---")
    print(f"Total emails: {len(emails)}")
    print(f"Successfully sent: {success_count}")
    print(f"Queued for later: {queue_count}")
    print(f"Failed: {failure_count}")

def main():
    """Main function to parse command-line arguments and send emails"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Send order announcement emails to waitlist subscribers')
    parser.add_argument('--test', action='store_true', help='Test mode - no emails sent')
    parser.add_argument('--email', type=str, help='Send to a specific email address')
    parser.add_argument('--start', type=int, default=0, help='Starting index for batch processing')
    parser.add_argument('--batch', type=int, help='Number of emails to process in this batch')
    parser.add_argument('--process-queue', action='store_true', help='Process the email queue after sending')
    
    args = parser.parse_args()
    
    # Ensure required directories exist
    klaviyo_utils.ensure_directories()
    
    # Send announcement emails
    send_announcement_emails(
        test_mode=args.test,
        specific_email=args.email,
        start_index=args.start,
        batch_size=args.batch
    )
    
    # Process the email queue if requested
    if args.process_queue:
        print("\n--- Processing Email Queue ---")
        processed = klaviyo_utils.process_email_queue()
        print(f"Processed {processed} emails from queue")

if __name__ == "__main__":
    main()
