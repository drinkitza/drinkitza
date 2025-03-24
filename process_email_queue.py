#!/usr/bin/env python3
"""
Process the email queue and send any pending emails via Klaviyo
"""
import os
import sys
import argparse
import klaviyo_utils

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
    """Ensure all required directories exist"""
    for directory in [os.path.join('emails', 'queue'), os.path.join('emails', 'processed'), os.path.join('emails', 'failed')]:
        os.makedirs(directory, exist_ok=True)

def process_queue(max_emails=None, delay_seconds=1, verbose=True):
    """Process emails in the queue using Klaviyo integration
    
    Args:
        max_emails: Maximum number of emails to process (None for all)
        delay_seconds: Delay between sending attempts
        verbose: Whether to print detailed logs
        
    Returns:
        tuple: (processed_count, success_count, failed_count)
    """
    # Simply delegate to the Klaviyo function
    if verbose:
        print("Processing email queue using Klaviyo integration...")
    
    # Ensure required directories exist
    ensure_directories()
    
    # Process the queue
    processed_count = klaviyo_utils.process_email_queue()
    
    if verbose:
        print(f"Queue processing complete. Processed {processed_count} emails.")
    
    return processed_count, processed_count, 0  # For backward compatibility

def process_legacy_queue():
    """For backward compatibility - process any emails in the old queue format"""
    # This function is mainly kept to ensure any emails in old queue format can be processed
    ensure_directories()
    
    # Find any legacy queue files that might not fit the new format
    legacy_count = 0
    for filename in os.listdir(os.path.join('emails', 'queue')):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(os.path.join('emails', 'queue'), filename)
        
        try:
            # Try to read the file as JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                email_data = json.load(f)
            
            # Check if it has the expected fields but might be in old format
            if 'to' in email_data and 'html' in email_data:
                to_email = email_data.get('to')
                subject = email_data.get('subject', "Message from Itza Yerba Mate")
                html_content = email_data.get('html', '')
                
                # Use Klaviyo integration to send
                success, message = klaviyo_utils.send_email(
                    to_email, 
                    subject, 
                    html_content=html_content
                )
                
                # Move the file
                if success:
                    target_dir = os.path.join('emails', 'processed')
                    legacy_count += 1
                else:
                    target_dir = os.path.join('emails', 'failed')
                
                target_path = os.path.join(target_dir, filename)
                os.rename(filepath, target_path)
                
        except Exception as e:
            print(f"Error processing legacy email {filename}: {str(e)}")
    
    return legacy_count

def main():
    """Main function"""
    import argparse
    import json
    import traceback
    
    parser = argparse.ArgumentParser(description='Process queued emails')
    parser.add_argument('--max', type=int, help='Maximum number of emails to process')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between sends (seconds)')
    parser.add_argument('--quiet', action='store_true', help='Suppress detailed logs')
    parser.add_argument('--legacy', action='store_true', help='Process legacy format emails only')
    
    args = parser.parse_args()
    
    if args.legacy:
        # Process only legacy format emails
        processed = process_legacy_queue()
        print(f"Processed {processed} legacy format emails")
    else:
        # Process all emails in queue
        processed, success, failed = process_queue(
            max_emails=args.max,
            delay_seconds=args.delay,
            verbose=not args.quiet
        )
        
        if not args.quiet:
            print(f"Queue processing complete: {processed} emails processed")
            print(f"Success: {success}, Failed: {failed}")

    print("Starting email queue processing...")
    processed_count = klaviyo_utils.process_email_queue()
    
    print(f"Processed {processed_count} emails from the queue")
    
    # Return a status code based on whether any emails were processed
    # This is useful for cron jobs or other scheduled tasks
    sys.exit(0 if processed_count > 0 else 1)

if __name__ == "__main__":
    main()
