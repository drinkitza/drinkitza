from flask import Flask, request, jsonify, send_from_directory
import csv
from datetime import datetime
import os
import json

app = Flask(__name__)

# Serve static files from root directory
@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/api/waitlist', methods=['POST'])
def submit_email():
    try:
        data = request.json
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400

        email = data['email'].strip().lower()
        if not email:
            return jsonify({'error': 'Email cannot be empty'}), 400

        # Create /tmp directory if it doesn't exist (Vercel uses /tmp for writable storage)
        tmp_dir = '/tmp'
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        csv_file = os.path.join(tmp_dir, 'waitlist.csv')
        
        # Check if email already exists
        if os.path.exists(csv_file):
            with open(csv_file, 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                existing_emails = [row[0].lower() for row in reader]
                if email in existing_emails:
                    return jsonify({'error': 'Email already registered'}), 400

        # Append to CSV file
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Email', 'Timestamp'])
            writer.writerow([email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

        # Also save to a backup JSON file
        json_file = os.path.join(tmp_dir, 'waitlist.json')
        emails = []
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                try:
                    emails = json.load(f)
                except:
                    emails = []
        
        emails.append({
            'email': email,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        with open(json_file, 'w') as f:
            json.dump(emails, f, indent=2)

        return jsonify({
            'status': 'success',
            'message': "You're on the waitlist! We'll notify you when we launch."
        })

    except Exception as e:
        print(f"Error handling email submission: {e}")
        return jsonify({
            'error': 'Server error. Please try again later.'
        }), 500

@app.route('/check-font')
def check_font():
    font_path = os.path.join(app.static_folder, 'fonts', 'SuperMario256.ttf')
    if os.path.exists(font_path):
        return f'Font file exists at {font_path}'
    return f'Font file not found at {font_path}'

if __name__ == '__main__':
    app.run(debug=True)
