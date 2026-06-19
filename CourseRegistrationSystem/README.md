# Course Registration System

A full-stack web application that lets students register for courses online and
lets administrators manage courses and registrations. Built for the **Open Source
Software Development (OSSD)** final semester project at **UMT Lahore**.

| | |
|---|---|
| **Student** | Zeeshan Mubeen |
| **Roll Number** | F2024408151 |
| **Section** | Y9 |
| **Submitted To** | Sir Abdullah Majid Butt |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript (no framework) |
| Backend | Python, FastAPI |
| Database | PostgreSQL (Supabase) — SQLite for local dev |
| ORM | SQLAlchemy |
| Auth | JWT (PyJWT) + PBKDF2 password hashing (passlib) |
| Deployment | Render (backend) + Vercel (frontend) |

---

## Features

**Student**
- Register an account and log in securely
- Browse, search and filter available courses
- View course details
- Enroll in courses and drop them
- View registration history
- View and update profile

**Admin**
- Add, update and delete courses
- View all students and delete student accounts
- View all registrations across the system
- Dashboard with live statistics

---

## Project Structure

```
CourseRegistrationSystem/
├── backend/
│   ├── main.py            # FastAPI app + all API endpoints
│   ├── models.py          # SQLAlchemy models (Students, Courses, Registrations)
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── database.py        # DB connection (SQLite local / PostgreSQL prod)
│   ├── auth.py            # Password hashing + JWT
│   ├── seed.py            # Sample data (admin, student, courses)
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment variable template
├── frontend/
│   ├── index.html         # Home
│   ├── about.html         # About
│   ├── login.html         # Login / Register
│   ├── dashboard.html     # Student dashboard
│   ├── courses.html       # Browse / search / enroll
│   ├── course-details.html# Single course details
│   ├── history.html       # Registration history
│   ├── profile.html       # View / update profile
│   ├── admin.html         # Admin dashboard
│   ├── css/style.css      # Global stylesheet
│   └── js/
│       ├── config.js      # API base URL
│       └── app.js         # Shared helpers (session, API, navbar)
├── screenshots/           # Place project & DB screenshots here
├── render.yaml            # Render deployment config
├── vercel.json            # Vercel deployment config
└── README.md
```

---

## Running Locally

### 1. Backend (FastAPI)

```bash
cd backend

# create a virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# (optional) load sample admin, student and courses
python seed.py

# start the server
uvicorn main:app --reload
```

The API now runs at **http://127.0.0.1:8000**
Interactive docs (Swagger UI): **http://127.0.0.1:8000/docs**

> By default it uses a local SQLite file (`course_registration.db`). No database
> setup is needed to try it out.

**Demo accounts created by `seed.py`:**
- Admin — `admin@umt.edu.pk` / `admin123`
- Student — `zeeshan@umt.edu.pk` / `student123`

### 2. Frontend (HTML/CSS/JS)

The frontend is plain static files. Open `frontend/index.html` directly, or
serve it (recommended, so relative paths work consistently):

```bash
cd frontend
python -m http.server 5500
```

Then visit **http://127.0.0.1:5500**.

Make sure `frontend/js/config.js` points at your backend:

```js
const API_BASE = "http://127.0.0.1:8000";
```

---

## Using Supabase (PostgreSQL)

1. Create a project at [supabase.com](https://supabase.com).
2. Go to **Project Settings → Database → Connection string (URI)** and copy it.
3. In `backend/`, copy `.env.example` to `.env` and set:
   ```
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres
   SECRET_KEY=some-long-random-string
   ```
4. Install python-dotenv if you want `.env` auto-loaded, or export the variables
   in your shell. Render lets you set these in the dashboard directly.
5. Start the app — tables are created automatically on first run.
   Run `python seed.py` once to add sample data.

---

## Deployment

### Backend → Render
1. Push this repo to GitHub.
2. On Render: **New → Web Service**, connect the repo, root directory `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables `DATABASE_URL` (Supabase) and `SECRET_KEY`.
6. Deploy and copy the live API URL.

### Frontend → Vercel
1. Update `frontend/js/config.js` → set `API_BASE` to your Render URL.
2. On Vercel: **New Project**, import the repo, set root directory `frontend`.
3. Deploy. Vercel serves the static site and gives you a live link.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new student |
| POST | `/login` | Authenticate, return JWT |
| GET | `/students` | List all students (admin) |
| GET | `/students/{id}` | View a single student |
| PUT | `/students/{id}` | Update a student |
| DELETE | `/students/{id}` | Delete a student (admin) |
| POST | `/courses` | Add a course (admin) |
| GET | `/courses` | List courses (supports `search`, `instructor`, `min_seats`, `max_credits`) |
| GET | `/courses/{id}` | View a single course |
| PUT | `/courses/{id}` | Update a course (admin) |
| DELETE | `/courses/{id}` | Delete a course (admin) |
| POST | `/enroll` | Enroll a student in a course |
| DELETE | `/enroll/{id}` | Drop a course by registration id |
| GET | `/registrations` | View all registrations (admin) |
| GET | `/students/{id}/courses` | Courses a student is enrolled in |
| GET | `/dashboard` | Dashboard statistics |

---

## Database Schema

**students**: `student_id` (PK), `name`, `email` (unique), `password` (hashed), `department`, `role`
**courses**: `course_id` (PK), `course_name`, `instructor`, `credit_hours`, `available_seats`
**registrations**: `registration_id` (PK), `student_id` (FK), `course_id` (FK), `registration_date`

Relationship: a student can register for many courses and a course can hold many
students; the **registrations** table is the junction table between them.
