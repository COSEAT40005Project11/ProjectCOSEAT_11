from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from API.auth import hash_password, verify_password, create_access_token
from API.user_repo import UserRepo, get_user_repo

router = APIRouter(prefix="/auth", tags=["auth"])

# used when the email doesn't exist, so the response takes the same time either way to mitigate certain attacks (i.e forcing and finding out which checks take more time)
DUMMY_HASH = hash_password("not-a-real-password")


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(),
          repo: UserRepo = Depends(get_user_repo)):
    user = repo.get_by_email(form.username.strip().lower())

    password_ok = verify_password(form.password,
                                  user.password_hash if user else DUMMY_HASH)

    if not user or not password_ok or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
        "name": user.name,     # for display in the UI only
        "role": user.role,     # for showing/hiding UI only; the server re-checks from the token
    }