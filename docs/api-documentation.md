# Medicall - REST API Specification

**Project Name:** Medicall  
**Document Version:** 1.0.0  
**Specification Type:** Proposed OpenAPI / RESTful Architectural Contract  
**Base URL:** `https://api.medicall.local/api/v1` (Production) / `http://localhost:8000/api/v1` (Development)  
**Last Updated:** November 2026  

> **Notice:** This document defines the **proposed** API contract. The endpoints detailed below represent the architectural target and are not yet implemented in application code.

---

## 1. Global API Standards & Conventions

### 1.1 Content Types & Protocols
- **Standard Endpoints:** Request and response bodies use `application/json; charset=utf-8`.
- **AI Streaming Endpoint:** Uses Server-Sent Events with `text/event-stream; charset=utf-8` over HTTP/2.

### 1.2 Authentication & Authorization Headers
Protected endpoints require an `Authorization` header containing a valid Bearer token:
```http
Authorization: Bearer <jwt_access_token>
```

### 1.3 Standard Error Format
All error responses adhere to the following unified schema:
```json
{
  "error": {
    "code": "SLOT_ALREADY_BOOKED",
    "message": "The requested appointment slot has already been reserved.",
    "details": {
      "slot_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    },
    "timestamp": "2026-11-10T06:00:00Z"
  }
}
```

---

## 2. Authentication Endpoints (`/auth`)

### 2.1 `POST /auth/register`
* **Purpose:** Registers a new base user account and creates the corresponding empty `Patient` or `Doctor` domain profile.
* **Authentication:** Public
* **Request Body:**
  ```json
  {
    "email": "sarah.connor@example.com",
    "password": "SecurePassword123!",
    "role": "PATIENT",
    "phone_number": "+1-555-0199",
    "first_name": "Sarah",
    "last_name": "Connor",
    "date_of_birth": "1985-05-12"
  }
  ```
* **Validation Rules:**
  - `email`: Valid RFC 5322 email string.
  - `password`: Minimum 8 characters, at least 1 uppercase letter, 1 number, and 1 special symbol.
  - `role`: Must be `'PATIENT'` or `'DOCTOR'`. (`'ADMIN'` cannot self-register).
* **Response Body (`201 Created`):**
  ```json
  {
    "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "email": "sarah.connor@example.com",
    "role": "PATIENT",
    "created_at": "2026-11-10T06:00:00Z"
  }
  ```
* **Status Codes:** `201 Created`, `400 Bad Request` (Email already registered), `422 Unprocessable Entity` (Schema validation failure).

---

### 2.2 `POST /auth/login`
* **Purpose:** Authenticates user credentials and issues a signed JWT access token.
* **Authentication:** Public
* **Request Body:**
  ```json
  {
    "email": "sarah.connor@example.com",
    "password": "SecurePassword123!"
  }
  ```
* **Response Body (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "email": "sarah.connor@example.com",
      "role": "PATIENT",
      "first_name": "Sarah",
      "last_name": "Connor"
    }
  }
  ```
* **Status Codes:** `200 OK`, `401 Unauthorized` (Invalid credentials), `403 Forbidden` (Account disabled).

---

### 2.3 `GET /auth/me`
* **Purpose:** Retrieves identity details and profile linkage of the currently authenticated user.
* **Authentication:** Bearer Token (Any Role)
* **Response Body (`200 OK`):**
  ```json
  {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "email": "sarah.connor@example.com",
    "role": "PATIENT",
    "profile_id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    "is_active": true
  }
  ```
* **Status Codes:** `200 OK`, `401 Unauthorized`.

---

## 3. Patient Management Endpoints (`/patients`)

### 3.1 `GET /patients/profile`
* **Purpose:** Retrieves the current authenticated patient's profile.
* **Authentication:** Bearer Token (`PATIENT` role only)
* **Response Body (`200 OK`):**
  ```json
  {
    "id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    "first_name": "Sarah",
    "last_name": "Connor",
    "date_of_birth": "1985-05-12",
    "gender": "Female",
    "blood_group": "O+",
    "emergency_contact_name": "John Connor",
    "emergency_contact_phone": "+1-555-0188",
    "allergies": "Penicillin",
    "medical_notes": "Mild exercise-induced asthma",
    "consent_given_at": "2026-11-01T10:00:00Z"
  }
  ```
* **Status Codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`.

---

