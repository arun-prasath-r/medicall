# Medicall - System Requirements & Specification Document

**Project Name:** Medicall  
**Document Version:** 1.1.0  
**Status:** Requirements & Planning Phase  
**Last Updated:** November 2026  

---

## 1. Project Overview

**Medicall** is an AI-powered, voice-enabled healthcare assistance and doctor appointment management platform. It bridges the gap between patients and healthcare providers by combining conversational AI, voice recognition, and clinical appointment workflows.

The system empowers patients to describe their symptoms naturally using voice or text, receive intelligent preliminary health guidance and triage suggestions powered by Google Gemini, and seamlessly discover doctors and book, manage, or reschedule appointments. For healthcare providers and clinics, Medicall provides an organized schedule management system that streamlines appointment queues and optimizes clinical workloads.

### 1.1 Architectural Layout
To ensure modularity, scalability, and clean separation of concerns, the project enforces a strict architectural boundary:
- **Monorepo Structure:** The project lives in a single repository with completely independent top-level application directories.
- **Frontend Application (`/frontend`):** Standalone Single Page Application (SPA) built with React.jss and Vite.
- **Backend Application (`/backend`):** Standalone RESTful API service with Server-Sent Events (SSE) support built with Python and FastAPI.
- **Documentation (`/docs`):** Centralized project specifications, architectural guides, and API documentation.

### 1.2 Technology Stack
| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React.js (v18+) + Vite | Interactive, responsive user interface |
| **Backend** | Python 3.11+ + FastAPI | High-performance asynchronous REST API |
| **Streaming Protocol** | Server-Sent Events (SSE) | Unidirectional real-time streaming of AI conversational tokens |
| **Database** | PostgreSQL (v15+) | Relational data persistence (users, profiles, schedules, appointments) |
| **ORM** | SQLAlchemy (2.0+) + Alembic | Object-relational mapping, data modeling, and schema migrations |
| **AI Engine** | Google Gemini API | Natural language understanding, health assistance, and contextual triage |
| **Speech-to-Text (STT)** | Web Speech API (`SpeechRecognition`) | Client-side real-time voice input capturing |
| **Text-to-Speech (TTS)** | Speech Synthesis API (`SpeechSynthesis`) | Browser-native natural voice response generation |

---

## 2. Problem Statement

1. **Friction in Healthcare Access:** Traditional appointment booking systems rely on tedious manual forms, rigid phone menus, or phone queues during clinic operating hours, discouraging patients from seeking timely care.
2. **Accessibility Barriers:** Elderly patients, visually impaired individuals, or users with low digital literacy struggle with complex graphical interfaces and benefit greatly from hands-free, voice-first interactions.
3. **Symptom Confusion & Misdirected Bookings:** Patients often do not know which medical specialty corresponds to their symptoms, leading to misdirected appointments, wasted clinical time, and delayed treatments.
4. **Administrative Burden on Clinics:** Medical staff spend disproportionate hours answering phone calls, checking calendars, and manually rescheduling appointments rather than delivering patient care.
5. **Emergency Triage Risks:** Untrained patients may attempt to book standard appointments for acute, life-threatening symptoms instead of seeking immediate emergency medical care.

---

## 3. Project Objectives

- **Voice-First Accessibility:** Provide a voice-enabled interface using native browser Speech-to-Text and Text-to-Speech APIs, allowing users to navigate and book appointments hands-free.
- **Multi-Tier Medical Safety:** Combine deterministic, client/server rule-based red-flag checks with Google Gemini AI triage to detect emergencies instantly and direct users to localized emergency services before or during any conversational processing.
- **AI-Powered Health Guidance:** Integrate Google Gemini API to analyze reported symptoms conversationally, recommend appropriate medical specialties, and clarify urgency while strictly providing informational disclaimers (non-diagnostic).
- **Streamlined Appointment Lifecycle:** Enable end-to-end appointment scheduling, status tracking, cancellations, and rescheduling with real-time slot availability.
- **Clean Decoupled Architecture:** Maintain strict isolation between frontend and backend codebases within the monorepo to allow independent testing, deployment, and maintenance.
- **Data Privacy & Security:** Establish secure role-based access control (RBAC), multi-tenant patient data isolation, informed consent workflows, and secure transcript retention policies.

---

## 4. Implementation Status Overview

To maintain clarity across project iterations, features and components are categorized by implementation status:

- **Implemented:** Code is written, integrated, and verified in the workspace.
- **In Progress:** Currently being developed or tested.
- **Proposed:** Defined in requirements and architecture, awaiting development.

> **Current Phase Status:** *Initial Planning & Requirements Phase.*  
> Currently, the workspace is freshly initialized. All functional and technical features listed below are **Proposed**.

---

## 5. Implementation Scope: Core Features vs. Proposed Enhancements

To establish a clear delivery roadmap, features are separated into **Core Scope (MVP / Phase 1)** and **Proposed Future Enhancements (Phase 2+)**:

