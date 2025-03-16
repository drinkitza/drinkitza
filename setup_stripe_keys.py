#!/usr/bin/env python
"""
Itza Yerba Mate - Stripe Keys Setup

This script sets up your Stripe API keys in a .env file.
"""

import os

def create_env_file():
    """Create a .env file with the Stripe API keys"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Prompt for Stripe API keys
    print("\nPlease enter your Stripe API keys:")
    publishable_key = input("Publishable Key (starts with pk_): ")
    secret_key = input("Secret Key (starts with sk_): ")
    webhook_secret = input("Webhook Secret (optional, starts with whsec_): ")
    
    # Validate inputs
    if not publishable_key.startswith(('pk_test_', 'pk_live_')):
        print("Warning: Publishable key should start with pk_test_ or pk_live_")
    
    if not secret_key.startswith(('sk_test_', 'sk_live_')):
        print("Warning: Secret key should start with sk_test_ or sk_live_")
    
    if webhook_secret and not webhook_secret.startswith('whsec_'):
        print("Warning: Webhook secret should start with whsec_")
    
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
        
        # Write updated content back to .env file
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
    
    print(f"\n✅ Stripe API keys have been saved to {env_path}")
    print("\nIMPORTANT: Make sure to add .env to your .gitignore file to keep your keys secure!")
    print("Never commit your API keys to version control.")
    return True

if __name__ == "__main__":
    try:
        create_env_file()
        print("\nSetup complete! Your Stripe API keys are now configured.")
        print("You can now run your Flask application with 'python app.py'")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Setup failed. Please try again.")