### 3.2 `PUT /patients/profile`
* **Purpose:** Updates personal and medical baseline information.
* **Authentication:** Bearer Token (`PATIENT` role only)
* **Request Body:**
  ```json
  {
    "emergency_contact_name": "John Connor",
    "emergency_contact_phone": "+1-555-0188",
    "allergies": "Penicillin, Latex",
    "medical_notes": "Mild exercise-induced asthma. Uses Albuterol inhaler."
  }
  ```
* **Response Body (`200 OK`):** Updated profile object.
* **Status Codes:** `200 OK`, `400 Bad Request`, `401 Unauthorized`.

---

### 3.3 `POST /patients/consent`
* **Purpose:** Formally logs the patient's informed consent for AI voice processing and data intake.
* **Authentication:** Bearer Token (`PATIENT` role only)
* **Request Body:**
  ```json
  {
    "agreed_to_terms": true,
    "agreed_to_voice_processing": true,
    "agreed_to_non_diagnostic_scope": true
  }
  ```
* **Response Body (`200 OK`):**
  ```json
  {
    "status": "CONSENT_RECORDED",
    "consent_given_at": "2026-11-10T06:15:00Z"
  }
  ```
* **Status Codes:** `200 OK`, `400 Bad Request` (All three consent flags must be true).

---

## 4. Doctor Directory Endpoints (`/doctors`)

### 4.1 `GET /doctors`
* **Purpose:** Search and filter active healthcare providers.
* **Authentication:** Public
* **Query Parameters:**
  - `specialty` (optional): Filter by specialty (e.g., `Cardiology`).
  - `max_fee` (optional): Filter by maximum consultation fee.
  - `query` (optional): Text search across name and qualifications.
  - `page` (default: 1), `limit` (default: 20).
* **Response Body (`200 OK`):**
  ```json
  {
    "total": 45,
    "page": 1,
    "limit": 20,
    "doctors": [
      {
        "id": "d1e2f3a4-5b6c-7d8e-9f0a-1b2c3d4e5f6a",
        "first_name": "Elena",
        "last_name": "Rostova",
        "specialty": "Cardiology",
        "qualifications": "MD, FACC",
        "experience_years": 14,
        "consultation_fee": 120.00,
        "clinic_address": "Suite 400, St. Jude Medical Plaza",
        "is_accepting_patients": true
      }
    ]
  }
  ```

---

### 4.2 `GET /doctors/{id}`
* **Purpose:** Retrieves full clinical bio and practice details for a specific doctor.
* **Authentication:** Public
* **Response Body (`200 OK`):** Complete doctor profile object.
* **Status Codes:** `200 OK`, `404 Not Found`.

---

## 5. Doctor Schedule & Availability Endpoints

### 5.1 `GET /doctors/{id}/availability`
* **Purpose:** Retrieves discrete available consultation slots for a doctor across a date range.
* **Authentication:** Public (or Authenticated)
* **Query Parameters:**
  - `start_date` (required): Format `YYYY-MM-DD`
  - `end_date` (required): Format `YYYY-MM-DD`
* **Response Body (`200 OK`):**
  ```json
  {
    "doctor_id": "d1e2f3a4-5b6c-7d8e-9f0a-1b2c3d4e5f6a",
    "slots": [
      {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "slot_date": "2026-11-15",
        "start_time": "10:00:00",
        "end_time": "10:30:00",
        "status": "AVAILABLE"
      },
      {
        "id": "8d0f778a-8536-51ef-a55c-f18fd2a01bf8",
        "slot_date": "2026-11-15",
        "start_time": "10:30:00",
        "end_time": "11:00:00",
        "status": "AVAILABLE"
      }
    ]
  }
  ```

---

### 5.2 `POST /doctors/{id}/schedules`
* **Purpose:** Configures weekly recurring working templates.
* **Authentication:** Bearer Token (`DOCTOR` role for own ID, or `ADMIN`)
* **Request Body:**
  ```json
  {
    "schedules": [
      {
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "slot_duration_minutes": 30
      },
      {
        "day_of_week": 2,
        "start_time": "09:00:00",
        "end_time": "13:00:00",
        "slot_duration_minutes": 30
      }
    ]
  }
  ```
