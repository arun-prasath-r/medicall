# Medicall - Security, Privacy & Compliance Specification

**Project Name:** Medicall  
**Document Version:** 1.0.0  
**Status:** Security Architecture Specification  
**Compliance Context:** HIPAA-conscious & GDPR-aligned health data protection principles  
**Last Updated:** November 2026  

---

## 1. Threat Model & Security Principles

As a voice-enabled healthcare assistance and appointment management system, Medicall processes Protected Health Information (PHI) and sensitive patient demographics. The security architecture enforces the following non-negotiable principles:

1. **Defense-in-Depth:** Security controls exist at the network, application middleware, database query, and storage layers.
2. **Zero Trust for External Integrations:** External AI services (Google Gemini) are strictly mediated through backend proxy wrappers and never possess direct credentials or database connectivity.
3. **Data Minimization:** No raw audio waveforms are ever transmitted to or stored on backend servers. Speech recognition and synthesis execute entirely within the client's local browser environment.
4. **Tenant Isolation:** Every database transaction involving clinical or patient data is scoped to the authenticated caller's identity to prevent Insecure Direct Object Reference (IDOR) attacks.

---

## 2. Authentication & Credential Management

### 2.1 Cryptographic Password Hashing
- **Algorithm:** `bcrypt` with a minimum work factor (cost) of `12`.
- **Implementation:** Utilizes Python's `passlib[bcrypt]` library.
- **Salt Generation:** Unique, cryptographically strong 128-bit salt automatically generated per password hash.
- **Storage:** Plaintext passwords are never logged, cached, or written to disk. Only the resulting 60-character bcrypt hash is persisted in `users.hashed_password`.

### 2.2 JSON Web Token (JWT) Architecture
- **Token Format:** Signed JSON Web Tokens conforming to RFC 7519.
- **Signing Algorithm:** `HMAC-SHA256` (`HS256`) using a cryptographically random 256-bit secret key (`JWT_SECRET_KEY`) managed via environment variables.
- **Token Claims Payload:**
  ```json
  {
    "sub": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "role": "PATIENT",
    "email": "patient@example.com",
    "profile_id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    "iat": 1794297600,
    "exp": 1794301200
  }
  ```
- **Token Expiration:** Access tokens expire after 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`).
- **Transport:** Carried via the HTTP `Authorization: Bearer <token>` header over TLS 1.3.

---

## 3. Role-Based Access Control (RBAC) & Authorization Matrix

Medicall enforces three distinct system roles verified by FastAPI dependency injection middlewares (`require_role`):

| Endpoint / Resource | Public | `PATIENT` | `DOCTOR` | `ADMIN` | Authorization Rule |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **User Registration / Login** | Yes | Yes | Yes | Yes | Base public auth flow |
| **Doctor Directory Browsing** | Yes | Yes | Yes | Yes | Read-only public practitioner info |
| **View Own Patient Profile** | No | Yes | No | No | Strictly scoped to own `patient_id` |
| **Update Own Patient Profile**| No | Yes | No | No | Strictly scoped to own `patient_id` |
| **Record Consent** | No | Yes | No | No | Patient must consent prior to assistant use |
| **AI Conversational Triage** | No | Yes | No | No | Authenticated patient triage session |
| **Book Appointment** | No | Yes | No | No | Requires active patient profile & consent |
| **View Patient Appointments** | No | Yes | No | No | Scoped to `patient_id = current_user.patient_id` |
| **Configure Doctor Schedules**| No | No | Yes | Yes | Doctor modifies only their own schedule |
| **View Doctor Appointments** | No | No | Yes | Yes | Doctor sees only their booked patients |
| **Verify Doctor Credentials** | No | No | No | Yes | Admin reviews medical licenses |
| **Audit Logs Access** | No | No | No | Yes | Admin compliance and security view |

---

## 4. Patient Data Isolation & IDOR Mitigation

To ensure patient records remain completely isolated:
1. **No Client-Supplied Patient IDs for Mutations:** The backend never trusts patient IDs passed in HTTP request bodies or query parameters for patient operations. Instead, it derives `patient_id` directly from the authenticated JWT session:
   ```python
   # FastAPI Dependency Enforcement Pattern
   current_patient = await get_current_patient(current_user=Depends(get_current_user), db=Depends(get_db))
   # All queries explicitly enforce: WHERE appointments.patient_id = current_patient.id
   ```
2. **UUID Primary Keys:** All tables use globally unique 128-bit UUIDv4 identifiers rather than sequential integers, preventing enumeration and crawling attacks.
3. **Doctor-Patient Access Linkage:** A doctor can only access a patient's triage notes if an active or historical appointment exists between that specific doctor and patient in the `appointments` table.

---

## 5. Secret & API Key Management

### 5.1 Google Gemini API Key Isolation
- The Google Gemini API key (`GEMINI_API_KEY`) is stored strictly in server-side environment variables and parsed via Pydantic `BaseSettings`.
- **Absolute Client Boundary:** The Gemini key is **never** bundled, compiled, or referenced in the frontend React codebase.
- Frontend users interact with Gemini solely through the backend proxy route `POST /api/v1/assistant/chat/stream`.

### 5.2 Environment Variable Security
- All sensitive credentials (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`) reside in `.env` files that are strictly excluded from source control via `.gitignore`.
- An sanitized `.env.example` file is maintained containing template variable keys without values.

