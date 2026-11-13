# Medicall — Complete REST API Endpoint Audit

**Document Version:** 1.0.0  
**Audit Date:** 12 November 2026  
**Auditor:** Senior Backend Architect  
**API Specification:** FastAPI / OpenAPI 3.1.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Interactive Docs:** `http://localhost:8000/docs`  

---

## 1. API Architecture & Routing Conventions

FastAPI routes are modularized under `backend/app/api/v1/endpoints/` and aggregated through `backend/app/api/v1/router.py`. The router is mounted on the core FastAPI application in `backend/app/main.py` with prefix `/api/v1`.

### Core Standards:
- **Authentication:** Bearer token via `Authorization: Bearer <JWT>` header, resolved by dependency `get_current_user`.
- **Role-Based Authorization:** Evaluates `UserRole` (`PATIENT`, `DOCTOR`, `ADMIN`).
- **Data Validation:** Pydantic v2 schemas strictly validate incoming request payloads and serialize outgoing response models.
- **Error Standards:** Returns JSON error responses with detailed `detail` messages for client consumption.

---

## 2. Complete Endpoint Inventory (26 Operations across 23 Endpoints)

| HTTP Method | Endpoint Path | Tag | Auth Requirement | Request Schema | Response Schema | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Root | Public | None | `dict` | Root health and API version metadata |
| `GET` | `/api/v1/health` | Health | Public | None | `dict` | System health check (`healthy`, version, service) |
| `POST` | `/api/v1/auth/register` | Authentication | Public | `UserRegister` | `TokenResponse` | Registers patient or doctor, hashes password, returns JWT |
| `POST` | `/api/v1/auth/login` | Authentication | Public | `UserLogin` | `TokenResponse` | Authenticates credentials, returns Bearer token and user info |
| `GET` | `/api/v1/auth/me` | Authentication | Bearer (Any) | None | `UserResponse` | Retrieves authenticated user profile |
| `GET` | `/api/v1/patients/me` | Patients | Bearer (Patient) | None | `PatientResponse` | Retrieves demographic profile for logged-in patient |
| `PUT` | `/api/v1/patients/me` | Patients | Bearer (Patient) | `PatientUpdate` | `PatientResponse` | Updates demographics, emergency contact, notes |
| `POST` | `/api/v1/patients/consent` | Patients | Bearer (Patient) | `ConsentRequest` | `dict` | Records patient informed consent timestamp for AI triage |
| `GET` | `/api/v1/doctors` | Doctors | Public | Query params | `List[DoctorResponse]` | Lists verified doctors; filter by specialty/patient acceptance |
| `GET` | `/api/v1/doctors/specialties` | Doctors | Public | None | `List[str]` | Lists all distinct specialties of verified practitioners |
| `GET` | `/api/v1/doctors/{id}` | Doctors | Public | None | `DoctorResponse` | Retrieves full practitioner profile and fee details |
| `GET` | `/api/v1/doctors/{id}/schedules` | Doctors | Public | None | `List[DoctorScheduleResponse]` | Retrieves weekly availability templates for a doctor |
| `POST` | `/api/v1/doctors/{id}/schedules` | Doctors | Bearer (Doctor/Admin)| `DoctorScheduleCreate`| `DoctorScheduleResponse` | Configures recurring weekly availability window |
| `GET` | `/api/v1/doctors/{id}/availability` | Availability | Public | Query params | `List[AvailabilityResponse]` | Lists discrete open consultation slots in a date range |
| `POST` | `/api/v1/doctors/{id}/availability` | Availability | Bearer (Doctor) | `AvailabilityCreate` | `AvailabilityResponse` | Creates a single custom consultation slot |
| `POST` | `/api/v1/doctors/{id}/availability/generate` | Availability | Bearer (Doctor) | `AvailabilityGenerateRequest` | `dict` | Batch-generates discrete slots from weekly templates |
| `POST` | `/api/v1/appointments` | Appointments | Bearer (Patient) | `AppointmentCreate` | `AppointmentResponse` | Atomically books an appointment with row-level slot locking |
| `GET` | `/api/v1/appointments/me` | Appointments | Bearer (Patient/Doctor)| None | `List[AppointmentResponse]` | Lists appointments filtered by user role ownership |
| `GET` | `/api/v1/appointments/{id}` | Appointments | Bearer (Owner/Admin) | None | `AppointmentResponse` | Retrieves single appointment details |
| `PATCH`| `/api/v1/appointments/{id}/cancel` | Appointments | Bearer (Owner/Admin) | `AppointmentCancel` | `AppointmentResponse` | Cancels appointment and restores availability slot to open |
| `PATCH`| `/api/v1/appointments/{id}/reschedule` | Appointments | Bearer (Owner/Admin) | `AppointmentReschedule` | `AppointmentResponse` | Atomically reschedules appointment to a new available slot |
| `GET` | `/api/v1/admin/doctors` | Admin Operations | Bearer (Admin) | None | `List[DoctorResponse]` | Lists all practitioners with verification status |
| `GET` | `/api/v1/admin/doctors/pending` | Admin Operations | Bearer (Admin) | None | `List[DoctorResponse]` | Lists newly registered doctors awaiting license review |
| `PATCH`| `/api/v1/admin/doctors/{id}/verify` | Admin Operations | Bearer (Admin) | `DoctorVerifyRequest` | `DoctorResponse` | Approves doctor license, enabling public appointment booking |
| `POST` | `/api/v1/ai/chat` | AI Clinical Assistant | Bearer (Any) | `AIChatRequest` | `AIChatResponse` | Conversational healthcare triage with red-flags & Gemini |
| `GET` | `/api/v1/ai/status` | AI Clinical Assistant | Bearer (Any) | None | `dict` | Returns Google Gemini API connectivity & model health |

---

## 3. Endpoint Live Verification Results

The live FastAPI backend (PID 1301 on port 8000) was verified using non-destructive programmatic tests:

```bash
# 1. System Health Check
curl -s http://localhost:8000/api/v1/health
# Response: 200 OK -> {"status":"healthy","service":"medicall-backend","version":"1.0.0"}

# 2. Public Doctor Directory
curl -s http://localhost:8000/api/v1/doctors
# Response: 200 OK -> Returns verified doctor list from PostgreSQL

# 3. Doctor Specialties
curl -s http://localhost:8000/api/v1/doctors/specialties
# Response: 200 OK -> ["Psychiatry"]

# 4. OpenAPI Documentation
curl -s -I http://localhost:8000/docs
# Response: 200 OK -> text/html; charset=utf-8 (Swagger UI active)
```

---

## 4. Concurrency & Security in API Endpoints

1. **Appointment Concurrency Protection:**
   - Both `POST /appointments` and `PATCH /appointments/{id}/reschedule` utilize SQLAlchemy row-level locks:
     ```python
     slot = db.query(Availability).filter(Availability.id == slot_id).with_for_update().first()
     ```
   - If two requests attempt to claim the same slot concurrently, the first commits and marks the slot `BOOKED`; the second is blocked until lock release and immediately rejected with `HTTP 409 Conflict`.
2. **Timezone Standardization:**
   - Pydantic serializers enforce strict UTC ISO-8601 formatting (`YYYY-MM-DDTHH:MM:SS+00:00`) for all appointment datetime fields.
3. **Data Isolation (Tenant Protection):**
   - Patients can only retrieve and modify their own appointments. Attempting to view another patient's appointment returns `HTTP 403 Forbidden` or `404 Not Found`.