* **Status Codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`.

---

## 6. Appointment Management Endpoints (`/appointments`)

### 6.1 `POST /appointments`
* **Purpose:** Reserves an available slot and schedules an appointment. Enforces row-level database locking.
* **Authentication:** Bearer Token (`PATIENT` role)
* **Request Body:**
  ```json
  {
    "doctor_id": "d1e2f3a4-5b6c-7d8e-9f0a-1b2c3d4e5f6a",
    "availability_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "chief_complaint": "Experiencing recurring headaches and visual sensitivity.",
    "triage_summary": "Patient reports 2-week history of throbbing unilateral headaches."
  }
  ```
* **Response Body (`201 Created`):**
  ```json
  {
    "id": "9b1c2d3e-4f5a-6b7c-8d9e-0f1a2b3c4d5e",
    "appointment_reference": "MED-20261110-C89",
    "doctor_name": "Dr. Elena Rostova",
    "specialty": "Cardiology",
    "appointment_datetime": "2026-11-15T10:00:00Z",
    "end_datetime": "2026-11-15T10:30:00Z",
    "status": "SCHEDULED",
    "chief_complaint": "Experiencing recurring headaches and visual sensitivity."
  }
  ```
* **Status Codes:**
  - `201 Created`: Appointment successfully confirmed.
  - `409 Conflict`: Slot already booked by another transaction.
  - `400 Bad Request`: Invalid doctor or slot.
  - `401 Unauthorized`.

---

### 6.2 `GET /appointments`
* **Purpose:** Lists appointments for the authenticated patient or doctor.
* **Authentication:** Bearer Token (`PATIENT` or `DOCTOR`)
* **Query Parameters:** `status` (e.g., `SCHEDULED`, `COMPLETED`, `CANCELLED`).
* **Response Body (`200 OK`):** Array of appointment summary objects.

---

### 6.3 `PATCH /appointments/{id}/cancel`
* **Purpose:** Cancels a scheduled appointment and restores the corresponding availability slot to `AVAILABLE`.
* **Authentication:** Bearer Token (Patient who booked, or Booked Doctor)
* **Request Body:**
  ```json
  {
    "cancellation_reason": "Conflict with work schedule."
  }
  ```
* **Response Body (`200 OK`):**
  ```json
  {
    "id": "9b1c2d3e-4f5a-6b7c-8d9e-0f1a2b3c4d5e",
    "status": "CANCELLED_PATIENT",
    "cancelled_at": "2026-11-10T06:30:00Z"
  }
  ```

---

## 7. AI Conversational Assistant Endpoints (`/assistant`)

### 7.1 `POST /assistant/chat/stream`
* **Purpose:** Primary conversational triage endpoint. Executes pre-LLM deterministic safety checks, invokes Google Gemini API with system instructions, and streams responses chunk-by-chunk via Server-Sent Events.
* **Authentication:** Bearer Token (`PATIENT` role)
* **Request Body:**
  ```json
  {
    "message": "I've been having sudden crushing chest pain and numbness in my left arm.",
    "conversation_history": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hello! I am Medicall. How can I assist you with your health today?"}
    ]
  }
  ```
* **Streaming Protocol:** `text/event-stream`
* **Stream Events Breakdown:**

#### Case A: Emergency Red Flag Triggered (Deterministic or AI)
```http
event: emergency
data: {"alert": "EMERGENCY_DETECTED", "guidance": "Critical red-flag symptoms detected. Please seek emergency medical care immediately.", "emergency_phone": "911", "country_code": "US"}

event: close
data: {"reason": "emergency_halt"}
```

#### Case B: Standard Conversational Triage
```http
event: token
data: {"text": "I understand "}

event: token
data: {"text": "you are experiencing a dry cough. "}

event: token
data: {"text": "How many days have you had these symptoms?"}

