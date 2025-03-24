import os
import dotenv
import klaviyo_utils

# Load environment variables
dotenv.load_dotenv()

print(f"Klaviyo API Key configured: {'Yes' if klaviyo_utils.KLAVIYO_API_KEY else 'No'}")
print(f"Klaviyo List ID configured: {'Yes' if klaviyo_utils.KLAVIYO_LIST_ID else 'No'}")
print(f"Next Drop List ID configured: {'Yes' if klaviyo_utils.KLAVIYO_NEXT_DROP_LIST_ID else 'No'}")
print(f"Email queue directory: {klaviyo_utils.EMAIL_QUEUE_DIR}")

def test_klaviyo_api_connection():
    """Test if the Klaviyo API connection is working"""
    print("\nTesting Klaviyo API connection...")
    
    # If no API key is configured, skip the test
    if not klaviyo_utils.KLAVIYO_API_KEY:
        return False, "Klaviyo API key not configured"
    
    try:
        # Try to make a simple API call that won't actually affect anything
        # We'll just do a simple test with a dummy email address that won't be saved
        test_email = "test_" + str(os.getpid()) + "@example.com"
        
        # Attempt to check if we can interact with the API (without actually subscribing)
        import requests
        url = "https://a.klaviyo.com/api/v2/ping"
        headers = {
            "Content-Type": "application/json",
            "Api-Key": klaviyo_utils.KLAVIYO_API_KEY
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return True, "Klaviyo API connection successful"
        else:
            return False, f"Klaviyo API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Klaviyo API connection error: {str(e)}"

def send_test_email(recipient_email, next_drop=False):
    """Send a test email using Klaviyo"""
    print(f"\nSending test email to {recipient_email}...")
    
    # Set up template variables for our test
    template_variables = {
        "email": recipient_email,
        "subject": "Test Email from Itza Yerba Mate",
        "first_name": recipient_email.split('@')[0],
        "message": "This is a test email to verify the Klaviyo integration is working correctly."
    }
    
    # Get a test template ID - use the waitlist template as it should always exist
    template_id = os.getenv('KLAVIYO_WAITLIST_TEMPLATE_ID', '')
    
    if not template_id:
        # If no template ID is configured, try to use a default one
        print("No template ID configured, attempting to send a generic email")
        
        # Send a transactional email without a specific template
        success, message = klaviyo_utils.send_transactional_email(
            recipient_email,
            template_id="",  # Empty template ID will try to use a default template
            template_variables=template_variables
        )
    else:
        # Send using the configured template
        success, message = klaviyo_utils.send_transactional_email(
            recipient_email,
            template_id,
            template_variables
        )
    
    # If sending fails, queue it for later
    if not success:
        queue_success, queue_path = klaviyo_utils.queue_email(
            recipient_email,
            template_id,
            template_variables,
            "test_email"
        )
        
        if queue_success:
            return False, f"Email queued for later processing: {queue_path}"
        else:
            return False, f"Failed to send and queue email: {queue_path}"
    
    return success, message

def test_add_to_waitlist(recipient_email, next_drop=False):
    """Test adding a subscriber to the Klaviyo list"""
    print(f"\nTesting adding {recipient_email} to the Klaviyo {'next drop' if next_drop else 'main'} waitlist...")
    
    # Test profile properties
    profile_properties = {
        "Source": "Test Script",
        "Test_Timestamp": klaviyo_utils.datetime.now().isoformat()
    }
    
    # Add to the appropriate list
    success, message = klaviyo_utils.add_subscriber_to_klaviyo(
        recipient_email,
        profile_properties=profile_properties,
        next_drop=next_drop
    )
    
    return success, message

if __name__ == "__main__":
    # Ensure required directories exist
    klaviyo_utils.ensure_directories()
    
    # First test Klaviyo API connection
    api_success, api_message = test_klaviyo_api_connection()
    print(f"Klaviyo API Connection Test: {api_message}")
    
    if api_success:
        # Ask for recipient email
        recipient = input("\nEnter recipient email to send test email to: ")
        if recipient and '@' in recipient:
            # Ask if this is for the next drop waitlist
            next_drop_input = input("Is this for the next drop waitlist? (y/n): ").lower()
            next_drop = next_drop_input in ('y', 'yes')
            
            # Test adding to waitlist
            list_success, list_message = test_add_to_waitlist(recipient, next_drop)
            print(f"Add to Waitlist Test: {list_message}")
            
            # Test sending email
            send_success, send_message = send_test_email(recipient, next_drop)
            print(f"Email Test: {send_message}")
            
            if not send_success and "queued" in send_message.lower():
                print("Email was queued. You can check the queue directory or run process_email_queue.py to process it.")
        else:
            print("Invalid email address. Test skipped.")
    else:
        print("\nSkipping email test due to Klaviyo API connection failure.")
        print("Please check your Klaviyo API configuration in the .env file.")
        print("Required environment variables:")
        print("- KLAVIYO_API_KEY: Your Klaviyo private API key")
        print("- KLAVIYO_LIST_ID: The ID of your main waitlist list")
        print("- KLAVIYO_NEXT_DROP_LIST_ID: The ID of your next drop waitlist list")
        print("- KLAVIYO_WAITLIST_TEMPLATE_ID: Template ID for waitlist confirmation emails")
