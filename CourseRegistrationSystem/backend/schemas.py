"""
schemas.py
----------
Pydantic models (schemas) used to validate request bodies and shape
JSON responses. Keeping these separate from the SQLAlchemy models keeps
the API clean and prevents leaking the hashed password to clients.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# --------------------------------------------------------------------------
# Student / auth schemas
# --------------------------------------------------------------------------
class StudentRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    department: Optional[str] = None


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class StudentOut(BaseModel):
    student_id: int
    name: str
    email: EmailStr
    department: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentOut


# --------------------------------------------------------------------------
# Course schemas
# --------------------------------------------------------------------------
class CourseBase(BaseModel):
    course_name: str = Field(..., min_length=2, max_length=150)
    instructor: Optional[str] = None
    credit_hours: int = Field(default=3, ge=1, le=12)
    available_seats: int = Field(default=30, ge=0, le=1000)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    instructor: Optional[str] = None
    credit_hours: Optional[int] = Field(default=None, ge=1, le=12)
    available_seats: Optional[int] = Field(default=None, ge=0, le=1000)


class CourseOut(CourseBase):
    course_id: int

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Registration / enrolment schemas
# --------------------------------------------------------------------------
class EnrollCreate(BaseModel):
    student_id: int
    course_id: int


class RegistrationOut(BaseModel):
    registration_id: int
    student_id: int
    course_id: int
    registration_date: date
    # Friendly extra fields for the frontend.
    course_name: Optional[str] = None
    instructor: Optional[str] = None
    credit_hours: Optional[int] = None
    student_name: Optional[str] = None

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Dashboard schema
# --------------------------------------------------------------------------
class DashboardStats(BaseModel):
    total_students: int
    total_courses: int
    total_registrations: int
    total_seats_available: int
