import os
import sys
from app import send_confirmation_email

# Use the provided email address
test_email = "oakley.alex178@gmail.com"
    
print(f"Sending test email to: {test_email}")
result = send_confirmation_email(test_email)

if result:
    print("✅ Email sent successfully!")
else:
    print("❌ Failed to send email. Check the logs for details.")
