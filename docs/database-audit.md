# Medicall — PostgreSQL Database & Schema Audit

**Document Version:** 1.0.0  
**Audit Date:** 12 November 2026  
**Auditor:** Senior Database Architect & Full-Stack Engineer  
**Database Engine:** PostgreSQL 16.15 (Debian 16.15-1.pgdg130+1)  

---

## 1. Container & Connectivity Configuration

### 1.1 Container Architecture & Port Isolation
Two separate PostgreSQL containers were inspected on the development host:

| Container Name | Image | Host Port | Container Port | Purpose & Project | Status |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`medicall-postgres`** | `postgres:16` | **5433** | **5432** | **Medicall Healthcare Platform** | **UP (Healthy)** |
| `smart-billing-postgres`| `postgres:16` | 5432 | 5432 | Separate external project | UP (Untouched) |

> [!IMPORTANT]
> To eliminate port collisions with the existing `smart-billing-postgres` instance on default port `5432`, `medicall-postgres` is cleanly mapped to host port **`5433`**. At no point was `smart-billing-postgres` modified, stopped, or queried.

### 1.2 Backend Connection URL
Configured in `backend/.env` and validated by SQLAlchemy session factory:
```env
DATABASE_URL=postgresql+psycopg://medicall_user:********@localhost:5433/medicall_db
```
- **Driver:** Native `psycopg` (v3) binary interface.
- **Database Name:** `medicall_db`
- **Database User:** `medicall_user`
- **Host Connection Verified:** Confirmed active via read-only SQL query (`SELECT version(), current_database(), current_user;`).

---

## 2. Database Tables & Row Counts

The database contains 7 tables in the `public` schema. Inspected via non-destructive queries:

| Table Name | Owner | Row Count | Purpose |
| :--- | :--- | :---: | :--- |
| **`users`** | `medicall_user` | 3 | Core identity, role (PATIENT, DOCTOR, ADMIN), and auth credentials |
| **`patients`** | `medicall_user` | 1 | Demographics, medical notes, emergency contacts, consent records |
| **`doctors`** | `medicall_user` | 1 | Practitioner credentials, specialty, licensing, fees, verification |
| **`doctor_schedules`** | `medicall_user` | 1 | Recurring weekly schedule templates (day of week, start/end time) |
| **`availability`** | `medicall_user` | 33 | Discrete consultation slots (`AVAILABLE`, `BOOKED`, `BLOCKED`) |
| **`appointments`** | `medicall_user` | 5 | Clinical booking records with unique references and UTC timestamps |
| **`alembic_version`** | `medicall_user` | 1 | Migration tracking (`version_num: 4afa13e7839a`) |

---

## 3. Detailed Table Schemas & Constraints

### 3.1 Table `users`
* **Primary Key:** `id` (`UUID`)
* **Columns:**
  - `id`: `UUID`, primary key, default `gen_random_uuid()`
  - `email`: `VARCHAR(255)`, unique, not null, indexed (`ix_users_email`)
  - `hashed_password`: `VARCHAR(255)`, not null (Argon2id format)
  - `role`: `VARCHAR(32)`, not null, indexed (`ix_users_role`), check constraint matching `UserRole` enum values (`PATIENT`, `DOCTOR`, `ADMIN`)
  - `phone_number`: `VARCHAR(32)`, nullable
  - `is_active`: `BOOLEAN`, not null, default `TRUE`
  - `is_verified`: `BOOLEAN`, not null, default `FALSE` (Used for Doctor verification)
  - `created_at`: `TIMESTAMPTZ`, not null, default `CURRENT_TIMESTAMP`
  - `updated_at`: `TIMESTAMPTZ`, not null, default `CURRENT_TIMESTAMP`
* **Relationships:**
  - `1-to-0..1` with `patients` (cascade delete)
  - `1-to-0..1` with `doctors` (cascade delete)

### 3.2 Table `patients`
* **Primary Key:** `id` (`UUID`)
* **Foreign Keys:**
  - `user_id` &rarr; `users.id` (`ON DELETE CASCADE`), unique, not null, indexed
