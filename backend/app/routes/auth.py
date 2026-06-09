from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import (
    COOKIE_NAME,
    PREDEFINED_AVATARS,
    SESSION_TOKEN_EXPIRE_DAYS,
    AuthError,
    authenticate_user,
    confirm_password_reset,
    create_session_token,
    register_user,
    request_password_reset,
    user_to_dict,
)

router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=255)
    avatar: str = Field(min_length=1, max_length=63)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user: dict
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=int(timedelta(days=SESSION_TOKEN_EXPIRE_DAYS).total_seconds()),
        samesite="lax",
        secure=False,
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, httponly=True, samesite="lax")


@router.get("/avatars")
def list_avatars():
    return {"avatars": list(PREDEFINED_AVATARS)}


@router.post("/register", status_code=201)
def register(
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            avatar=body.avatar,
        )
    except AuthError as exc:
        raise _http_error(exc)

    token = create_session_token(user.id)
    _set_auth_cookie(response, token)
    return {"user": user_to_dict(user)}


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in — copy access_token for Swagger Authorize",
)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(db, body.email, body.password)
    except AuthError as exc:
        raise _http_error(exc)

    token = create_session_token(user.id)
    _set_auth_cookie(response, token)
    return LoginResponse(user=user_to_dict(user), access_token=token)


@router.post("/logout")
def logout(response: Response):
    _clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.post("/password-reset/request")
def password_reset_request(body: PasswordResetRequest, db: Session = Depends(get_db)):
    try:
        request_password_reset(db, body.email)
    except AuthError as exc:
        raise _http_error(exc)

    return {
        "message": "If an account exists for that email, a password reset link has been sent"
    }


@router.post("/password-reset/confirm")
def password_reset_confirm(
    body: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
):
    try:
        confirm_password_reset(db, body.token, body.new_password)
    except AuthError as exc:
        raise _http_error(exc)

    return {"message": "Password has been reset successfully"}


def _http_error(exc: AuthError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)