### 5.1 Original Core Scope (Phase 1 / MVP)
1. **User Authentication & Role Management:** Secure JWT-based authentication supporting distinct `Patient` and `Doctor` roles with individual profiles.
2. **Voice Interface (STT/TTS):** Browser-native speech recognition and speech synthesis for conversational navigation and appointment booking.
3. **Deterministic Emergency Triage & Guardrails:** Hard-coded keyword/rule red-flag interceptor coupled with country-configurable emergency hotline routing.
4. **AI Health Assistant:** Contextual multi-turn symptom guidance and specialist recommendation powered by Google Gemini API with mandatory medical disclaimers.
5. **Doctor Directory & Search:** Filter doctors by specialty, consultation fee, and available dates.
6. **Doctor Schedule & Availability Management:** Weekly recurring schedule templates and daily slot availability generation.
7. **Appointment Lifecycle Management:** Booking, viewing, rescheduling, and cancelling appointments with concurrency controls to prevent double-booking.
8. **Patient Consent & Privacy Controls:** Explicit user consent for audio processing and health data intake.

### 5.2 Proposed Enhancements (Phase 2+ Roadmap)
1. **Automated Clinical Consultation Summaries:** AI-generated structured appointment prep notes summarizing patient conversations for doctor review prior to consultations.
2. **Multi-Language Voice Support:** Dynamic language detection and multilingual voice assistance for non-English speakers.
3. **Automated Reminders & Notifications:** SMS and email notifications for booking confirmations, reminders, and cancellations via third-party gateways (e.g., Twilio, SendGrid).
4. **Telehealth / Video Consultations:** Integrated WebRTC-based video calling between doctors and patients.
5. **EHR / FHIR Interoperability:** Export and sync appointment and clinical summary records with standard Electronic Health Record systems.
6. **Waitlist & Dynamic Slot Reclamation:** Automated patient alerts when a cancelled appointment frees up an earlier slot.

---

## 6. Major Features Breakdown

| ID | Feature Name | Scope Category | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **F-01** | **Voice Interface (STT/TTS)** | Core (Phase 1) | Browser-native voice input via Web Speech API and voice responses via Speech Synthesis API. | **Proposed** |
| **F-02** | **Deterministic Red-Flag Interceptor** | Core (Phase 1) | Rule-based keyword matching that detects acute emergency symptoms immediately without waiting for LLM inference. | **Proposed** |
| **F-03** | **AI Health Assistant** | Core (Phase 1) | Conversational symptom inquiry and specialist recommendation via Google Gemini API with persistent disclaimers. | **Proposed** |
| **F-04** | **Country-Configurable Emergency Hotline** | Core (Phase 1) | Dynamic routing to localized emergency services (e.g., 911, 112, 999) based on deployment configuration. | **Proposed** |
| **F-05** | **Doctor Directory & Search** | Core (Phase 1) | Search and filter doctors by medical specialty, availability, fee, and qualifications. | **Proposed** |
| **F-06** | **Schedule & Availability Engine** | Core (Phase 1) | Weekly schedule definitions and discrete slot generation with database-level uniqueness locks. | **Proposed** |
| **F-07** | **Interactive Appointment Booking** | Core (Phase 1) | Voice-assisted and form-based appointment scheduling, rescheduling, and cancellation. | **Proposed** |
| **F-08** | **User & Role Authentication** | Core (Phase 1) | JWT authentication separating base User identities into Patient and Doctor domain profiles. | **Proposed** |
| **F-09** | **Informed Consent & Data Privacy** | Core (Phase 1) | Explicit audio/health data consent capture, retention management, and isolated patient queries. | **Proposed** |
| **F-10** | **Clinical Consultation Summary** | Enhancement (Phase 2) | Automated AI-generated clinical pre-consultation notes for doctors. | **Proposed** |
| **F-11** | **Multi-Language Voice Support** | Enhancement (Phase 2) | Multilingual voice recognition and speech synthesis. | **Proposed** |
| **F-12** | **External Notifications (SMS/Email)** | Enhancement (Phase 2) | Automated booking alerts, SMS reminders, and schedule change notifications. | **Proposed** |

---

## 7. Medical Safety & Emergency Triage Safeguards

Medical safety is the foundational constraint of Medicall. The platform is explicitly designed **not** to act as a definitive diagnostic instrument, but as an informational and scheduling assistant.

```
                              [ User Input (Voice or Text) ]
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    Layer 1: Deterministic Red-Flag Check     │
                      │  (Client & Server Keyword / Pattern Regex)   │
                      └──────────────────────┬───────────────────────┘
                                             │
                       Is Critical Red Flag Detected?
                                    ├─── YES ───► [ EMERGENCY OVERLAY TRIGGERED ]
                                    │             - Immediate visual alert & audio prompt
                                    │             - Direct click-to-call localized number
                                    │             - Bypass LLM; halt booking flow
                                    │
                                    └─── NO
                                         │
                                         ▼
                      ┌──────────────────────────────────────────────┐
                      │      Layer 2: Google Gemini AI Triage        │
                      │     (Clinical System Prompts & Safety)       │
                      └──────────────────────┬───────────────────────┘
                                             │
                               Does AI detect secondary urgency?
                                    ├─── YES ───► Advise immediate urgent care / ER
                                    └─── NO  ───► Recommend medical specialty & slots
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │     Mandatory Medical Disclaimer Appended    │
                      └──────────────────────────────────────────────┘
```

