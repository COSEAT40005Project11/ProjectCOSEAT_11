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


class UserRepo(Protocol):
    """The contract. The DB dev implements these four methods against MySQL."""
    def get_by_email(self, email: str) -> UserRecord | None: ...
    def get_by_id(self, user_id: str) -> UserRecord | None: ...
    def create(self, name: str, email: str, password_hash: str, role: str = "viewer") -> UserRecord: ...
    def set_role(self, user_id: str, role: str) -> None: ...


class InMemoryUserRepo:
    def __init__(self):
        self._users: dict[str, UserRecord] = {}

    def get_by_email(self, email: str) -> UserRecord | None:
        email = email.strip().lower()
        return next((u for u in self._users.values() if u.email == email), None)

    def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._users.get(user_id)

    def create(self, name, email, password_hash, role="viewer") -> UserRecord:
        user = UserRecord(
            id=str(uuid.uuid4()),
            name=name,
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        self._users[user.id] = user
        return user

    def set_role(self, user_id: str, role: str) -> None:
        self._users[user_id].role = role


_repo = InMemoryUserRepo()      # the DB dev replaces this one line


def get_user_repo() -> UserRepo:
    return _repo


# dev-only test accounts, one per role 
# Only created when DEV_SEED_USERS=1 is set in  local jwt.env.
if os.environ.get("DEV_SEED_USERS") == "1":
    from API.auth import hash_password

    for _name, _email, _role in [
        ("Test Viewer",    "viewer@test.local",    "viewer"),
        ("Test Reviewer",  "reviewer@test.local",  "reviewer"),
        ("Test Custodian", "custodian@test.local", "custodian"),
        ("Test Admin",     "admin@test.local",     "admin"),
    ]:
        _repo.create(_name, _email, hash_password("password1234"), _role)
#Unique user identifier
# Name or display name
# User role
# Access level or permissions
# Account status
# Creation and update information

#role and premissions should be handled by policies (ill let you know if this needs to channge after testing )