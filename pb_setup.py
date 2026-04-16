#!/usr/bin/env python3
"""
PocketBase Collection Setup Script - FIXED VERSION
"""

import requests
import argparse
import sys

PB_URL = "http://127.0.0.1:8090"

# Your collections (same as before)
COLLECTIONS = [
    {
        "name": "workout_templates",
        "type": "base",
        "schema": [
            {"name": "user_id",                "type": "text",   "required": True},
            {"name": "name",                   "type": "text",   "required": True},
            {"name": "workout_type",           "type": "text",   "required": False},
            {"name": "estimated_duration_min", "type": "number", "required": False},
            {"name": "difficulty",             "type": "text",   "required": False},
            {"name": "description",            "type": "text",   "required": False},
            {"name": "last_used_at",           "type": "text",   "required": False},
        ]
    },
    # ... (add all other collections from your original script)
]

def login_as_admin(email, password):
    """Login as admin and return token"""
    login_url = f"{PB_URL}/api/admins/auth-with-password"
    login_data = {
        "identity": email,
        "password": password
    }
    
    print(f"Logging in as admin at {login_url}...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        token = response.json().get("token")
        print("✅ Admin login successful")
        return token
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

def create_collection(token, collection):
    """Create a single collection"""
    url = f"{PB_URL}/api/collections"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Creating collection '{collection['name']}'...")
    response = requests.post(url, json=collection, headers=headers)
    
    if response.status_code in [200, 201]:
        print(f"✅ Created '{collection['name']}'")
        return True
    else:
        print(f"❌ Failed '{collection['name']}': {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PocketBase Collection Setup")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    args = parser.parse_args()
    
    # Login first
    token = login_as_admin(args.email, args.password)
    
    # Create all collections
    success_count = 0
    for collection in COLLECTIONS:
        if create_collection(token, collection):
            success_count += 1
    
    print(f"\n✅ Done! Created {success_count}/{len(COLLECTIONS)} collections.")
    print("Restart your FastAPI server to use the new endpoints.")