### 7.1 Multi-Layered Triage Architecture
1. **Layer 1: Deterministic Red-Flag Interceptor (Pre-LLM):**
   - **Emergency detection must never rely exclusively on Gemini API**, protecting against network latency, API outages, or LLM non-determinism.
   - A deterministic, rule-based clinical keyword and regex filter runs on both client input and backend intake.
   - **Monitored Red Flags:** Acute chest pain / pressure radiating to arm or jaw, severe dyspnea (shortness of breath), signs of stroke (F.A.S.T.: facial droop, arm weakness, slurred speech), massive or uncontrolled bleeding, sudden severe head injury or loss of consciousness, acute anaphylaxis (throat swelling, severe wheezing), severe poisoning/ingestion, and active suicidal ideation.
   - **Immediate Action:** If any red-flag criteria are met, the conversational loop is intercepted immediately. The system bypasses standard AI generation, renders a non-dismissible high-priority emergency modal, halts appointment booking, and provides instant emergency contact buttons.

2. **Layer 2: Google Gemini AI Clinical Guardrails (Post-Interceptor):**
   - System prompts instruct the Gemini model to operate strictly within informational and triage boundaries.
   - The model is instructed never to produce a definitive diagnosis or prescribe pharmaceutical dosages.
   - The model categorizes symptom inquiries into appropriate medical specialties (e.g., General Medicine, Cardiology, Dermatology, Orthopedics) and indicates urgency levels (Routine, Soon, Urgent).

### 7.2 Clear Emergency Guidance
- When an emergency is triggered, Medicall presents high-contrast visual alerts accompanied by clear audio instruction: *"An urgent medical symptom has been detected. Medicall cannot treat emergencies. Please immediately call emergency services or proceed to the nearest emergency room."*
- Click-to-call emergency links (`tel:<emergency_number>`) are presented with prominent, accessible tap targets.

### 7.3 Country-Configurable Emergency Numbers
- Emergency contact numbers are decoupled from application code and configured via environment variables and deployment settings:
  - `DEFAULT_COUNTRY_CODE` (e.g., `US`, `GB`, `IN`, `EU`)
  - `EMERGENCY_PHONE_NUMBER` (e.g., `911` for US/Canada, `999` for UK, `112` for EU/India, `000` for Australia)
- The application dynamically formats the emergency alert and calling mechanism based on the configured locale, ensuring reliable regional compliance upon deployment.

### 7.4 Medical Disclaimers
- **Pre-Interaction Disclaimer:** Displayed prior to starting the voice assistant. Users must acknowledge that the tool is informational and not a substitute for clinical judgment.
- **Persistent Interface Notice:** A permanent, legible footer disclaimer appears across all conversational views.
- **Per-Response Disclosure:** Every AI-generated response includes a standardized footer: *"Notice: AI-generated informational guidance only. Not medical advice. For emergencies, call your local emergency service immediately."*

---

## 8. Proposed Database Architecture & Entity Relationships

The relational database separates authentication/identity concerns from domain-specific roles, enforcing clean distinction between base accounts, patients, and healthcare providers.

```
┌─────────────────────────────────┐
│              Users              │
├─────────────────────────────────┤
│ id (PK, UUID)                   │
│ email (Unique)                  │
│ hashed_password                 │
│ role (PATIENT, DOCTOR, ADMIN)   │
│ phone_number                    │
│ is_active                       │
│ created_at / updated_at         │
└──────────────┬──────────────────┘
               │ 1
               │
               ├────────────────────────────────────────┐
               │ 0..1 (if role == PATIENT)              │ 0..1 (if role == DOCTOR)
               ▼                                        ▼
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│            Patients             │      │             Doctors             │
├─────────────────────────────────┤      ├─────────────────────────────────┤
│ id (PK, UUID)                   │      │ id (PK, UUID)                   │
│ user_id (FK -> Users.id, UNIQUE)│      │ user_id (FK -> Users.id, UNIQUE)│
│ first_name, last_name           │      │ first_name, last_name           │
│ date_of_birth, gender           │      │ license_number (Unique)         │
│ blood_group                     │      │ specialty                       │
│ emergency_contact_name / phone  │      │ qualifications, bio             │
│ allergies, medical_notes        │      │ consultation_fee                │
│ consent_given_at                │      │ is_accepting_patients           │
└──────────────┬──────────────────┘      └──────────────┬──────────────────┘
               │ 1                                      │ 1
               │                                        ├────────────────────────────────┐
               │                                        │ 1                              │ 1
               │                                        ▼                                ▼
               │                         ┌───────────────────────────────┐ ┌───────────────────────────────┐
               │                         │       Doctor_Schedules        │ │         Availability          │
               │                         ├───────────────────────────────┤ ├───────────────────────────────┤
               │                         │ id (PK, UUID)                 │ │ id (PK, UUID)                 │
               │                         │ doctor_id (FK -> Doctors.id)  │ │ doctor_id (FK -> Doctors.id)  │
               │                         │ day_of_week (0=Mon .. 6=Sun)  │ │ slot_date (DATE)              │
               │                         │ start_time (TIME)             │ │ start_time, end_time (TIME)   │
               │                         │ end_time (TIME)               │ │ status (AVAILABLE, BOOKED,    │
               │                         │ slot_duration_minutes (INT)   │ │         BLOCKED)              │
               │                         │ is_active (BOOLEAN)           │ └──────────────┬────────────────┘
               │                         └───────────────────────────────┘                │ 1
               │                                                                          │
               │ N                                                                      N │ 0..1
               └────────────────────────────────► ┌───────────────────────────────┐ ◄─────┘
                                                  │         Appointments          │
                                                  ├───────────────────────────────┤
                                                  │ id (PK, UUID)                 │
                                                  │ appointment_reference (Unique)│
                                                  │ patient_id (FK -> Patients.id)│
                                                  │ doctor_id (FK -> Doctors.id)  │
                                                  │ availability_id (FK, UNIQUE)  │
                                                  │ appointment_datetime (TIMESTAM│
                                                  │ end_datetime (TIMESTAMP)      │
                                                  │ status (SCHEDULED, COMPLETED, │
                                                  │         CANCELLED, RESCHEDULE)│
                                                  │ chief_complaint (TEXT)        │
                                                  │ triage_summary (TEXT)         │
                                                  │ cancellation_reason (TEXT)    │
                                                  │ created_at / updated_at       │
                                                  └───────────────────────────────┘
```

