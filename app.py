from flask import Flask, request, jsonify, send_from_directory
import csv
from datetime import datetime
import os

app = Flask(__name__)

# Serve static files from root directory
@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/submit-email', methods=['POST'])
def submit_email():
    try:
        email = request.json.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Create emails directory if it doesn't exist
        if not os.path.exists('emails'):
            os.makedirs('emails')

        # Save to CSV file with timestamp
        csv_file = 'emails/waitlist.csv'
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Email', 'Timestamp'])
            writer.writerow([email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

        return jsonify({'message': 'Success! You\'re on the waitlist'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-font')
def check_font():
    font_path = os.path.join(app.static_folder, 'fonts', 'SuperMario256.ttf')
    if os.path.exists(font_path):
        return f'Font file exists at {font_path}'
    return f'Font file not found at {font_path}'

if __name__ == '__main__':
    app.run(debug=True)
