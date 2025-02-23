# Version 2.2 - Auto-sync with local CSV
from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import requests
import subprocess

app = Flask(__name__)

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'drinkitza'
REPO_NAME = 'drinkitza'
FILE_PATH = 'emails/waitlist.csv'

def sync_local_csv():
    try:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Run git pull
        subprocess.run(['git', 'pull'], cwd=current_dir, check=True)
        return True
    except Exception as e:
        print(f"Error syncing local CSV: {e}")
        return False

def save_to_github(email):
    # Get current file content
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        # Get current file
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        current_file = response.json()
        
        # Add new email
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_content = f'{email},{timestamp}\n'
        
        if 'content' in current_file:
            import base64
            content = base64.b64decode(current_file['content']).decode('utf-8')
            new_content = content + new_content
        
        # Update file
        data = {
            'message': f'Add email: {email}',
            'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            'sha': current_file.get('sha') if 'sha' in current_file else None
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Sync local CSV after successful GitHub update
        sync_local_csv()
        return True
        
    except Exception as e:
        print(f"GitHub Error: {e}")
        return False

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
        
        if save_to_github(email):
            return jsonify({
                'status': 'success',
                'message': "You're on the waitlist! We'll notify you when we launch."
            })
        else:
            return jsonify({'error': 'Failed to save email'}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to save email'}), 500

if __name__ == '__main__':
    app.run(debug=True)
