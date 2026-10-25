#THIS IS TO TEST, PLEASE REMOVE FILE ONCE DB HAS BEEN CREATED


import os
import uuid
from dataclasses import dataclass
from typing import Protocol



@dataclass
class UserRecord:
    id: str
    name: str 
    email: str
    password_hash: str
    role: str
    is_active: bool



#- Unique user identifier
#- Name or display name
#- User role
#- Access level or permissions
#- Account status
#- Creation and update information

#role and premissions should be handled by policies (ill let you know if this needs to channge after testing )