### 8.1 Detailed Entity Definitions

#### 1. `Users` Table (System Identity & Credentials)
- **Purpose:** Stores core identity, credentials, authentication state, and authorization role.
- **Attributes:**
  - `id`: `UUID` (Primary Key, default `uuid_generate_v4()`)
  - `email`: `VARCHAR(255)` (Unique, Indexed, Not Null)
  - `hashed_password`: `VARCHAR(255)` (Not Null)
  - `role`: `ENUM('PATIENT', 'DOCTOR', 'ADMIN')` (Not Null)
  - `phone_number`: `VARCHAR(32)` (Nullable)
  - `is_active`: `BOOLEAN` (Default `True`)
  - `is_verified`: `BOOLEAN` (Default `False`)
  - `created_at`: `TIMESTAMP WITH TIME ZONE` (Default `NOW()`)
  - `updated_at`: `TIMESTAMP WITH TIME ZONE` (Default `NOW()`)

#### 2. `Patients` Table (Patient Domain Profile)
- **Purpose:** Stores demographic, clinical profile, and emergency data specific to patients.
- **Attributes:**
  - `id`: `UUID` (Primary Key)
  - `user_id`: `UUID` (Foreign Key -> `users.id`, Unique, On Delete Cascade, Not Null)
  - `first_name`: `VARCHAR(100)` (Not Null)
  - `last_name`: `VARCHAR(100)` (Not Null)
  - `date_of_birth`: `DATE` (Not Null)
  - `gender`: `VARCHAR(32)` (Nullable)
  - `blood_group`: `VARCHAR(10)` (Nullable)
  - `emergency_contact_name`: `VARCHAR(100)` (Nullable)
  - `emergency_contact_phone`: `VARCHAR(32)` (Nullable)
  - `allergies`: `TEXT` (Nullable)
  - `medical_notes`: `TEXT` (Nullable)
  - `consent_given_at`: `TIMESTAMP WITH TIME ZONE` (Nullable, captures explicit informed consent)

#### 3. `Doctors` Table (Practitioner Domain Profile)
- **Purpose:** Stores professional qualifications, medical credentials, specialties, and fee structures.
- **Attributes:**
  - `id`: `UUID` (Primary Key)
  - `user_id`: `UUID` (Foreign Key -> `users.id`, Unique, On Delete Cascade, Not Null)
  - `first_name`: `VARCHAR(100)` (Not Null)
  - `last_name`: `VARCHAR(100)` (Not Null)
  - `license_number`: `VARCHAR(100)` (Unique, Not Null)
  - `specialty`: `VARCHAR(100)` (Indexed, Not Null - e.g., "Cardiology", "General Medicine")
  - `qualifications`: `VARCHAR(255)` (Not Null - e.g., "MD, FACC")
  - `experience_years`: `INTEGER` (Default `0`)
  - `bio`: `TEXT` (Nullable)
  - `consultation_fee`: `NUMERIC(10, 2)` (Not Null, Default `0.00`)
  - `clinic_address`: `TEXT` (Nullable)
  - `is_accepting_patients`: `BOOLEAN` (Default `True`)

#### 4. `Doctor_Schedules` Table (Recurring Template Schedules)
- **Purpose:** Represents the doctor's recurring weekly working hours and default slot durations.
- **Attributes:**
  - `id`: `UUID` (Primary Key)
  - `doctor_id`: `UUID` (Foreign Key -> `doctors.id`, On Delete Cascade, Not Null)
  - `day_of_week`: `SMALLINT` (Not Null, `0` = Monday through `6` = Sunday)
  - `start_time`: `TIME` (Not Null - e.g., `09:00:00`)
  - `end_time`: `TIME` (Not Null - e.g., `17:00:00`)
  - `slot_duration_minutes`: `INTEGER` (Not Null, Default `30`)
  - `is_active`: `BOOLEAN` (Default `True`)

