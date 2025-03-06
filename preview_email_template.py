import os
import webbrowser
import tempfile

def preview_email_template():
    """Generate a preview of the email template and open it in a browser"""
    try:
        # Get the absolute path to the email template
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, 'emails', 'confirmation_template.html')
        print(f"Looking for template at: {template_path}")
        
        # Check if the template file exists
        if not os.path.exists(template_path):
            print(f"❌ Template file not found at: {template_path}")
            # Check if the directory exists
            emails_dir = os.path.join(current_dir, 'emails')
            if os.path.exists(emails_dir):
                print(f"✅ Emails directory exists at: {emails_dir}")
                print(f"Files in directory: {os.listdir(emails_dir)}")
            else:
                print(f"❌ Emails directory does not exist at: {emails_dir}")
            return False
        
        print(f"✅ Template file found: {os.path.getsize(template_path)} bytes")
            
        # Read the template content
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
            print(f"✅ Read {len(html_content)} characters from template")
        
        # Replace placeholder with test email
        html_content = html_content.replace('{{email}}', 'oakley.alex178@gmail.com')
        
        # Create a temporary file to view the HTML
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        temp_file_path = temp_file.name
        temp_file.close()  # Close the file so we can write to it
        
        with open(temp_file_path, 'w', encoding='utf-8') as file:
            file.write(html_content)
            print(f"✅ Wrote {len(html_content)} characters to temporary file")
        
        # Open the temporary file in the default browser
        print(f"✅ Opening email template preview in browser: {temp_file_path}")
        webbrowser.open('file://' + temp_file_path)
        
        return True
    except Exception as e:
        import traceback
        print(f"❌ Error previewing email template: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=== Email Template Preview ===")
    result = preview_email_template()
    if result:
        print("\n✅ Successfully generated email template preview!")
    else:
        print("\n❌ Failed to generate email template preview. See errors above.")
