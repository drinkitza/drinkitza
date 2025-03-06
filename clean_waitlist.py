import os
import json
import glob
import re

def clean_waitlist_csv(email_to_remove):
    """Remove an email from the waitlist CSV file"""
    waitlist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'waitlist.csv')
    
    if not os.path.exists(waitlist_path):
        print(f"Waitlist file not found at {waitlist_path}")
        return False
    
    # Read the current waitlist
    lines = []
    removed = False
    
    try:
        with open(waitlist_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) >= 1:
                        email = parts[0].lower()
                        if email != email_to_remove.lower():
                            lines.append(line.strip())
                        else:
                            removed = True
                            print(f"Found and removed {email_to_remove} from waitlist.csv")
                else:
                    lines.append(line.strip())  # Keep empty lines
    except Exception as e:
        print(f"Error reading waitlist: {str(e)}")
        return False
    
    # Write the updated waitlist
    try:
        with open(waitlist_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(f"{line}\n")
        
        if removed:
            print(f"Successfully removed {email_to_remove} from waitlist.csv")
        else:
            print(f"Email {email_to_remove} not found in waitlist.csv")
        
        return removed
    except Exception as e:
        print(f"Error writing updated waitlist: {str(e)}")
        return False

def clean_queue_directory(email_to_remove):
    """Remove any queued emails for the specified address"""
    queue_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails', 'queue')
    
    if not os.path.exists(queue_dir):
        print(f"Queue directory not found at {queue_dir}")
        return False
    
    removed = False
    
    # Check all JSON files in the queue directory
    for json_file in glob.glob(os.path.join(queue_dir, '*.json')):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'to' in data and data['to'].lower() == email_to_remove.lower():
                os.remove(json_file)
                print(f"Removed queued email file: {json_file}")
                removed = True
        except Exception as e:
            print(f"Error processing queue file {json_file}: {str(e)}")
    
    if not removed:
        print(f"No queued emails found for {email_to_remove}")
    
    return removed

def clean_cache_files(email_to_remove):
    """Check for any cache files that might contain the email"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_patterns = ['*.cache', '*.tmp', '*.db', '*.sqlite']
    
    removed = False
    
    for pattern in cache_patterns:
        for cache_file in glob.glob(os.path.join(base_dir, '**', pattern), recursive=True):
            try:
                with open(cache_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if email_to_remove.lower() in content.lower():
                    print(f"Found email in cache file: {cache_file}")
                    # For cache files, we don't delete them but report their presence
                    removed = True
            except Exception as e:
                # Silently ignore errors reading cache files
                pass
    
    if not removed:
        print(f"No cache files found containing {email_to_remove}")
    
    return removed

def clean_all_text_files(email_to_remove):
    """Check all text files for the email and remove it"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    text_patterns = ['*.txt', '*.md', '*.csv', '*.json', '*.js', '*.py', '*.html']
    
    removed = False
    
    for pattern in text_patterns:
        for text_file in glob.glob(os.path.join(base_dir, '**', pattern), recursive=True):
            # Skip the waitlist.csv as it's handled separately
            if 'waitlist.csv' in text_file:
                continue
                
            try:
                with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Only modify files that contain the email
                if email_to_remove.lower() in content.lower():
                    # Use regex to replace the email while preserving line structure
                    new_content = re.sub(
                        r'(?i)' + re.escape(email_to_remove), 
                        'removed@example.com', 
                        content
                    )
                    
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"Removed email from file: {text_file}")
                    removed = True
            except Exception as e:
                print(f"Error processing file {text_file}: {str(e)}")
    
    if not removed:
        print(f"No other text files found containing {email_to_remove}")
    
    return removed

if __name__ == "__main__":
    email_to_remove = "removed@example.com"
    print(f"Cleaning all instances of {email_to_remove} from the system...")
    
    csv_cleaned = clean_waitlist_csv(email_to_remove)
    queue_cleaned = clean_queue_directory(email_to_remove)
    cache_checked = clean_cache_files(email_to_remove)
    text_cleaned = clean_all_text_files(email_to_remove)
    
    if csv_cleaned or queue_cleaned or cache_checked or text_cleaned:
        print(f"Successfully removed {email_to_remove} from the system")
    else:
        print(f"Could not find {email_to_remove} anywhere in the system")