event: done
data: {"specialty_recommendation": "General Medicine", "suggested_actions": ["check_slots", "clarify_duration"]}
```

---

## 8. Administrative Operations Endpoints (`/admin`)

### 8.1 `GET /admin/audit-logs`
* **Purpose:** Access immutable audit logs of clinical data queries for compliance and security oversight.
* **Authentication:** Bearer Token (`ADMIN` role only)
* **Response Body (`200 OK`):** Paginated audit event log entries.

### 8.2 `PATCH /admin/doctors/{id}/verify`
* **Purpose:** Approves a registered doctor's license and enables public appointment booking.
* **Authentication:** Bearer Token (`ADMIN` role only)
* **Request Body:**
  ```json
  {
    "is_verified": true,
    "verification_notes": "State Medical Board active license confirmed."
  }
  ```

---

## 9. AI Assistant Endpoints (`/ai`)

### 9.1 `POST /ai/chat`
* **Purpose:** Primary conversational healthcare assistant and triage inquiry endpoint with deterministic emergency checks, Google Gemini intelligence, and verified function calling tools.
* **Authentication:** Bearer Token (Authenticated `PATIENT`, `DOCTOR`, or `ADMIN`)
* **Request Headers:**
  ```http
  Authorization: Bearer <jwt_access_token>
  Content-Type: application/json
  ```
* **Request Body (`AIChatRequest`):**
  ```json
  {
    "message": "I would like to book an appointment with Dr. Gregory House for my persistent knee pain.",
    "conversation_history": [
      {
        "role": "user",
        "content": "Hello"
      },
      {
        "role": "assistant",
        "content": "Hello! How can I assist you with your health inquiry today?"
      }
    ],
    "confirmation_token": null
  }
  ```
* **Response Body with Action Proposal requiring Patient Confirmation (`200 OK` - `AIChatResponse`):**
  ```json
  {
    "response": "I have located an available consultation slot with Dr. Gregory House on Tuesday, December 1 at 10:00 AM IST. Would you like me to confirm and book this appointment for you?",
    "urgency_level": "ROUTINE",
    "is_emergency": false,
    "emergency_guidance": null,
    "disclaimer": "Medicall AI is an informational triage and healthcare coordination assistant, not a diagnostic or prescriptive medical device...",
    "metadata": {
      "model": "gemini-3.5-flash",
      "tokens_used": 642,
      "latency_ms": 940.2,
      "is_emergency": false,
      "matched_red_flags": null,
      "tools_called": ["search_doctors", "get_doctor_availability", "book_appointment"],
      "requires_confirmation": true,
      "confirmation_action": "book_appointment",
      "confirmation_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    },
    "pending_confirmation": {
      "requires_confirmation": true,
      "action": "book_appointment",
      "confirmation_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "doctor_name": "Dr. Gregory House",
      "specialty": "Diagnostic Medicine",
      "consultation_fee": 150.0,
      "slot_date": "Tuesday, December 01, 2026",
      "slot_time": "10:00 AM - 10:30 AM",
      "chief_complaint": "persistent knee pain",
      "summary": "Booking with Dr. Gregory House (Diagnostic Medicine) on Tuesday, December 01, 2026 at 10:00 AM - 10:30 AM. Consultation fee: $150.00."
    },
    "success": true,
    "error_message": null
  }
  ```
* **Emergency Red-Flag Response (`200 OK`):**
  ```json
  {
    "response": "⚠️ MEDICAL EMERGENCY DIRECTIVE:\n\nPOTENTIAL MEDICAL EMERGENCY DETECTED (Suspected Acute Coronary Syndrome). Please STOP using online appointment scheduling and call local emergency services (112) or proceed directly to the nearest hospital Emergency Room immediately.",
    "urgency_level": "EMERGENCY",
    "is_emergency": true,
    "emergency_guidance": "POTENTIAL MEDICAL EMERGENCY DETECTED (Suspected Acute Coronary Syndrome). Please STOP using online appointment scheduling and call local emergency services (112) or proceed directly to the nearest hospital Emergency Room immediately. Medicall AI is an informational scheduling assistant and cannot dispatch emergency medical responders or provide emergency care.",
    "disclaimer": "Medicall AI is an informational triage and healthcare coordination assistant...",
    "metadata": {
      "model": "deterministic-safety-guardrail",
      "tokens_used": 0,
      "latency_ms": 0.0,
      "is_emergency": true,
      "matched_red_flags": ["Suspected Acute Coronary Syndrome"],
      "tools_called": null,
      "requires_confirmation": false,
      "confirmation_action": null,
      "confirmation_token": null
    },
    "pending_confirmation": null,
    "success": true,
    "error_message": null
  }
  ```
* **Error Responses:**
  * `401 Unauthorized`: Missing or expired Bearer token.
  * `422 Unprocessable Entity`: Empty message or message exceeding 2000 characters.
  * `503 Service Unavailable`: Gemini experiencing high demand after exponential backoff exhaustion.

### 9.2 `GET /ai/status`
* **Purpose:** Inspects current Gemini AI provider configuration and connectivity status.
* **Authentication:** Bearer Token
* **Response Body (`200 OK`):**
  ```json
  {
    "status": "available",
    "configured": true,
    "model": "gemini-3.5-flash",
    "detail": "Successfully communicated with Google Gemini API.",
    "sample_reply": "Hello"
  }
  ```

### 9.3 `POST /ai/confirm`
* **Purpose:** Deterministically executes an explicit patient-confirmed write operation (booking, cancellation, rescheduling) using a single-use cryptographic confirmation token.
* **Authentication:** Required (`Authorization: Bearer <JWT>`)
* **Request Body (`AIConfirmActionRequest`):**
  ```json
  {
    "confirmation_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
* **Response Body (`200 OK` - `AIConfirmActionResponse`):**
  ```json
  {
    "success": true,
    "action": "book_appointment",
    "message": "Appointment successfully confirmed and booked! Reference: MED-1A2B3C. Date: Friday, November 20, 2026 at 10:00 AM with Dr. Sarah Smith.",
    "appointment_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "reference_code": "MED-1A2B3C",
    "details": {
      "success": true,
      "appointment_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "reference_code": "MED-1A2B3C",
      "status": "SCHEDULED",
      "doctor_name": "Dr. Sarah Smith",
      "specialty": "Cardiology",
      "appointment_date": "Friday, November 20, 2026",
      "appointment_time": "10:00 AM"
    },
    "error": null
  }
  ```
* **Error Responses:**
  * `400 Bad Request`: Token expired, token already consumed, or parameter tampered (`"Confirmation token has already been used. Tokens are strictly single-use to prevent replay."`).
  * `403 Forbidden`: Authenticated user is not a patient, or token does not belong to caller.


---

## 10. Gemini AI Function Calling Tools Catalog

Medicall AI communicates with the database strictly through backend Python services. Gemini NEVER has direct SQL/PostgreSQL access.

| Tool Name | Parameters | Safety / Scope | Description |
| :--- | :--- | :--- | :--- |
| `search_doctors` | `specialty` (str, opt), `doctor_name` (str, opt) | Read-Only | Queries verified clinic doctors accepting new patients. |
| `get_doctor_availability` | `doctor_id` (UUID, req), `date_from` (opt), `date_to` (opt) | Read-Only | Queries available appointment slots for a specific doctor. |
| `get_my_appointments` | *None* | Read-Only (Isolated) | Retrieves appointments strictly for the authenticated patient from JWT token. |
| `book_appointment` | `doctor_id`, `availability_id`, `chief_complaint`, `confirmation_token` (opt) | **Write (Confirmation Required)** | Proposes booking without token; commits booking with valid signed token. |
| `cancel_appointment` | `appointment_id`, `reason` (opt), `confirmation_token` (opt) | **Write (Confirmation Required)** | Proposes cancellation without token; executes cancellation with valid signed token. |
| `reschedule_appointment`| `appointment_id`, `new_availability_id`, `confirmation_token` (opt) | **Write (Confirmation Required)** | Proposes reschedule without token; executes slot exchange with valid signed token. |

### 10.1 Two-Stage Confirmation Protocol & Replay Protection

Write operations (`book_appointment`, `cancel_appointment`, `reschedule_appointment`) follow an atomic, persistent single-use confirmation token protocol:

1. **Stage 1: Proposal Generation**
   - The user or assistant initiates a request without `confirmation_token`.
   - The tool validates arguments, checks slot/appointment existence, and returns `requires_confirmation: true` alongside a short-lived signed JWT containing a unique `jti` (UUID4) and parameter hashes.
   - The Gemini tool loop halts immediately, presenting the action details to the patient.
   - **No database mutations occur at Stage 1.**

2. **Stage 2: Execution & Single-Use Enforcement**
   - Upon the patient's explicit approval, the frontend or assistant invokes the endpoint with the `confirmation_token`.
   - The backend checks:
     - Cryptographic signature and expiration (10-minute maximum lifetime).
     - Action match (`action == expected_action`).
     - Parameter integrity (hash matches submitted parameters).
     - Patient identity match (`sub == current_patient.id`).
     - **Replay Protection Check:** Verifies `jti` against PostgreSQL `consumed_confirmation_tokens`. If the token has been consumed, it is rejected immediately before domain evaluation.
     - Upon successful verification, the `jti` is inserted into `consumed_confirmation_tokens` within the active transaction and flushed.
   - The appointment service performs row-level locking (`with_for_update`) and commits the change.

3. **Confirmation Error Responses:**
   When token validation fails, the tool returns a structured error:
   ```json
   {
     "success": false,
     "error": "This confirmation token has already been used and cannot be replayed.",
     "error_code": "TOKEN_ALREADY_USED"
   }
   ```
   Other error codes: `TOKEN_EXPIRED`, `INVALID_CONFIRMATION_TOKEN`, `PATIENT_MISMATCH`, `ACTION_MISMATCH`, `PARAMETER_TAMPERED`.




