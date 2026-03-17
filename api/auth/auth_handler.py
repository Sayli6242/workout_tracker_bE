# from supabase import Client
# from fastapi import HTTPException
# from ..config.database import supabase

# def verify_supabase_token(token: str) -> dict:
#     try:
#         # Verify the JWT token using Supabase client
#         user = supabase.auth.get_user(token)
#         if not user or not user.user:
#             return None
            
#         # Extract relevant user data
#         user_data = {
#             "id": user.user.id,
#             "sub": user.user.id,  # Adding sub to match JWT standard
#             "email": user.user.email,
#             "role": "authenticated"
#         }
#         return user_data
#     except Exception as e:
#         print(f"Token verification error: {str(e)}")
#         return None

import json
import base64
import requests
from fastapi import HTTPException

def verify_pocketbase_token(token: str) -> dict:
    """PocketBase token verification - decode JWT and verify with PocketBase"""
    try:
        # Decode the JWT payload to get the user ID
        # PocketBase JWTs contain: id, type, collectionId, exp
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (add padding if needed)
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))

        user_id = decoded.get("id")
        if not user_id:
            return None

        # Verify the token is still valid by calling PocketBase auth-refresh
        response = requests.post(
            "http://127.0.0.1:8090/api/collections/users/auth-refresh",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user_data = response.json().get("record", {})
            return {
                "id": user_data.get("id", user_id),
                "email": user_data.get("email", ""),
                "role": "authenticated"
            }
        return None
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None

# Keep old name for compatibility
verify_supabase_token = verify_pocketbase_token
