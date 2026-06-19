"""
auth.py
-------
Authentication helpers: password hashing and JSON Web Token (JWT) creation
and verification.

Passwords are hashed with PBKDF2-SHA256 (pure Python, no system libraries
needed, so it installs and runs anywhere). Tokens are signed with PyJWT.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt  # PyJWT
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
import models

# Secret key used to sign tokens. ALWAYS override this in production via env var.
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# PBKDF2-SHA256 needs no native compilation, so it is very reliable to install.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Tells FastAPI/Swagger where to obtain a token (the /login endpoint).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def hash_password(plain_password: str) -> str:
    """Return a salted hash for the given plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against its stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT containing the given data plus an expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_student(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Student:
    """
    Decode the token from the Authorization header and return the matching
    Student. Raises 401 if the token is missing or invalid.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get("sub")
        if student_id is None:
            raise credentials_error
    except jwt.PyJWTError:
        raise credentials_error

    student = (
        db.query(models.Student)
        .filter(models.Student.student_id == int(student_id))
        .first()
    )
    if student is None:
        raise credentials_error
    return student


def require_admin(
    current: models.Student = Depends(get_current_student),
) -> models.Student:
    """Dependency that only allows admin accounts through."""
    if current.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this action.",
        )
    return current
