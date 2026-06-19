"""
main.py
-------
The Course Registration System backend (FastAPI).

Run locally:
    uvicorn main:app --reload

Interactive API docs are available at http://127.0.0.1:8000/docs

Implemented endpoints (17 total):
    POST   /register            Register a new student
    POST   /login               Authenticate user, return JWT
    GET    /students            View all students        (admin)
    GET    /students/{id}       View a single student
    PUT    /students/{id}       Update a student
    DELETE /students/{id}       Delete a student         (admin)
    POST   /courses             Add a new course         (admin)
    GET    /courses             View all courses (+search/filter)
    GET    /courses/{id}        View a single course
    PUT    /courses/{id}        Update a course          (admin)
    DELETE /courses/{id}        Delete a course          (admin)
    POST   /enroll              Enrol a student in a course
    DELETE /enroll/{id}         Drop a course (by registration id)
    GET    /registrations       View all registrations
    GET    /students/{id}/courses   Courses a student is enrolled in
    GET    /dashboard           Dashboard statistics
    GET    /                    Health check
"""

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from auth import (
    create_access_token,
    get_current_student,
    hash_password,
    require_admin,
    verify_password,
)
from database import Base, engine, get_db

# Create database tables if they do not already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Course Registration System API",
    description="A full-stack course registration system built with FastAPI.",
    version="1.0.0",
)

# Allow the frontend (any origin during development) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================================
# Health check
# ==========================================================================
@app.get("/", tags=["Health"])
def root():
    return {"message": "Course Registration System API is running.", "docs": "/docs"}


