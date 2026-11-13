# Medicall - Backend Service

Asynchronous RESTful API backend for the Medicall AI-powered healthcare assistance and doctor appointment management platform.

---

## 1. Technology Stack

- **Python:** 3.11+
- **Web Framework:** FastAPI (v0.115+)
- **ASGI Server:** Uvicorn
- **Database:** PostgreSQL 15+ (with SQLite support for isolated tests)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Validation:** Pydantic v2 & Pydantic-Settings
- **Security:** Argon2id (`argon2-cffi`) password hashing & signed JWT tokens (`pyjwt`)
- **Driver:** Psycopg 3 (`psycopg[binary]`)
- **Testing:** Pytest & HTTPX

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── appointments.py  # Booking, rescheduling, cancellation
│   │       │   ├── auth.py          # Registration, login, profile retrieval
│   │       │   ├── availability.py  # Slot queries, creation, generation
│   │       │   ├── doctors.py       # Doctor directory, search, schedules
│   │       │   └── patients.py      # Patient profile and consent
│   │       └── router.py            # Aggregated v1 router & health check
│   ├── core/
│   │   ├── config.py                # Pydantic BaseSettings
│   │   ├── dependencies.py          # Auth, RBAC, DB session dependencies
│   │   └── security.py              # Argon2 hashing & JWT management
│   ├── db/
│   │   ├── base.py                  # DeclarativeBase for SQLAlchemy 2.0
│   │   └── session.py               # Engine & sessionmaker provider
│   ├── models/                      # SQLAlchemy 2.0 Declarative ORM Models
│   │   ├── appointment.py
│   │   ├── availability.py
│   │   ├── doctor.py
│   │   ├── doctor_schedule.py
│   │   ├── patient.py
│   │   └── user.py
│   ├── schemas/                     # Pydantic v2 Request/Response Schemas
│   │   ├── appointment.py
│   │   ├── auth.py
│   │   ├── availability.py
│   │   ├── doctor.py
│   │   ├── patient.py
│   │   └── user.py
│   ├── services/                    # Encapsulated Business Logic Layer
│   │   ├── appointment_service.py   # Row locking & concurrency protection
│   │   ├── auth_service.py          # User & role registration logic
│   │   ├── availability_service.py  # Overlap checks & slot generation
│   │   └── doctor_service.py        # Directory queries & schedules
│   └── main.py                      # FastAPI initialization & CORS
├── alembic/                         # Database migration versions & env
├── tests/                           # Pytest automated test suites
├── requirements.txt                 # Backend Python dependencies
├── .env.example                     # Environment template
└── README.md
```

---

## 3. Environment Configuration

Copy the example environment file and configure local credentials:

```bash
cp .env.example .env
```

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string (e.g. `postgresql+psycopg://user:password@localhost:5432/medicall_db`)
- `JWT_SECRET_KEY`: Cryptographically secure secret string for token signing
- `JWT_ALGORITHM`: `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime in minutes (default: `30`)
- `CORS_ORIGINS`: JSON array of allowed frontend origins (e.g. `["http://localhost:5173"]`)

---

## 4. Setup & Running the Application

### 4.1 Create Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Database Migrations (Alembic)
Apply the database migrations to your PostgreSQL database:
```bash
alembic upgrade head
```

To create a new migration after modifying models:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### 4.3 Start the Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation is automatically accessible at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 5. Running the Automated Tests

The test suite runs against an isolated in-memory SQLite database without modifying persistent data:

```bash
pytest tests -v
```

All 23 automated tests verify:
- Application startup and health checks (`/api/v1/health`)
- Patient and Doctor registration
- Argon2 password hashing and JWT authentication
- Role-based authorization boundaries (`PATIENT`, `DOCTOR`, `ADMIN`)
- Doctor directory filtering and recurring weekly schedules
- Discrete availability slot creation and dynamic slot generation
- Overlapping slot prevention
- Concurrency control and duplicate booking prevention (row locking)
- Appointment cancellation with slot restoration
- Appointment rescheduling
- Multi-tenant patient data isolation (IDOR protection)