* **Columns:**
  - `first_name`: `VARCHAR(100)`, not null
  - `last_name`: `VARCHAR(100)`, not null
  - `date_of_birth`: `DATE`, not null
  - `gender`: `VARCHAR(32)`, nullable
  - `blood_group`: `VARCHAR(10)`, nullable
  - `emergency_contact_name`: `VARCHAR(100)`, nullable
  - `emergency_contact_phone`: `VARCHAR(32)`, nullable
  - `allergies`: `TEXT`, nullable
  - `medical_notes`: `TEXT`, nullable
  - `consent_given_at`: `TIMESTAMPTZ`, nullable (Captures informed consent for AI triage)
  - `created_at`: `TIMESTAMPTZ`, not null
  - `updated_at`: `TIMESTAMPTZ`, not null
* **Relationships:**
  - `Many-to-1` with `users`
  - `1-to-Many` with `appointments` (cascade delete)

### 3.3 Table `doctors`
* **Primary Key:** `id` (`UUID`)
* **Foreign Keys:**
  - `user_id` &rarr; `users.id` (`ON DELETE CASCADE`), unique, not null, indexed
* **Columns:**
  - `first_name`: `VARCHAR(100)`, not null
  - `last_name`: `VARCHAR(100)`, not null
  - `license_number`: `VARCHAR(100)`, unique, not null, indexed
  - `specialty`: `VARCHAR(100)`, not null, indexed (`ix_doctors_specialty`)
  - `qualifications`: `VARCHAR(255)`, not null
  - `experience_years`: `INTEGER`, not null, check constraint (`chk_doctor_experience_years`: `>= 0`)
  - `bio`: `TEXT`, nullable
  - `consultation_fee`: `NUMERIC(10, 2)`, not null, check constraint (`chk_doctor_consultation_fee`: `>= 0`)
  - `clinic_address`: `TEXT`, nullable
  - `is_accepting_patients`: `BOOLEAN`, not null, default `TRUE`
  - `created_at`: `TIMESTAMPTZ`, not null
  - `updated_at`: `TIMESTAMPTZ`, not null
* **Relationships:**
  - `Many-to-1` with `users`
  - `1-to-Many` with `doctor_schedules` (cascade delete)
  - `1-to-Many` with `availability` (cascade delete)
  - `1-to-Many` with `appointments`

### 3.4 Table `doctor_schedules`
* **Primary Key:** `id` (`UUID`)
* **Foreign Keys:**
  - `doctor_id` &rarr; `doctors.id` (`ON DELETE CASCADE`), not null, indexed
* **Columns:**
  - `day_of_week`: `SMALLINT`, not null, check constraint (`chk_schedule_day_of_week`: `0 <= day_of_week <= 6`, where 0=Monday, 6=Sunday)
  - `start_time`: `TIME`, not null
  - `end_time`: `TIME`, not null, check constraint (`chk_schedule_time_window`: `end_time > start_time`)
  - `slot_duration_minutes`: `INTEGER`, not null, default `30`, check constraint (`> 0`)
  - `is_active`: `BOOLEAN`, not null, default `TRUE`
  - `created_at`: `TIMESTAMPTZ`, not null
  - `updated_at`: `TIMESTAMPTZ`, not null

### 3.5 Table `availability`
* **Primary Key:** `id` (`UUID`)
* **Foreign Keys:**
  - `doctor_id` &rarr; `doctors.id` (`ON DELETE CASCADE`), not null, indexed
* **Columns:**
  - `slot_date`: `DATE`, not null, indexed
  - `start_time`: `TIME`, not null
  - `end_time`: `TIME`, not null, check constraint (`chk_availability_time_window`: `end_time > start_time`)
  - `status`: `VARCHAR(32)`, not null, default `'AVAILABLE'` (`AVAILABLE`, `BOOKED`, `BLOCKED`)
  - `created_at`: `TIMESTAMPTZ`, not null
* **Constraints & Indexes:**
  - Unique Constraint: `uq_doctor_date_slot` on `(doctor_id, slot_date, start_time)` (Prevents duplicate slots)
  - Composite Index: `idx_availability_search` on `(doctor_id, slot_date, status)`
  - Composite Index: `idx_availability_date_status` on `(slot_date, status)`