# ==========================================================================
# Authentication
# ==========================================================================
@app.post("/register", response_model=schemas.StudentOut, tags=["Auth"], status_code=201)
def register(payload: schemas.StudentRegister, db: Session = Depends(get_db)):
    """Create a new student account."""
    existing = (
        db.query(models.Student)
        .filter(models.Student.email == payload.email)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    student = models.Student(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        department=payload.department,
        role="student",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.post("/login", response_model=schemas.Token, tags=["Auth"])
def login(payload: schemas.StudentLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT access token."""
    student = (
        db.query(models.Student)
        .filter(models.Student.email == payload.email)
        .first()
    )
    if not student or not verify_password(payload.password, student.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": str(student.student_id), "role": student.role})
    return {"access_token": token, "token_type": "bearer", "student": student}


# ==========================================================================
# Students (CRUD)
# ==========================================================================
@app.get("/students", response_model=List[schemas.StudentOut], tags=["Students"])
def get_students(
    db: Session = Depends(get_db),
    _: models.Student = Depends(require_admin),
):
    """List all students (admin only)."""
    return db.query(models.Student).order_by(models.Student.student_id).all()


@app.get("/students/{student_id}", response_model=schemas.StudentOut, tags=["Students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get a single student by id."""
    student = (
        db.query(models.Student)
        .filter(models.Student.student_id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@app.put("/students/{student_id}", response_model=schemas.StudentOut, tags=["Students"])
def update_student(
    student_id: int,
    payload: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    current: models.Student = Depends(get_current_student),
):
    """Update a student. A student may update their own profile; admins may
    update anyone."""
    if current.role != "admin" and current.student_id != student_id:
        raise HTTPException(status_code=403, detail="You can only update your own profile.")

    student = (
        db.query(models.Student)
        .filter(models.Student.student_id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        data["password"] = hash_password(data["password"])
    elif "password" in data:
        del data["password"]

    # Prevent duplicate emails.
    if "email" in data and data["email"] != student.email:
        clash = (
            db.query(models.Student)
            .filter(models.Student.email == data["email"])
            .first()
        )
        if clash:
            raise HTTPException(status_code=400, detail="Email already in use.")

    for field, value in data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student


@app.delete("/students/{student_id}", tags=["Students"])
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: models.Student = Depends(require_admin),
):
    """Delete a student (admin only)."""
    student = (
        db.query(models.Student)
        .filter(models.Student.student_id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully."}


# ==========================================================================
# Courses (CRUD + search + filter)
# ==========================================================================
@app.post("/courses", response_model=schemas.CourseOut, tags=["Courses"], status_code=201)
def create_course(
    payload: schemas.CourseCreate,
    db: Session = Depends(get_db),
    _: models.Student = Depends(require_admin),
):
    """Add a new course (admin only)."""
    course = models.Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@app.get("/courses", response_model=List[schemas.CourseOut], tags=["Courses"])
def get_courses(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by course name or instructor"),
    instructor: Optional[str] = Query(None, description="Filter by instructor"),
    min_seats: Optional[int] = Query(None, ge=0, description="Only courses with at least this many free seats"),
    max_credits: Optional[int] = Query(None, ge=1, description="Maximum credit hours"),
):
    """List all courses. Supports optional search and filtering."""
    query = db.query(models.Course)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Course.course_name.ilike(like))
            | (models.Course.instructor.ilike(like))
        )
    if instructor:
        query = query.filter(models.Course.instructor.ilike(f"%{instructor}%"))
    if min_seats is not None:
        query = query.filter(models.Course.available_seats >= min_seats)
    if max_credits is not None:
        query = query.filter(models.Course.credit_hours <= max_credits)

    return query.order_by(models.Course.course_id).all()


@app.get("/courses/{course_id}", response_model=schemas.CourseOut, tags=["Courses"])
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get a single course by id."""
    course = (
        db.query(models.Course)
        .filter(models.Course.course_id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course


@app.put("/courses/{course_id}", response_model=schemas.CourseOut, tags=["Courses"])
def update_course(
    course_id: int,
    payload: schemas.CourseUpdate,
    db: Session = Depends(get_db),
    _: models.Student = Depends(require_admin),
):
    """Update a course (admin only)."""
    course = (
        db.query(models.Course)
        .filter(models.Course.course_id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


@app.delete("/courses/{course_id}", tags=["Courses"])
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _: models.Student = Depends(require_admin),
):
    """Delete a course (admin only)."""
    course = (
        db.query(models.Course)
        .filter(models.Course.course_id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully."}


# ==========================================================================
# Enrolment / Registrations
# ==========================================================================
def _registration_to_out(reg: models.Registration) -> schemas.RegistrationOut:
    """Build a friendly registration response including course/student names."""
    return schemas.RegistrationOut(
        registration_id=reg.registration_id,
        student_id=reg.student_id,
        course_id=reg.course_id,
        registration_date=reg.registration_date,
        course_name=reg.course.course_name if reg.course else None,
        instructor=reg.course.instructor if reg.course else None,
        credit_hours=reg.course.credit_hours if reg.course else None,
        student_name=reg.student.name if reg.student else None,
    )


@app.post("/enroll", response_model=schemas.RegistrationOut, tags=["Enrollment"], status_code=201)
def enroll(
    payload: schemas.EnrollCreate,
    db: Session = Depends(get_db),
    current: models.Student = Depends(get_current_student),
):
    """Enrol a student in a course. Decrements available seats by one."""
    # A student may only enrol themselves (admins may enrol anyone).
    if current.role != "admin" and current.student_id != payload.student_id:
        raise HTTPException(status_code=403, detail="You can only enrol yourself.")

    student = (
        db.query(models.Student)
        .filter(models.Student.student_id == payload.student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    course = (
        db.query(models.Course)
        .filter(models.Course.course_id == payload.course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    # Already enrolled?
    existing = (
        db.query(models.Registration)
        .filter(
            models.Registration.student_id == payload.student_id,
            models.Registration.course_id == payload.course_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course.")

    if course.available_seats <= 0:
        raise HTTPException(status_code=400, detail="No seats available for this course.")

    registration = models.Registration(
        student_id=payload.student_id, course_id=payload.course_id
    )
    course.available_seats -= 1
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return _registration_to_out(registration)


@app.delete("/enroll/{registration_id}", tags=["Enrollment"])
def drop_course(
    registration_id: int,
    db: Session = Depends(get_db),
    current: models.Student = Depends(get_current_student),
):
    """Drop a course by registration id. Frees one seat back up."""
    registration = (
        db.query(models.Registration)
        .filter(models.Registration.registration_id == registration_id)
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found.")

    if current.role != "admin" and current.student_id != registration.student_id:
        raise HTTPException(status_code=403, detail="You can only drop your own courses.")

    # Return the seat to the course.
    course = (
        db.query(models.Course)
        .filter(models.Course.course_id == registration.course_id)
        .first()
    )
    if course:
        course.available_seats += 1

    db.delete(registration)
    db.commit()
    return {"message": "Course dropped successfully."}


@app.get("/registrations", response_model=List[schemas.RegistrationOut], tags=["Enrollment"])
def get_registrations(
    db: Session = Depends(get_db),
    _: models.Student = Depends(require_admin),
):
    """View all registrations across the system (admin only)."""
    regs = (
        db.query(models.Registration)
        .order_by(models.Registration.registration_id)
        .all()
    )
    return [_registration_to_out(r) for r in regs]


@app.get(
    "/students/{student_id}/courses",
    response_model=List[schemas.RegistrationOut],
    tags=["Enrollment"],
)
def get_student_courses(
    student_id: int,
    db: Session = Depends(get_db),
    current: models.Student = Depends(get_current_student),
):
    """List all courses a particular student is enrolled in."""
    if current.role != "admin" and current.student_id != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own courses.")

    regs = (
        db.query(models.Registration)
        .filter(models.Registration.student_id == student_id)
        .order_by(models.Registration.registration_id)
        .all()
    )
    return [_registration_to_out(r) for r in regs]


# ==========================================================================
# Dashboard
# ==========================================================================
@app.get("/dashboard", response_model=schemas.DashboardStats, tags=["Dashboard"])
def dashboard(db: Session = Depends(get_db)):
    """Return high-level statistics for the dashboards."""
    total_students = db.query(func.count(models.Student.student_id)).scalar() or 0
    total_courses = db.query(func.count(models.Course.course_id)).scalar() or 0
    total_registrations = (
        db.query(func.count(models.Registration.registration_id)).scalar() or 0
    )
    total_seats = db.query(func.coalesce(func.sum(models.Course.available_seats), 0)).scalar() or 0

    return schemas.DashboardStats(
        total_students=total_students,
        total_courses=total_courses,
        total_registrations=total_registrations,
        total_seats_available=total_seats,
    )
