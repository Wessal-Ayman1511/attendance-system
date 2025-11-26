#!/usr/bin/env python3
"""
Firebase setup script for Smart Attendance System.
This script helps you set up Firebase configuration and test the connection.
"""

import os
import json
from firebase_config import initialize_firebase

def setup_firebase():
    """Setup Firebase configuration."""
    print("🔥 Firebase Setup for Smart Attendance System")
    print("=" * 50)
    
    # Check if service account key exists
    service_account_path = "serviceAccountKey.json"
    
    if not os.path.exists(service_account_path):
        print(f"❌ Service account key not found at: {service_account_path}")
        print("\n📋 To set up Firebase:")
        print("1. Go to Firebase Console: https://console.firebase.google.com/")
        print("2. Select your project or create a new one")
        print("3. Go to Project Settings > Service Accounts")
        print("4. Click 'Generate new private key'")
        print("5. Save the downloaded JSON file as 'serviceAccountKey.json' in this directory")
        print("6. Make sure to add the file to .gitignore to keep it secure!")
        print("\n📄 A template file 'serviceAccountKey_template.json' has been created for reference.")
        return False
    
    # Validate service account key
    try:
        with open(service_account_path, 'r') as f:
            key_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in key_data]
        
        if missing_fields:
            print(f"❌ Service account key is missing required fields: {missing_fields}")
            return False
        
        print(f"✅ Service account key found for project: {key_data['project_id']}")
        
    except json.JSONDecodeError:
        print("❌ Service account key is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error reading service account key: {e}")
        return False
    
    # Test Firebase connection
    print("\n🔗 Testing Firebase connection...")
    try:
        firebase_manager = initialize_firebase(service_account_path)
        print("✅ Firebase connection successful!")
        
        # Test basic operations
        print("\n🧪 Testing basic operations...")
        
        # Test saving a sample attendance record
        test_success = firebase_manager.save_attendance_record(
            class_id="test_class",
            student_id="test_student",
            status="present",
            additional_data={"test": True}
        )
        
        if test_success:
            print("✅ Test attendance record saved successfully")
        else:
            print("❌ Failed to save test attendance record")
        
        # Test getting attendance records
        records = firebase_manager.get_attendance_for_class("test_class")
        print(f"✅ Retrieved {len(records)} attendance records")
        
        print("\n🎉 Firebase setup completed successfully!")
        print("\n📚 Next steps:")
        print("1. Run 'python app_firebase.py' to start the server with Firebase integration")
        print("2. Use the new endpoints like /start_session, /stop_session, /attendance/<class_id>")
        print("3. Check your Firebase Console to see the data being stored")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify the service account key is correct")
        print("3. Make sure your Firebase project has Firestore enabled")
        print("4. Check that the service account has the necessary permissions")
        return False

def create_gitignore():
    """Create .gitignore file to protect sensitive files."""
    gitignore_content = """# Firebase service account key (keep this secure!)
serviceAccountKey.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.temp
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ Created .gitignore file to protect sensitive data")

if __name__ == "__main__":
    print("🚀 Starting Firebase setup...")
    
    # Create .gitignore
    create_gitignore()
    
    # Setup Firebase
    success = setup_firebase()
    
    if success:
        print("\n🎯 Setup completed! You can now run the Firebase-integrated version.")
    else:
        print("\n❌ Setup failed. Please fix the issues above and try again.")
