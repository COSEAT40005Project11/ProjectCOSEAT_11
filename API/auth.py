import getpass
import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
 
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel



USERS_FILE = Path(__file__).resolve().parent / "users.json"
ROLES = ("viewer", "reviewer", "custodian", "admin")   # "anonymous" is implicit
TOKEN_HOURS = 8

ALGORITHM = "HS256" #let me play with this more, just the first one i know of



bearer = HTTPBearer(auto_error=False)   # we handle "no token" ourselves


