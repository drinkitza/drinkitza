import os
import dotenv
import email_utils

# Load environment variables
dotenv.load_dotenv()

print(f"Sender email: {email_utils.SENDER_EMAIL}")
print(f"Password loaded: {'Yes' if email_utils.SENDER_APP_PASSWORD else 'No'}")
print(f"EmailJS configured: {'Yes' if all([email_utils.EMAIL_SERVICE_URL, email_utils.EMAIL_SERVICE_USER_ID, email_utils.EMAIL_SERVICE_TEMPLATE_ID]) else 'No'}")

def test_smtp_connection():
    """Test if SMTP connection can be established"""
    print("\nTesting SMTP connection...")
    try:
        # Use a simplified version of the SMTP sending function
        success, message = email_utils.send_via_smtp(
            email_utils.SENDER_EMAIL,  # Send to self (for testing)
            "SMTP Connection Test",
            "<p>This is just a connection test</p>",
            "This is just a connection test"
        )
        return success, message
    except Exception as e:
        return False, f"SMTP error: {str(e)}"

def test_emailjs_connection():
    """Test if EmailJS connection can be established"""
    print("\nTesting EmailJS connection...")
    try:
        # Use the EmailJS function from email_utils
        success, message = email_utils.send_via_emailjs(
            email_utils.SENDER_EMAIL,  # Send to self (for testing)
            "EmailJS Connection Test"
        )
        return success, message
    except Exception as e:
        return False, f"EmailJS error: {str(e)}"

def send_test_email(recipient_email):
    """Send a test email using the centralized email utilities"""
    print(f"\nSending test email to {recipient_email}...")
    
    # Create HTML content for the test email
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; color: #2D5A27; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            h1 { color: #2D5A27; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Itza Yerba Mate</h1>
            <p>This is a test email to verify the email sending functionality is working.</p>
            <p>If you received this email, the system is working correctly!</p>
            <p>Email sent using the centralized email utilities module.</p>
        </div>
    </body>
    </html>
    """
    
    # Use the centralized send_email function that tries all methods
    success, message = email_utils.send_email(
        recipient_email,
        "Test Email from Itza Yerba Mate",
        html_content=html_content
    )
    
    return success, message

if __name__ == "__main__":
    # Ensure required directories exist
    email_utils.ensure_directories()
    
    # First test EmailJS connection
    emailjs_success, emailjs_message = test_emailjs_connection()
    print(f"EmailJS Connection Test: {emailjs_message}")
    
    # Then test SMTP connection
    smtp_success, smtp_message = test_smtp_connection()
    print(f"SMTP Connection Test: {smtp_message}")
    
    if emailjs_success or smtp_success:
        # Ask for recipient email
        recipient = input("\nEnter recipient email to send test email to: ")
        if recipient and '@' in recipient:
            send_success, send_message = send_test_email(recipient)
            print(f"Email Test: {send_message}")
            
            if not send_success and "queued" in send_message.lower():
                print("Email was queued. You can check the queue directory or run process_email_queue.py to process it.")
        else:
            print("Invalid email address. Test skipped.")
    else:
        print("\nSkipping email test due to all connection failures.")
        print("Please check your email configuration in the .env file.")