#### 5. `Availability` Table (Discrete Daily Booking Slots & Overrides)
- **Purpose:** Stores instantiated calendar slots for specific dates and doctor schedule overrides (vacations, leaves).
- **Attributes:**
  - `id`: `UUID` (Primary Key)
  - `doctor_id`: `UUID` (Foreign Key -> `doctors.id`, On Delete Cascade, Not Null)
  - `slot_date`: `DATE` (Indexed, Not Null)
  - `start_time`: `TIME` (Not Null)
  - `end_time`: `TIME` (Not Null)
  - `status`: `ENUM('AVAILABLE', 'BOOKED', 'BLOCKED')` (Not Null, Default `'AVAILABLE'`)
  - `created_at`: `TIMESTAMP WITH TIME ZONE` (Default `NOW()`)

#### 6. `Appointments` Table (Booked Consultations)
- **Purpose:** Represents a confirmed or historical appointment binding a patient, doctor, and slot.
- **Attributes:**
  - `id`: `UUID` (Primary Key)
  - `appointment_reference`: `VARCHAR(32)` (Unique, Indexed, Not Null - e.g., "MED-20261105-X92")
  - `patient_id`: `UUID` (Foreign Key -> `patients.id`, On Delete Restrict, Not Null)
  - `doctor_id`: `UUID` (Foreign Key -> `doctors.id`, On Delete Restrict, Not Null)
  - `availability_id`: `UUID` (Foreign Key -> `availability.id`, Unique, Nullable)
  - `appointment_datetime`: `TIMESTAMP WITH TIME ZONE` (Indexed, Not Null)
  - `end_datetime`: `TIMESTAMP WITH TIME ZONE` (Not Null)
  - `status`: `ENUM('SCHEDULED', 'COMPLETED', 'CANCELLED_PATIENT', 'CANCELLED_DOCTOR', 'RESCHEDULED')` (Default `'SCHEDULED'`)
  - `chief_complaint`: `TEXT` (Patient-reported issue)
  - `triage_summary`: `TEXT` (AI-assisted summary notes, if consented)
  - `cancellation_reason`: `TEXT` (Nullable)
  - `created_at`: `TIMESTAMP WITH TIME ZONE` (Default `NOW()`)
  - `updated_at`: `TIMESTAMP WITH TIME ZONE` (Default `NOW()`)

### 8.2 Entity Relationships & Integrity Rules
1. **Users to Patients / Doctors (1-to-0..1):** A base User account maps strictly to at most one domain profile based on the `role` enum. This avoids mixing authentication logic with medical or professional data.
2. **Doctors to Doctor_Schedules (1-to-Many):** A doctor establishes weekly standard working intervals.
3. **Doctors to Availability (1-to-Many):** Standard schedules generate concrete daily availability slots for booking.
4. **Availability to Appointments (1-to-0..1):** Each available slot can be reserved by at most one appointment. Enforced via a `UNIQUE` constraint on `appointments.availability_id` combined with row-level database locking during booking transactions to completely prevent double-booking.
5. **Patients and Doctors to Appointments (1-to-Many):** Patients and doctors can independently query their complete appointment history.

---

## 9. API Architecture & Communication Strategy

To ensure architectural clarity, reliable scalability, and minimal client-server complexity, the system standardizes on **REST APIs** for all core operations and **Server-Sent Events (SSE)** for streaming AI responses.

### 9.1 RESTful APIs for Standard Operations
All core data operations use standard HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) with JSON payloads, stateless JWT bearer authorization, and standard HTTP status codes:
- **Authentication Endpoints:**
  - `POST /api/v1/auth/register` (Register new user with role)
  - `POST /api/v1/auth/login` (Authenticate and obtain JWT)
  - `GET /api/v1/auth/me` (Retrieve current user identity)
- **Patient Profile Endpoints:**
  - `GET /api/v1/patients/profile` (Retrieve patient profile)
  - `PUT /api/v1/patients/profile` (Update demographic & emergency info)
  - `POST /api/v1/patients/consent` (Record explicit informed consent)
- **Doctor & Directory Endpoints:**
  - `GET /api/v1/doctors` (Search/filter doctors by specialty, date, fee)
  - `GET /api/v1/doctors/{id}` (Retrieve doctor profile and public bio)
  - `GET /api/v1/doctors/{id}/availability` (Fetch available slots for given date range)
- **Doctor Schedule Management (Doctor/Admin only):**
  - `GET /api/v1/doctors/{id}/schedules` (Get recurring schedule templates)
  - `POST /api/v1/doctors/{id}/schedules` (Define/update schedule templates)
  - `POST /api/v1/doctors/{id}/availability/block` (Block personal time/leaves)
- **Appointment Management Endpoints:**
  - `POST /api/v1/appointments` (Reserve slot and book appointment)
  - `GET /api/v1/appointments` (List user appointments with status filters)
  - `GET /api/v1/appointments/{id}` (Get appointment details)
  - `PATCH /api/v1/appointments/{id}/reschedule` (Move appointment to new slot)
  - `PATCH /api/v1/appointments/{id}/cancel` (Cancel scheduled appointment)

