from flask import Flask, request, jsonify, send_from_directory
import os
import csv
from datetime import datetime

app = Flask(__name__)

# Ensure the emails directory exists
os.makedirs('emails', exist_ok=True)
WAITLIST_FILE = 'emails/waitlist.csv'

# Create the CSV file if it doesn't exist
if not os.path.exists(WAITLIST_FILE):
    with open(WAITLIST_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Email', 'Timestamp'])

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/api/waitlist', methods=['POST'])
def submit_email():
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400

        email = data['email'].strip().lower()
        if not email:
            return jsonify({'error': 'Email cannot be empty'}), 400

        # Check if email already exists
        try:
            with open(WAITLIST_FILE, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                existing_emails = [row[0].lower() for row in reader]
                if email in existing_emails:
                    return jsonify({'error': 'Email already registered'}), 400
        except Exception as e:
            print(f"Error checking existing emails: {e}")

        # Add the new email
        try:
            with open(WAITLIST_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            
            print(f"Successfully added email: {email}")
            return jsonify({
                'status': 'success',
                'message': "You're on the waitlist! We'll notify you when we launch."
            })

        except Exception as e:
            print(f"Error writing to CSV: {e}")
            return jsonify({'error': 'Failed to save email'}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
