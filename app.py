from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import os
from pymongo import MongoClient
from bson.json_util import dumps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# MongoDB Atlas connection
try:
    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        logger.error("MONGODB_URI environment variable is not set!")
        raise ValueError("MONGODB_URI environment variable is not set!")
        
    logger.info("Attempting to connect to MongoDB...")
    client = MongoClient(MONGODB_URI)
    
    # Verify connection
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB!")
    
    # Get or create database and collection
    db = client['drinkitza']  # Changed database name to match project
    waitlist = db['waitlist']
    
    # Create an index on email field to ensure uniqueness
    waitlist.create_index('email', unique=True)
    
    logger.info("Database and collection setup complete!")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

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
        logger.info(f"Received submission request with data: {data}")
        
        if not data or 'email' not in data:
            logger.warning("No email provided in request")
            return jsonify({'error': 'Email is required'}), 400

        email = data['email'].strip().lower()
        if not email:
            logger.warning("Empty email provided")
            return jsonify({'error': 'Email cannot be empty'}), 400

        # Add new email to MongoDB
        try:
            result = waitlist.insert_one({
                'email': email,
                'timestamp': datetime.utcnow(),
                'status': 'active',
                'source': 'website'
            })
            
            if result.inserted_id:
                logger.info(f"Successfully added email to database: {email}")
                return jsonify({
                    'status': 'success',
                    'message': "You're on the waitlist! We'll notify you when we launch."
                })
            else:
                logger.error("Failed to insert email - no inserted_id returned")
                return jsonify({'error': 'Failed to save email'}), 500
                
        except Exception as db_error:
            if "duplicate key error" in str(db_error).lower():
                logger.info(f"Duplicate email attempted: {email}")
                return jsonify({'error': 'Email already registered'}), 400
            else:
                logger.error(f"Database error while saving email: {str(db_error)}")
                return jsonify({'error': 'Failed to save email'}), 500

    except Exception as e:
        logger.error(f"Unexpected error in submit_email: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/check-font')
def check_font():
    font_path = os.path.join(app.static_folder, 'fonts', 'SuperMario256.ttf')
    if os.path.exists(font_path):
        return f'Font file exists at {font_path}'
    return f'Font file not found at {font_path}'

if __name__ == '__main__':
    app.run(debug=True)