### 9.2 Server-Sent Events (SSE) for AI Conversational Streaming
- **Endpoint:** `POST /api/v1/assistant/chat/stream`
- **Protocol:** Server-Sent Events (`text/event-stream` over standard HTTP/2).
- **Mechanism:**
  - Client submits the conversational message and current dialogue context.
  - The backend executes pre-LLM red-flag safety checks synchronously.
  - If safe, the backend initiates a streaming completion with Google Gemini API.
  - Generated response tokens are streamed incrementally to the browser via SSE events (`event: token`, `data: {"text": "..."}`).
  - When the response concludes, a final event (`event: done`, `data: {"specialty_recommendation": "Cardiology"}`) delivers structured actions.
- **Client Processing:** The React frontend consumes the stream via native `fetch` / `ReadableStream` or `EventSource`, progressively displaying text and queueing sentences to the `SpeechSynthesis` API for real-time vocalization.

### 9.3 Exclusion of WebSockets
- **Decision:** WebSockets are explicitly **not** utilized for Medicall.
- **Rationale:**
  - Medicall's communication requirements are either request-response (CRUD operations) or unidirectional server-to-client streaming (AI conversational responses).
  - WebSockets introduce persistent stateful TCP connections, difficult auto-scaling, complex sticky-session load balancing, firewall blocking risks, and manual reconnection handshakes.
  - SSE provides native HTTP streaming, automatic client reconnection, full compatibility with HTTP/2 multiplexing, and seamless integration with standard REST authorization headers without additional infrastructure overhead.

---

## 10. Performance & Latency Targets

All latency targets defined below are **proposed engineering benchmarks (Service Level Objectives - SLOs)** to be validated under defined testing profiles.

### 10.1 Defined Testing Conditions & Environment
- **Client Testing Profile:** Modern Chromium browser (Chrome 120+) executing on mid-range hardware (e.g., 4-core CPU, 8GB RAM). Network emulation: Standard 4G (15 Mbps download, 5 Mbps upload, 50ms round-trip latency) and Broadband (100 Mbps, 15ms RTT).
- **Server Benchmark Environment:** Containerized FastAPI backend running under Uvicorn (2 vCPU, 4GB RAM) with connection-pooled async SQLAlchemy connected to PostgreSQL 15 on the same regional network (< 5ms DB ping).
- **Concurrency Load:** 50 concurrent active users performing mixed voice interactions, searches, and booking transactions. Benchmarks measured at **p95** and **p99** percentiles.

### 10.2 Proposed Latency SLOs

| Stage | Benchmark Metric | Proposed Target (p95) | Notes / Boundary |
| :--- | :--- | :--- | :--- |
| **Client Mic Activation** | UI response to microphone toggle | **< 100 ms** | Browser Web Speech API local hardware capture |
| **Client Speech-to-Text** | Voice-to-text final transcription | **< 300 ms** | Browser local speech recognition engine post-utterance |
| **Deterministic Red-Flag Check**| Pre-LLM safety filter evaluation | **< 20 ms** | Local regex & keyword dictionary check (backend) |
| **Backend REST Endpoints** | Standard CRUD (Auth, Doctors, Booking) | **< 150 ms** | Backend processing + PostgreSQL query time |
| **Gemini AI Time-to-First-Token**| First token emitted over SSE stream | **< 1,200 ms** | Dependent on Google Gemini API external latency |
| **Full AI Response Completion** | Complete 150-token triage response | **< 2,800 ms** | Streamed progressively via SSE |
| **Client Text-to-Speech Start** | Vocalization starts after first sentence | **< 250 ms** | Local browser `window.speechSynthesis` queueing |

*Note: External Google Gemini API latency is governed by Google Cloud network routing and LLM inference time; backend architecture guarantees that internal overhead adds less than 50ms to the external API response.*

---

## 11. Privacy, Data Protection & Security

Healthcare-adjacent applications demand rigorous data protection, clear patient consent, and strong isolation boundaries.

### 11.1 Informed Patient Consent
- **Pre-Interaction Agreement:** Prior to granting microphone permissions or initiating an AI consultation, patients must review and explicitly accept the *Medicall Privacy and Clinical Scope Disclosure*.
- **Captured Metadata:** Consent acceptance is permanently timestamped (`consent_given_at` in `Patients` table).
- **Right to Revoke & Erase:** Patients maintain the right to revoke consent and request deletion of their profile and consultation history (supporting GDPR/HIPAA privacy principles).

### 11.2 Conversation Data Retention & Purging
- **Zero Raw Audio Storage:** User voice streams are processed locally in the browser by the Web Speech API into text. No raw audio files (`.wav`, `.mp3`) are recorded, transmitted, or stored on the backend.
- **Configurable Retention Window:** Text transcripts and triage summaries are retained for a configurable retention window (default: 30 days) solely to assist doctor consultation context.
- **Automated Data Purging:** A scheduled backend maintenance task automatically scrubs or anonymizes consultation transcripts older than the retention threshold.