### 3.6 Table `appointments`
* **Primary Key:** `id` (`UUID`)
* **Foreign Keys:**
  - `patient_id` &rarr; `patients.id` (`ON DELETE RESTRICT`), not null, indexed
  - `doctor_id` &rarr; `doctors.id` (`ON DELETE RESTRICT`), not null, indexed
  - `availability_id` &rarr; `availability.id` (`ON DELETE SET NULL`), unique, nullable, indexed
* **Columns:**
  - `appointment_reference`: `VARCHAR(32)`, unique, not null, indexed (Format: `MED-YYYYMMDD-XXXXXX`)
  - `appointment_datetime`: `TIMESTAMPTZ`, not null, indexed (Standardized to UTC)
  - `end_datetime`: `TIMESTAMPTZ`, not null (Standardized to UTC, check constraint: `end_datetime > appointment_datetime`)
  - `status`: `VARCHAR(32)`, not null, indexed (`SCHEDULED`, `RESCHEDULED`, `COMPLETED`, `CANCELLED_PATIENT`, `CANCELLED_DOCTOR`)
  - `chief_complaint`: `TEXT`, not null
  - `triage_summary`: `TEXT`, nullable
  - `cancellation_reason`: `TEXT`, nullable
  - `created_at`: `TIMESTAMPTZ`, not null
  - `updated_at`: `TIMESTAMPTZ`, not null
* **Composite Indexes:**
  - `idx_appointments_patient_dt` on `(patient_id, appointment_datetime)`
  - `idx_appointments_doctor_dt` on `(doctor_id, appointment_datetime)`

---

## 4. Entity-Relationship Diagram

```mermaid
erDiagram
    users ||--o| patients : "1-to-0..1 (CASCADE)"
    users ||--o| doctors : "1-to-0..1 (CASCADE)"
    doctors ||--o{ doctor_schedules : "1-to-many (CASCADE)"
    doctors ||--o{ availability : "1-to-many (CASCADE)"
    doctors ||--o{ appointments : "1-to-many (RESTRICT)"
    patients ||--o{ appointments : "1-to-many (RESTRICT)"
    availability ||--o| appointments : "1-to-0..1 (SET NULL on cancel)"

    users {
        UUID id PK
        VARCHAR email UK
        VARCHAR hashed_password
        VARCHAR role
        VARCHAR phone_number
        BOOLEAN is_active
        BOOLEAN is_verified
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    patients {
        UUID id PK
        UUID user_id FK,UK
        VARCHAR first_name
        VARCHAR last_name
        DATE date_of_birth
        VARCHAR gender
        VARCHAR blood_group
        VARCHAR emergency_contact_name
        VARCHAR emergency_contact_phone
        TEXT allergies
        TEXT medical_notes
        TIMESTAMPTZ consent_given_at
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    doctors {
        UUID id PK
        UUID user_id FK,UK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR license_number UK
        VARCHAR specialty
        VARCHAR qualifications
        INTEGER experience_years
        TEXT bio
        NUMERIC consultation_fee
        TEXT clinic_address
        BOOLEAN is_accepting_patients
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    doctor_schedules {
        UUID id PK
        UUID doctor_id FK
        SMALLINT day_of_week
        TIME start_time
        TIME end_time
        INTEGER slot_duration_minutes
        BOOLEAN is_active
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    availability {
        UUID id PK
        UUID doctor_id FK
        DATE slot_date
        TIME start_time
        TIME end_time
        VARCHAR status
        TIMESTAMPTZ created_at
    }

    appointments {
        UUID id PK
        VARCHAR appointment_reference UK
        UUID patient_id FK
        UUID doctor_id FK
        UUID availability_id FK,UK
        TIMESTAMPTZ appointment_datetime
        TIMESTAMPTZ end_datetime
        VARCHAR status
        TEXT chief_complaint
        TEXT triage_summary
        TEXT cancellation_reason
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
```

---

## 5. Migration Status & Schema Consistency

1. **Alembic Version Check:**
   - Database record: `4afa13e7839a`
   - Migration file: `backend/alembic/versions/4afa13e7839a_initial_schema_users_patients_doctors_.py`
   - Status: **Up to date (HEAD)**.
2. **Schema Drift Analysis:**
   - Every column, foreign key constraint, index, check constraint, and default value defined in the SQLAlchemy 2.0 ORM models matches the PostgreSQL database tables.
   - **Zero schema drift detected.**
   - No migration generation or database alteration is required.

