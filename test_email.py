import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# Email configuration - using environment variables
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_APP_PASSWORD')

# Test email address - replace with your own for testing
TEST_EMAIL = "your-test-email@example.com"  # Replace with your email for testing

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

def test_email_template():
    """Test that the email template can be loaded correctly"""
    try:
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'confirmation_template.html')
        print(f"Looking for template at: {template_path}")
        
        if os.path.exists(template_path):
            print("✅ Template file exists")
            with open(template_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            if html_content and len(html_content) > 100:
                print(f"✅ Template loaded successfully ({len(html_content)} characters)")
                print(f"First 100 characters: {html_content[:100]}...")
                return True, html_content
            else:
                print("❌ Template file exists but content is empty or too short")
                return False, None
        else:
            print("❌ Template file does not exist")
            # Let's check if the directory exists
            emails_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails')
            if os.path.exists(emails_dir):
                print(f"✅ Emails directory exists at: {emails_dir}")
                print(f"Files in directory: {os.listdir(emails_dir)}")
            else:
                print(f"❌ Emails directory does not exist at: {emails_dir}")
            return False, None
    except Exception as e:
        log_error(e, "test_email_template")
        return False, None

# Only test the template loading, not the email sending
if __name__ == "__main__":
    print("=== Testing Email Template ===")
    success, content = test_email_template()
    if success:
        print("\nTemplate test passed! The email template is loading correctly.")
        print("\nTo test sending an actual email, you would need to:")
        print("1. Set the SENDER_EMAIL and SENDER_APP_PASSWORD environment variables")
        print("2. Update the TEST_EMAIL variable in this script with your email")
        print("3. Uncomment and run the test_send_email function")
    else:
        print("\nTemplate test failed. Please check the errors above.")