### 11.3 Secure Transcript Handling & Encryption
- **Encryption in Transit:** All traffic is strictly enforced over TLS 1.3 with HSTS headers.
- **Encryption at Rest:** PostgreSQL database volumes must utilize AES-256 block-level encryption. Sensitive medical notes and chief complaints utilize database column encryption or application-level cryptographic envelopes.
- **Access Audit Logs:** Every query or retrieval of patient medical records or triage notes produces an immutable access log (`user_id`, `patient_id`, `timestamp`, `action`).

### 11.4 Role-Based Access Control (RBAC) & Patient Data Isolation
- **Role Scoping:**
  - `PATIENT`: Can read and update only their own profile, appointments, and conversation sessions.
  - `DOCTOR`: Can view only their own schedules, availability, and appointments booked with their doctor profile. Access to patient profiles is restricted strictly to patients who possess an active or historical appointment with that specific doctor.
  - `ADMIN`: Platform operations, doctor verification, and system telemetry; strictly prohibited from viewing patient medical notes without elevated, auditable emergency access.
- **Tenant Isolation Enforcement:** Every patient-facing backend database query explicitly binds the authenticated user ID (`WHERE patients.user_id = :current_user_id`), eliminating Insecure Direct Object Reference (IDOR) vulnerabilities.

---

## 12. Functional Requirements (FR)

### 12.1 Voice Interaction & Audio Processing
- **FR-1.1 (Voice Input):** Capture user voice in real-time using browser-native Web Speech API (`SpeechRecognition`).
- **FR-1.2 (Transcription Display):** Real-time text display in chat interface with visual microphone listening animations.
- **FR-1.3 (Voice Output):** Vocalize assistant responses using native `window.speechSynthesis` with speech rate and pitch settings.
- **FR-1.4 (Graceful Fallback):** Seamless text input alternative for unsupported browsers or noisy environments.

### 12.2 AI Health Assistance & Safety Safeguards
- **FR-2.1 (Multi-Turn Triage):** Conduct contextual multi-turn conversations regarding symptoms using Google Gemini API.
- **FR-2.2 (Deterministic Interceptor):** Intercept life-threatening red-flag symptoms client-side and backend prior to LLM processing.
- **FR-2.3 (Localized Emergency Routing):** Present dynamic click-to-call emergency hotlines matching configured deployment country.
- **FR-2.4 (Specialty Recommendation):** Identify appropriate clinical specialties based on symptom classification.
- **FR-2.5 (Persistent Disclaimers):** Mandate visible medical disclaimers on every interaction and response.

### 12.3 Doctor & Schedule Management
- **FR-3.1 (Doctor Profiles):** Manage credentials, specialty, consultation fee, bio, and clinic location.
- **FR-3.2 (Recurring Schedules):** Doctors can configure weekly recurring availability templates with custom slot durations.
- **FR-3.3 (Slot Availability):** Generate daily available slots while honoring doctor blackout dates and existing bookings.
- **FR-3.4 (Concurrency Protection):** Database-level transaction locking to guarantee zero double-booking under concurrent booking attempts.

### 12.4 Appointment Lifecycle
- **FR-4.1 (Voice & UI Booking):** Reserve available consultation slots via conversational assistant or interactive calendar UI.
- **FR-4.2 (Unique Reference):** Generate distinct, human-readable appointment reference codes upon booking.
- **FR-4.3 (Cancellation & Rescheduling):** Allow patients and doctors to reschedule or cancel appointments in accordance with configured cutoff policies.

### 12.5 Identity, Consent & Security
- **FR-5.1 (JWT Authentication):** Secure registration and login issuing signed JSON Web Tokens.
- **FR-5.2 (Role Profiles):** Enforce 1-to-1 separation between base `Users` and `Patients` or `Doctors`.
- **FR-5.3 (Consent Capture):** Mandatory consent modal recording timestamp prior to assistant usage.
- **FR-5.4 (Data Isolation):** Scoped database queries preventing cross-patient data exposure.

---

## 13. Non-Functional Requirements (NFR)

### 13.1 Architectural Decoupling
- **NFR-1.1 (Independent Codebases):** Completely segregated `/frontend` (React + Vite) and `/backend` (FastAPI) applications with isolated dependencies and runtime environments.
- **NFR-1.2 (Standardized Interfaces):** Inter-application communication strictly over HTTP REST endpoints and Server-Sent Events (SSE).

### 13.2 Reliability & Availability
- **NFR-2.1 (Resilient Safety):** Deterministic red-flag safety features must function even if the external Gemini API experiences downtime.
- **NFR-2.2 (Database Concurrency):** PostgreSQL isolation level `SERIALIZABLE` or `SELECT FOR UPDATE` locking during booking transactions.

### 13.3 Usability & Accessibility
- **NFR-3.1 (WCAG AA Compliance):** High-contrast color palettes, accessible form inputs, ARIA voice state labels, and full keyboard navigation.
- **NFR-3.2 (Responsive Design):** Fluid user interface supporting mobile, tablet, and desktop viewports.

---

## 14. Target Directory Structure (Monorepo Blueprint)

