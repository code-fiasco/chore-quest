import logging
import re
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.household import Household
from app.models.user import User, UserRole
from app.seed import ensure_default_categories
from app.services.email import EmailError, send_email

logger = logging.getLogger(__name__)

PREDEFINED_AVATARS = (
    "Tiger",
    "Kitten",
    "Fox",
    "Panda",
    "Rabbit",
    "Bear",
    "Wolf",
    "Owl",
)

MAX_HOUSEHOLD_MEMBERS = 2
SESSION_TOKEN_EXPIRE_DAYS = 7
RESET_TOKEN_EXPIRE_HOURS = 1
COOKIE_NAME = "access_token"

ALGORITHM = "HS256"
SESSION_TOKEN_TYPE = "session"
RESET_TOKEN_TYPE = "password_reset"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise AuthError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise AuthError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise AuthError("Password must contain at least one number")


def validate_avatar(avatar: str) -> None:
    if avatar not in PREDEFINED_AVATARS:
        raise AuthError(
            f"Avatar must be one of: {', '.join(PREDEFINED_AVATARS)}"
        )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_session_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=SESSION_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": SESSION_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_password_reset_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": RESET_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str) -> int:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        raise AuthError("Invalid or expired token", status_code=401)

    token_type = payload.get("type")
    if token_type != expected_type:
        raise AuthError("Invalid or expired token", status_code=401)

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthError("Invalid or expired token", status_code=401)

    return int(user_id)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.lower()))


def get_registration_status(db: Session) -> dict:
    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    return {
        "open": user_count < MAX_HOUSEHOLD_MEMBERS,
        "max_members": MAX_HOUSEHOLD_MEMBERS,
        "current_members": user_count,
    }


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    avatar: str,
) -> User:
    email = email.strip().lower()
    display_name = display_name.strip()

    if not email:
        raise AuthError("Email is required")
    if not display_name:
        raise AuthError("Display name is required")

    validate_password(password)
    validate_avatar(avatar)

    if get_user_by_email(db, email):
        raise AuthError("An account with this email already exists", status_code=409)

    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    if user_count >= MAX_HOUSEHOLD_MEMBERS:
        raise AuthError(
            "Registration is closed; this household already has two members",
            status_code=403,
        )

    if user_count == 0:
        household = Household(name="Home", timezone="UTC")
        db.add(household)
        db.flush()
        ensure_default_categories(db, household.id)
        role = UserRole.ADMIN
    else:
        household = db.scalar(select(Household).limit(1))
        if household is None:
            raise AuthError("No household found to join", status_code=500)
        role = UserRole.MEMBER

    user = User(
        email=email,
        display_name=display_name,
        avatar=avatar,
        hashed_password=hash_password(password),
        role=role,
        household_id=household.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user_count == 0:
        from app.scheduler import schedule_household_jobs

        schedule_household_jobs(household)

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    email = email.strip().lower()
    if not email:
        raise AuthError("Email is required")
    if not password:
        raise AuthError("Password is required")

    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password", status_code=401)

    return user


def request_password_reset(
    db: Session,
    email: str,
    *,
    frontend_base_url: str | None = None,
) -> None:
    email = email.strip().lower()
    if not email:
        raise AuthError("Email is required")

    user = get_user_by_email(db, email)
    if user is None:
        return

    token = create_password_reset_token(user.id)
    base_url = (frontend_base_url or settings.public_frontend_url).rstrip("/")
    reset_url = f"{base_url}/password-reset/confirm?token={token}"

    # Local/dev: always log the link so reset works when SMTP/DNS is unavailable.
    if not settings.is_production:
        logger.warning("Password reset link for %s: %s", user.email, reset_url)

    try:
        _send_password_reset_email(user.email, reset_url)
    except EmailError as exc:
        if settings.is_production:
            raise AuthError(
                "Unable to send password reset email. Please try again later.",
                status_code=503,
            ) from exc
        # Non-production: link is already in logs; do not fail the request.
        logger.warning(
            "Password reset email failed; use the logged link instead: %s", exc
        )


def confirm_password_reset(db: Session, token: str, new_password: str) -> None:
    if not token:
        raise AuthError("Reset token is required")

    validate_password(new_password)
    user_id = decode_token(token, RESET_TOKEN_TYPE)

    user = get_user_by_id(db, user_id)
    if user is None:
        raise AuthError("Invalid or expired reset token", status_code=400)

    user.hashed_password = hash_password(new_password)
    db.commit()


def _send_password_reset_email(to_email: str, reset_url: str) -> None:
    text = (
        "You requested a password reset for Chore Quest.\n\n"
        f"Reset your password using this link (valid for {RESET_TOKEN_EXPIRE_HOURS} hour):\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    html = (
        "<p>You requested a password reset for Chore Quest.</p>"
        f"<p><a href=\"{reset_url}\">Reset your password</a> "
        f"(valid for {RESET_TOKEN_EXPIRE_HOURS} hour).</p>"
        "<p>If you did not request this, you can ignore this email.</p>"
    )
    send_email(
        to=to_email,
        subject="Chore Quest – Password Reset",
        html_body=html,
        text_body=text,
    )


def update_user_profile(db: Session, user: User, *, avatar: str | None = None) -> User:
    if avatar is not None:
        validate_avatar(avatar)
        user.avatar = avatar
    db.commit()
    db.refresh(user)
    return user


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "avatar": user.avatar,
        "role": user.role.value,
        "household_id": user.household_id,
    }
