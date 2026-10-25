
import os

#loading first to verify SECRET early
from dotenv import load_dotenv
load_dotenv()       

from pathlib import Path 
load_dotenv(Path(__file__).parent / "jwt.env")

from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Depends, HTTPException
from fastapi.security import  OAuth2PasswordBearer
from policy import has_permission



#USERS_FILE = Path(__file__).resolve().parent / "users.json"
ROLES = ("viewer", "reviewer", "custodian", "admin")   # "anonymous" is implicit

SECRET = os.environ.get("JWT_SECRET")
if not SECRET or len(SECRET) < 60:  
    raise RuntimeError("SECRET is missing or is too short. Please verify SECRET exists and is 60+ Char")




TOKEN_MINS = 15 #keep the user refreshing their access tokens 
ALGORITHM = "HS256" 


ph = PasswordHasher() 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str: 
    return ph.hash(password)        #hashes the password entered

def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)      #verifies the hashed password against stored hash 
    except (VerifyMismatchError, InvalidHashError): 
        return False

def create_access_token(user_id: str, role: str) -> str: 
    now = datetime.now(timezone.utc) # using utc idk what happens during daylight savings to tokens if they rely on timezones that change. 
    return jwt.encode( 
        {"sub": user_id, 
         "role": role, 
         "iat": now, 
         "exp": now + timedelta(minutes=TOKEN_MINS)},  #passed Subject (userid) their role and time of initialisation then passes an expiry time (now + the defined token length)
        SECRET, 
        algorithm=ALGORITHM,)  # then encodes using secret and the algorthim



#current user
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict: 
    try:
        return jwt.decode(token, 
                          SECRET, 
                          algorithms=[ALGORITHM], 
                          options={"require": ["exp", "sub", "role"]})
    except InvalidTokenError: 
        raise HTTPException(401, "invalid or expired token", headers ={"WWW-Authenticate": "Bearer"})


def require_role(*allowed: str):
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed:
            raise HTTPException(403, "Need Higher Clearance")
        return user
    return checker



def require_permission(permission: str): #Using this one for now since in my head it makes more sense to check for the permission to be in the dict
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if not has_permission(user, permission):
            raise HTTPException(403, "Need Higher Clearance")
        return user
    return checker