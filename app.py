from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import os
from pymongo import MongoClient
from bson.json_util import dumps

app = Flask(__name__)

# MongoDB Atlas connection string (you'll need to set this as an environment variable in Vercel)
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://your-connection-string')
client = MongoClient(MONGODB_URI)
db = client.itza_db
waitlist = db.waitlist

# Ensure the static directory exists
os.makedirs('static', exist_ok=True)

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
        if waitlist.find_one({'email': email}):
            return jsonify({'error': 'Email already registered'}), 400

        # Add new email to MongoDB
        result = waitlist.insert_one({
            'email': email,
            'timestamp': datetime.utcnow(),
            'status': 'active'
        })

        if result.inserted_id:
            return jsonify({
                'status': 'success',
                'message': "You're on the waitlist! We'll notify you when we launch."
            })
        else:
            return jsonify({'error': 'Failed to save email'}), 500

    except Exception as e:
        print(f"Error saving email: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/check-font')
def check_font():
    font_path = os.path.join(app.static_folder, 'fonts', 'SuperMario256.ttf')
    if os.path.exists(font_path):
        return f'Font file exists at {font_path}'
    return f'Font file not found at {font_path}'

if __name__ == '__main__':
    app.run(debug=True)
