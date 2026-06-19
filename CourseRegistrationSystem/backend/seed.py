"""
seed.py
-------
Populate the database with a default admin account and some sample courses
so the app is usable immediately after setup.

Run once after installing dependencies:
    python seed.py
"""

from database import Base, SessionLocal, engine
from auth import hash_password
import models

Base.metadata.create_all(bind=engine)

SAMPLE_COURSES = [
    {"course_name": "Introduction to Programming", "instructor": "Dr. Ahmed Khan", "credit_hours": 3, "available_seats": 40},
    {"course_name": "Data Structures and Algorithms", "instructor": "Ms. Sara Ali", "credit_hours": 4, "available_seats": 35},
    {"course_name": "Database Systems", "instructor": "Mr. Bilal Hassan", "credit_hours": 3, "available_seats": 30},
    {"course_name": "Web Development with FastAPI", "instructor": "Sir Abdullah Majid Butt", "credit_hours": 3, "available_seats": 45},
    {"course_name": "Operating Systems", "instructor": "Dr. Nadia Sheikh", "credit_hours": 4, "available_seats": 25},
    {"course_name": "Computer Networks", "instructor": "Mr. Usman Tariq", "credit_hours": 3, "available_seats": 30},
    {"course_name": "Cyber Security Fundamentals", "instructor": "Dr. Ayesha Malik", "credit_hours": 3, "available_seats": 28},
    {"course_name": "Software Engineering", "instructor": "Ms. Fatima Noor", "credit_hours": 3, "available_seats": 32},
]


def seed():
    db = SessionLocal()
    try:
        # --- Admin account ------------------------------------------------
        admin_email = "admin@umt.edu.pk"
        if not db.query(models.Student).filter(models.Student.email == admin_email).first():
            db.add(
                models.Student(
                    name="System Admin",
                    email=admin_email,
                    password=hash_password("admin123"),
                    department="Administration",
                    role="admin",
                )
            )
            print(f"Created admin account: {admin_email} / admin123")
        else:
            print("Admin account already exists, skipping.")

        # --- Sample student ----------------------------------------------
        student_email = "zeeshan@umt.edu.pk"
        if not db.query(models.Student).filter(models.Student.email == student_email).first():
            db.add(
                models.Student(
                    name="Zeeshan Mubeen",
                    email=student_email,
                    password=hash_password("student123"),
                    department="Cyber Security",
                    role="student",
                )
            )
            print(f"Created sample student: {student_email} / student123")

        # --- Sample courses ----------------------------------------------
        if db.query(models.Course).count() == 0:
            for c in SAMPLE_COURSES:
                db.add(models.Course(**c))
            print(f"Inserted {len(SAMPLE_COURSES)} sample courses.")
        else:
            print("Courses already exist, skipping.")

        db.commit()
        print("Seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