---

## 6. Network Security & In-Transit Encryption

- **Transport Layer Security:** All production traffic requires HTTPS over TLS 1.3 (TLS 1.2 minimum).
- **HTTP Strict Transport Security (HSTS):** Enforced with `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
- **Cross-Origin Resource Sharing (CORS):** The FastAPI CORS middleware explicitly whitelists only the designated frontend domain. Wildcard origins (`*`) are strictly prohibited on authenticated routes.
- **Content Security Policy (CSP):** Configured on the frontend to block unauthorized cross-site script execution.

---

## 7. Patient Consent, Privacy & Retention Policies

### 7.1 Informed Consent Protocol
- Before any voice interaction or health triage begins, the user must pass an explicit consent screen explaining:
  1. That Medicall is an AI-powered conversational tool, **not** a licensed medical doctor.
  2. That the assistant does not offer binding clinical diagnoses.
  3. That browser speech recognition will process their voice locally into text.
- The timestamp of agreement is recorded permanently in `patients.consent_given_at`.

### 7.2 Zero Audio Storage Policy
- Medicall operates on a zero-audio persistence policy. The Web Speech API executes speech recognition inside the client's browser engine. No `.wav`, `.mp3`, or audio streams are ever uploaded, recorded, or saved on Medicall servers.

### 7.3 Data Retention & Automated Purging
- **Triage Transcripts:** Text transcripts and AI conversational notes are stored with an active retention period (default: 30 days) solely to allow the patient and doctor to review symptoms during scheduled consultations.
- **Automated Deletion:** An automated background task runs periodically to purge or pseudonymize conversation transcripts older than the retention threshold.
- **Right to Erasure (GDPR / Privacy Compliance):** Patients may request account deletion, triggering a cascading removal of their profile, personal health notes, and conversation history.

---

## 8. Immutable Audit Logging

Every read or write access involving Protected Health Information (PHI) produces an immutable audit log entry:

| Field | Description | Example |
| :--- | :--- | :--- |
| `event_id` | UUID of the audit event | `4a3b2c1d-0000-0000-0000-123456789abc` |
| `timestamp` | UTC ISO-8601 timestamp | `2026-11-10T06:45:00Z` |
| `actor_id` | User UUID performing the operation | `d1e2f3a4-5b6c-7d8e-9f0a-1b2c3d4e5f6a` |
| `actor_role`| System role of the actor | `DOCTOR` |
| `action` | Action verb performed | `VIEW_PATIENT_TRIAGE_SUMMARY` |
| `resource_id`| Target resource identifier | `Appointment: 9b1c2d3e-4f5a-6b7c-8d9e-0f1a2b3c4d5e` |
| `ip_address` | Masked client IP address | `192.168.1.xxx` |
| `status` | Execution status | `SUCCESS` |

Audit logs are stored in a dedicated, append-only log table to detect potential data access anomalies or compliance violations.

