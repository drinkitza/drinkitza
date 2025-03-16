#!/usr/bin/env python
"""
Itza Yerba Mate - Stripe Setup Helper

This script helps you set up your Stripe API keys for your Itza Yerba Mate website.
It will guide you through the process of getting your keys from Stripe and setting them up in your application.
"""

import os
import sys
import webbrowser
import time

def print_header():
    """Print a nice header for the script"""
    print("\n" + "=" * 80)
    print("  ITZA YERBA MATE - STRIPE SETUP HELPER  ".center(80, "="))
    print("=" * 80 + "\n")

def print_section(title):
    """Print a section title"""
    print("\n" + "-" * 80)
    print(f"  {title}  ".center(80, "-"))
    print("-" * 80 + "\n")

def create_env_file(publishable_key, secret_key, webhook_secret):
    """Create a .env file with the Stripe API keys"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Check if .env file already exists
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Update existing keys
        lines = env_content.split('\n')
        updated_lines = []
        
        stripe_keys_updated = {
            'STRIPE_PUBLISHABLE_KEY': False,
            'STRIPE_SECRET_KEY': False,
            'STRIPE_WEBHOOK_SECRET': False
        }
        
        for line in lines:
            if line.startswith('STRIPE_PUBLISHABLE_KEY='):
                updated_lines.append(f'STRIPE_PUBLISHABLE_KEY={publishable_key}')
                stripe_keys_updated['STRIPE_PUBLISHABLE_KEY'] = True
            elif line.startswith('STRIPE_SECRET_KEY='):
                updated_lines.append(f'STRIPE_SECRET_KEY={secret_key}')
                stripe_keys_updated['STRIPE_SECRET_KEY'] = True
            elif line.startswith('STRIPE_WEBHOOK_SECRET='):
                updated_lines.append(f'STRIPE_WEBHOOK_SECRET={webhook_secret}')
                stripe_keys_updated['STRIPE_WEBHOOK_SECRET'] = True
            else:
                updated_lines.append(line)
        
        # Add any keys that weren't updated
        if not stripe_keys_updated['STRIPE_PUBLISHABLE_KEY']:
            updated_lines.append(f'STRIPE_PUBLISHABLE_KEY={publishable_key}')
        if not stripe_keys_updated['STRIPE_SECRET_KEY']:
            updated_lines.append(f'STRIPE_SECRET_KEY={secret_key}')
        if not stripe_keys_updated['STRIPE_WEBHOOK_SECRET']:
            updated_lines.append(f'STRIPE_WEBHOOK_SECRET={webhook_secret}')
        
        # Write updated content back to .env
        with open(env_path, 'w') as f:
            f.write('\n'.join(updated_lines))
    else:
        # Create new .env file
        with open(env_path, 'w') as f:
            f.write(f"""# Stripe API Keys
STRIPE_PUBLISHABLE_KEY={publishable_key}
STRIPE_SECRET_KEY={secret_key}
STRIPE_WEBHOOK_SECRET={webhook_secret}

# Email configuration
EMAIL_SERVICE_URL=your_emailjs_service_id
EMAIL_SERVICE_USER_ID=your_emailjs_user_id
EMAIL_SERVICE_TEMPLATE_ID=your_emailjs_template_id
EMAIL_SERVICE_ACCESS_TOKEN=your_emailjs_access_token

