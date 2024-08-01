import os
from datetime import datetime
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv('cfg/.env', raise_error_if_not_found=True))

# These should be kept secret and stored securely (e.g., in environment variables)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

def verify_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        exp: int = payload.get("exp")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role, exp=exp)
        return token_data
    except JWTError:
        raise credentials_exception

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
    
    token_data = verify_token(token)
    
    # Check if the token has expired
    if datetime.now().timestamp() > token_data.exp:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    return token_data
