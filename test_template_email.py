import os
import sys
import getpass
from app import send_confirmation_email

def main():
    # Get the test email address
    if len(sys.argv) > 1:
        test_email = sys.argv[1]
    else:
        test_email = input("Enter your email address for testing: ")
    
    # Get email credentials securely
    sender_email = input("Enter sender email address [drinkitza@gmail.com]: ") or "drinkitza@gmail.com"
    sender_password = getpass.getpass("Enter sender email app password: ")
    
    # Set environment variables
    os.environ['SENDER_EMAIL'] = sender_email
    os.environ['SENDER_APP_PASSWORD'] = sender_password
    
    print(f"\nSending test email to: {test_email}")
    print("Using the HTML template from emails/confirmation_template.html")
    
    # Send the test email
    result = send_confirmation_email(test_email)
    
    if result:
        print("\n✅ Email sent successfully!")
        print("Check your inbox to see if the HTML template is displayed correctly.")
    else:
        print("\n❌ Failed to send email. Check the logs for details.")

if __name__ == "__main__":
    main()