# SMTP fallback (optional)
SENDER_EMAIL=drinkitza@gmail.com
SENDER_APP_PASSWORD=

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=billions
""")
    
    print(f"✅ Stripe API keys have been saved to {env_path}")

def main():
    """Main function to guide the user through the Stripe setup process"""
    print_header()
    
    print("This script will help you set up your Stripe API keys for your Itza Yerba Mate website.")
    print("You'll need to create a Stripe account if you don't have one already.")
    
    # Step 1: Create Stripe account
    print_section("Step 1: Create a Stripe Account")
    print("If you don't have a Stripe account, you'll need to create one.")
    print("Opening Stripe website in your browser...")
    
    input("Press Enter to open the Stripe website...")
    webbrowser.open("https://dashboard.stripe.com/register")
    
    input("\nOnce you've created your account and logged in, press Enter to continue...")
    
    # Step 2: Get API keys
    print_section("Step 2: Get Your API Keys")
    print("Now you'll need to get your API keys from the Stripe Dashboard.")
    print("1. In the Stripe Dashboard, click on 'Developers' in the left sidebar")
    print("2. Click on 'API keys'")
    print("3. You'll see your Publishable key and Secret key")
    
    input("Press Enter to open the Stripe API keys page...")
    webbrowser.open("https://dashboard.stripe.com/apikeys")
    
    print("\nNote: You're currently in TEST mode by default. This is perfect for development.")
    print("When you're ready to accept real payments, you'll need to activate your account")
    print("and switch to LIVE mode.")
    
    # Get API keys from user
    publishable_key = input("\nEnter your Publishable key (starts with 'pk_test_'): ")
    while not publishable_key.startswith('pk_test_') and not publishable_key.startswith('pk_live_'):
        print("Invalid Publishable key. It should start with 'pk_test_' or 'pk_live_'")
        publishable_key = input("Enter your Publishable key: ")
    
    secret_key = input("\nEnter your Secret key (starts with 'sk_test_'): ")
    while not secret_key.startswith('sk_test_') and not secret_key.startswith('sk_live_'):
        print("Invalid Secret key. It should start with 'sk_test_' or 'sk_live_'")
        secret_key = input("Enter your Secret key: ")
    
    # Step 3: Set up webhooks
    print_section("Step 3: Set Up Webhooks")
    print("Webhooks allow Stripe to notify your application when events happen in your account.")
    print("For example, when a payment is successful or when a subscription is canceled.")
    
    print("\nTo set up webhooks:")
    print("1. In the Stripe Dashboard, go to Developers > Webhooks")
    print("2. Click 'Add endpoint'")
    print("3. For the endpoint URL, enter: http://your-website-url.com/webhook")
    print("   (Replace with your actual website URL when deployed)")
    print("4. For local testing, you can use Stripe CLI or a service like ngrok")
    print("5. Select events to listen for (at minimum: payment_intent.succeeded, payment_intent.payment_failed)")
    
    input("Press Enter to open the Stripe Webhooks page...")
    webbrowser.open("https://dashboard.stripe.com/webhooks")
    
    webhook_setup = input("\nDid you set up a webhook endpoint? (yes/no): ").lower()
    
    webhook_secret = ""
    if webhook_setup in ['yes', 'y']:
        print("\nAfter setting up your webhook, Stripe provides a signing secret.")
        print("This is used to verify that webhook events are coming from Stripe.")
        webhook_secret = input("Enter your Webhook Signing Secret (starts with 'whsec_'): ")
        while webhook_secret and not webhook_secret.startswith('whsec_'):
            print("Invalid Webhook Signing Secret. It should start with 'whsec_'")
            webhook_secret = input("Enter your Webhook Signing Secret (or leave empty for now): ")
    else:
        print("\nThat's okay! You can set up webhooks later when you're ready to deploy.")
        print("For now, we'll continue without webhook configuration.")
    
    # Step 4: Save API keys to .env file
    print_section("Step 4: Save Your API Keys")
    create_env_file(publishable_key, secret_key, webhook_secret)
    
    # Final instructions
    print_section("Setup Complete!")
    print("Your Stripe API keys have been saved to the .env file.")
    print("\nNext steps:")
    print("1. Make sure you have the python-dotenv package installed:")
    print("   pip install python-dotenv")
    print("2. Run your Flask application:")
    print("   python app.py")
    print("3. Test a payment using Stripe's test cards:")
    print("   - US: 4242 4242 4242 4242")
    print("   - UK: 4000 0082 6000 0000")
    print("   - EU (3D Secure): 4000 0025 0000 3155")
    print("   (Use any future expiration date, any 3 digits for CVC, and any postal code)")
    
    print("\nFor more information on testing, visit:")
    print("https://stripe.com/docs/testing")
    
    print("\nHappy selling! 🧉")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup canceled. You can run this script again anytime.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nAn error occurred: {str(e)}")
        print("Please try again or set up your API keys manually in the .env file.")
        sys.exit(1)
