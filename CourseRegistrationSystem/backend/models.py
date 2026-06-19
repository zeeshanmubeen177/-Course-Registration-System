"""
models.py
---------
SQLAlchemy ORM models for the Course Registration System.

Tables (as described in the project documentation):
    - students        : student accounts
    - courses         : available courses
    - registrations   : junction table linking students to courses
"""

from datetime import date

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class Student(Base):
    """A student (or admin) account."""

    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # stored hashed, never plain text
    department = Column(String(120), nullable=True)
    # "student" or "admin". Used to unlock the admin dashboard.
    role = Column(String(20), nullable=False, default="student")

    # One student -> many registrations.
    registrations = relationship(
        "Registration",
        back_populates="student",
        cascade="all, delete-orphan",
    )


class Course(Base):
    """A course students can enrol in."""

    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_name = Column(String(150), nullable=False)
    instructor = Column(String(120), nullable=True)
    credit_hours = Column(Integer, nullable=False, default=3)
    available_seats = Column(Integer, nullable=False, default=30)

    # One course -> many registrations.
    registrations = relationship(
        "Registration",
        back_populates="course",
        cascade="all, delete-orphan",
    )


class Registration(Base):
    """Junction table: which student is enrolled in which course."""

    __tablename__ = "registrations"

    registration_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    student_id = Column(
        Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False
    )
    course_id = Column(
        Integer, ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False
    )
    registration_date = Column(Date, nullable=False, default=date.today)

    student = relationship("Student", back_populates="registrations")
    course = relationship("Course", back_populates="registrations")

    # A student cannot enrol in the same course twice.
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )
