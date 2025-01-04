from supabase import Client
from fastapi import HTTPException
from ..config.database import supabase

def verify_supabase_token(token: str) -> dict:
    try:
        # Verify the JWT token using Supabase client
        user = supabase.auth.get_user(token)
        return user.dict()
    except Exception as e:
        return None