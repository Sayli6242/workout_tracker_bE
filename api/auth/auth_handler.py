from supabase import Client
from fastapi import HTTPException
from ..config.database import supabase

def verify_supabase_token(token: str) -> dict:
    try:
        # Verify the JWT token using Supabase client
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            return None
            
        # Extract relevant user data
        user_data = {
            "id": user.user.id,
            "sub": user.user.id,  # Adding sub to match JWT standard
            "email": user.user.email,
            "role": "authenticated"
        }
        return user_data
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None