The directory layout aligns with the decoupled architecture, database models, and API routers:

```
medicall/
├── docs/
│   └── requirements.md               # System requirements and specifications (this document)
├── frontend/                         # Standalone React.js + Vite Application
│   ├── public/                       # Static public assets
│   ├── src/
│   │   ├── assets/                   # SVG icons and visual assets
│   │   ├── components/               # Reusable UI components
│   │   │   ├── common/               # Button, Modal, Disclaimer, EmergencyBanner
│   │   │   ├── voice/                # VoiceMicButton, WaveformVisualizer, SpeechControls
│   │   │   ├── appointments/         # SlotPicker, AppointmentCard, BookingModal
│   │   │   └── doctor/               # DoctorCard, SpecialtyFilter
│   │   ├── context/                  # React Contexts (AuthContext, VoiceContext)
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useSpeechToText.js    # Web Speech API wrapper
│   │   │   ├── useSpeechSynthesis.js # Speech Synthesis API wrapper
│   │   │   └── useSSEChat.js         # Server-Sent Events assistant stream reader
│   │   ├── pages/                    # Application pages
│   │   │   ├── HomePage.jsx          # Landing and entry
│   │   │   ├── AssistantPage.jsx     # Voice & text health assistant interface
│   │   │   ├── DoctorsPage.jsx       # Doctor directory and search
│   │   │   ├── AppointmentsPage.jsx  # Patient appointment list and management
│   │   │   ├── DoctorDashboard.jsx   # Doctor schedule and queue management
│   │   │   └── LoginPage.jsx         # Authentication portal
│   │   ├── services/                 # Axios / Fetch HTTP API client services
│   │   ├── App.jsx                   # Root application router and layout
│   │   └── main.jsx                  # React application entry point
│   ├── package.json                  # Frontend dependencies and npm scripts
│   ├── vite.config.js                # Vite build configuration
│   └── README.md
├── backend/                          # Standalone Python + FastAPI Application
│   ├── app/
│   │   ├── api/                      # API Routers
│   │   │   ├── v1/
│   │   │   │   ├── auth.py           # Login, registration, token refresh
│   │   │   │   ├── users.py          # User management
│   │   │   │   ├── patients.py       # Patient profile and consent endpoints
│   │   │   │   ├── doctors.py        # Doctor directory and schedule endpoints
│   │   │   │   ├── appointments.py   # Booking and appointment lifecycle
│   │   │   │   ├── assistant.py      # AI assistant chat & SSE streaming router
│   │   │   │   └── router.py         # Aggregated v1 router
│   │   ├── core/                     # Application configurations
│   │   │   ├── config.py             # Pydantic Settings (DB URLs, Gemini Key, Emergency No)
│   │   │   ├── security.py           # Password hashing and JWT generation/validation
│   │   │   └── safety.py             # Deterministic red-flag keyword dictionaries & rules
│   │   ├── db/                       # Database setup
│   │   │   ├── base.py               # Base declarative model class
│   │   │   └── session.py            # Async SQLAlchemy engine and sessionmaker
│   │   ├── models/                   # SQLAlchemy ORM Models
│   │   │   ├── user.py               # Users table
│   │   │   ├── patient.py            # Patients table
│   │   │   ├── doctor.py             # Doctors table
│   │   │   ├── schedule.py           # Doctor_Schedules table
│   │   │   ├── availability.py       # Availability table
│   │   │   └── appointment.py        # Appointments table
│   │   ├── schemas/                  # Pydantic validation schemas
│   │   │   ├── user.py
│   │   │   ├── patient.py
│   │   │   ├── doctor.py
│   │   │   ├── schedule.py
│   │   │   ├── appointment.py
│   │   │   └── assistant.py
│   │   ├── services/                 # Core business logic
│   │   │   ├── appointment_service.py# Booking logic and slot collision prevention
│   │   │   ├── gemini_service.py     # Google Gemini API client and prompt templates
│   │   │   └── triage_service.py     # Deterministic safety triage coordinator
│   │   └── main.py                   # FastAPI application initialization & CORS
│   ├── alembic/                      # Database migrations
│   ├── alembic.ini                   # Alembic migration configuration
│   ├── requirements.txt              # Backend Python dependencies
│   ├── .env.example                  # Environment variable template
│   └── README.md
└── .gitignore                        # Monorepo root gitignore
```

---

## 15. Next Steps (Pending User Approval)

1. **User Sign-Off:** Review and approval of this refined architectural and requirements specification.
2. **Environment & Git Setup:** Initialize repository configuration and `.gitignore`.
3. **Frontend Project Scaffolding:** Initialize `/frontend` using Vite + React.
4. **Backend Project Scaffolding:** Initialize `/backend` using FastAPI + async SQLAlchemy.
5. **Database Migration Baseline:** Generate Alembic models for `Users`, `Patients`, `Doctors`, `Doctor_Schedules`, `Availability`, and `Appointments`.
6. **Safety Interceptor Implementation:** Implement deterministic safety rules in backend `core/safety.py` and frontend pre-checks.
7. **Assistant & Voice Integration:** Connect Web Speech API hooks and SSE Gemini streaming services.
