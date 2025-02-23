from flask import Flask, request, jsonify, send_from_directory
import os
import csv
from datetime import datetime

app = Flask(__name__)

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
        with open('emails/waitlist.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        return jsonify({
            'status': 'success',
            'message': "You're on the waitlist! We'll notify you when we launch."
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to save email'}), 500

if __name__ == '__main__':
    app.run(debug=True)
