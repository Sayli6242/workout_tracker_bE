from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth_handler import verify_supabase_token

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            
            decoded_token = self.verify_jwt(credentials.credentials)
            if not decoded_token:
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
                
            return decoded_token
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, token: str) -> dict:
        try:
            decoded_token = verify_supabase_token(token)
            if decoded_token is None:
                return None
            return decoded_token
        except Exception as e:
            print(f"An error occurred: {e}")
            return None