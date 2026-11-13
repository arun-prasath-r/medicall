# Medicall - Engineering Development Roadmap

**Project Name:** Medicall  
**Document Version:** 1.0.0  
**Status:** Implementation Roadmap & Milestone Plan  
**Target Architecture:** Monorepo (Independent `/frontend` & `/backend`)  
**Last Updated:** November 2026  

---

## 1. Roadmap Overview & Phasing Strategy

The development of Medicall is structured into eight sequential phases. Each phase builds on strictly tested foundations: from core repository scaffolding and relational persistence, through backend API services and frontend interfaces, to client voice processing, AI triage integration, and end-to-end deployment.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Project Setup & Monorepo Architecture                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 2: Relational Database Modeling & Alembic Migrations             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 3: Backend REST API & Authentication Services                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 4: Frontend UI Scaffold & Component Library                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 5: Web Speech API - Speech-to-Text (STT) Integration             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 6: Google Gemini AI Triage & SSE Streaming                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 7: Web Speech API - Text-to-Speech (TTS) Integration             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 8: Complete Integration, Concurrency Testing & Deployment        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase-by-Phase Milestone Breakdown

### Phase 1: Project Setup and Architecture
* **Objective:** Establish the clean monorepo structure, repository hygiene, version control, and base configuration templates.
* **Dependencies:** None.
* **Tasks & Subtasks:**
  1. *Monorepo Scaffolding:*
     - Create `/frontend` and `/backend` top-level directories.
     - Establish root `.gitignore` covering Python bytecode, `.env`, Node modules, and build outputs.
  2. *Backend Tooling Setup:*
     - Initialize Python 3.11 virtual environment (`venv`).
     - Configure `backend/requirements.txt` with initial pins (`fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`).
     - Set up `backend/.env.example` with template keys.
  3. *Frontend Tooling Setup:*
     - Initialize React 18 SPA using `vite` (`npm create vite@latest frontend -- --template react`).
     - Configure base Tailwind CSS and asset directories.
* **Expected Deliverables:** Clean monorepo directory layout, functional local dev servers for both apps.
* **Completion Criteria:** Backend starts on `http://localhost:8000/docs` with empty OpenAPI schema; frontend loads Vite welcome page on `http://localhost:5173`.

---

### Phase 2: Database Development
* **Objective:** Implement declarative SQLAlchemy models, establish PostgreSQL connectivity, and configure versioned Alembic migrations.
* **Dependencies:** Phase 1 complete, local PostgreSQL 15+ instance running.
* **Tasks & Subtasks:**
  1. *Database Engine & Connection Pool:*
     - Create `backend/app/db/base.py` and `backend/app/db/session.py` with async SQLAlchemy engine.
  2. *Declarative Model Implementation:*
     - Implement `User` model (`backend/app/models/user.py`).
     - Implement `Patient` model (`backend/app/models/patient.py`).
     - Implement `Doctor` model (`backend/app/models/doctor.py`).
     - Implement `DoctorSchedule` model (`backend/app/models/schedule.py`).
     - Implement `Availability` model (`backend/app/models/availability.py`).
     - Implement `Appointment` model (`backend/app/models/appointment.py`).
  3. *Alembic Migrations:*
     - Initialize Alembic (`alembic init alembic`).
     - Configure `env.py` to import declarative base metadata.
     - Generate and apply initial baseline migration (`001_initial_schema.py`).
  4. *Database Seed Script:*
     - Create `backend/app/db/seed.py` to populate initial specialties and verified mock doctors.
* **Expected Deliverables:** Executable migration scripts, seeded PostgreSQL schema matching `database-schema.md`.
* **Completion Criteria:** Alembic executes `upgrade head` without warnings; all tables, foreign keys, unique constraints, and enums verified in PostgreSQL.

---

### Phase 3: Backend Development
* **Objective:** Implement the core REST API layer, authentication middleware, and appointment scheduling logic.
* **Dependencies:** Phase 2 complete.
* **Tasks & Subtasks:**
  1. *Authentication & Security Core:*
     - Implement password hashing (bcrypt) and JWT encode/decode in `core/security.py`.
     - Implement JWT dependency middleware for role verification (`PATIENT`, `DOCTOR`, `ADMIN`).
     - Implement `/api/v1/auth/register`, `/login`, and `/me`.
  2. *Patient & Doctor Management:*
     - Implement patient profile retrieval and update endpoints (`/api/v1/patients/profile`).
     - Implement patient consent recording endpoint (`/api/v1/patients/consent`).
     - Implement doctor directory search and filtering endpoints (`/api/v1/doctors`).
  3. *Schedule & Availability Engine:*
     - Implement doctor recurring schedule configuration endpoints.
     - Implement dynamic availability slot retrieval with date filters.
  4. *Appointment Lifecycle & Concurrency Control:*
     - Implement booking endpoint `POST /api/v1/appointments` with `SELECT FOR UPDATE` slot locking.
     - Implement rescheduling and cancellation endpoints (`PATCH /appointments/{id}/cancel`).
  5. *Deterministic Emergency Triage Filter:*
     - Implement keyword/regex red-flag matcher in `backend/app/core/safety.py`.
* **Expected Deliverables:** Complete RESTful API endpoints covered by automated Pytest suites.
* **Completion Criteria:** All API endpoints documented in Swagger UI; zero unhandled 500 errors; concurrent booking test passes with `409 Conflict` on race conditions.

---

### Phase 4: Frontend Development
* **Objective:** Build the reactive Single Page Application, routing structure, component library, and state management.
* **Dependencies:** Phase 3 complete (or running with mock data).
* **Tasks & Subtasks:**
  1. *Application Layout & Navigation:*
     - Implement React Router DOM layout with header, navigation, and persistent medical disclaimer footer.
  2. *Authentication & Protected Routes:*
     - Implement `AuthContext` to store JWT tokens and user profile state.
     - Implement `LoginPage` and registration modals.
  3. *Doctor Directory & Booking UI:*
     - Implement `DoctorsPage` with specialty filter dropdowns.
     - Implement `SlotPicker` component displaying open calendar slots.
     - Implement `BookingModal` with chief complaint input.
  4. *Patient Appointments Portal:*
     - Implement `AppointmentsPage` displaying scheduled and historical appointments with cancellation buttons.
* **Expected Deliverables:** Responsive, accessible React UI connecting to backend REST endpoints.
* **Completion Criteria:** Patients can log in, browse doctors, view slots, and submit booking requests visually.

---

### Phase 5: Speech Recognition (STT) Integration
* **Objective:** Implement client-side voice capture using the browser's native Web Speech API.
* **Dependencies:** Phase 4 complete.
* **Tasks & Subtasks:**
  1. *Custom Hook Implementation:*
     - Build `useSpeechToText.js` encapsulating `window.SpeechRecognition`.
     - Support continuous transcription with interim results.
  2. *Voice UI Components:*
     - Build `VoiceMicButton` with pulsing animations during active listening.
     - Build live transcription preview card displaying real-time speech.
  3. *Microphone Permission & Graceful Degradation:*
     - Implement browser support checks (detecting non-Chromium browsers).
     - Provide automatic fallback to keyboard input when microphone is denied or unavailable.
  4. *Client-Side Emergency Pre-Filter:*
     - Implement instant client-side keyword check triggering immediate visual emergency alerts.
* **Expected Deliverables:** Voice-enabled input interface in `AssistantPage.jsx`.
* **Completion Criteria:** Spoken patient symptoms are transcribed into the chat box in real-time with zero backend audio transmission.

---

### Phase 6: Google Gemini AI Integration
* **Objective:** Connect FastAPI backend to Google Gemini API, configure clinical guardrails, and stream responses via Server-Sent Events.
* **Dependencies:** Phase 3 (Backend) & Phase 5 (STT) complete.
* **Tasks & Subtasks:**
  1. *Google GenAI Service Setup:*
     - Implement `backend/app/services/gemini_service.py` using official Google GenAI SDK.
     - Configure `GEMINI_MODEL` and clinical system prompts.
  2. *Function / Tool Calling:*
     - Define `get_available_slots` and `search_doctors` tool declarations.
     - Implement backend tool execution routing queries to PostgreSQL.
  3. *Server-Sent Events (SSE) Endpoint:*
     - Implement `POST /api/v1/assistant/chat/stream` returning `text/event-stream`.
  4. *Frontend SSE Consumer:*
     - Build `useSSEChat.js` hook in React to read token chunks via `fetch` ReadableStream.
* **Expected Deliverables:** Conversational assistant capable of symptom triage, specialty recommendations, and interactive slot presentation.
* **Completion Criteria:** Assistant receives user text/voice, correctly calls doctor availability tools when appropriate, and streams responses with Time-to-First-Token `< 1.2s`.

---

### Phase 7: Text-to-Speech (TTS) Integration
* **Objective:** Voice-enable assistant responses using the browser-native Speech Synthesis API.
* **Dependencies:** Phase 6 complete.
* **Tasks & Subtasks:**
  1. *Custom Hook Implementation:*
     - Build `useSpeechSynthesis.js` wrapping `window.speechSynthesis`.
     - Support sentence-level audio queueing as SSE tokens arrive.
  2. *Voice Quality & Clinical Controls:*
     - Configure natural English voice selection.
     - Implement user audio controls: Mute, Pause, Play, and Speech Speed toggle (0.8x, 1.0x, 1.2x).
  3. *Audio Triage Safety:*
     - Ensure emergency alerts are vocalized with urgent, clear phrasing.
* **Expected Deliverables:** Fully hands-free voice conversational loop in the React assistant view.
* **Completion Criteria:** AI assistant responses are spoken back naturally through client speakers with synchronized text display.

---

### Phase 8: Complete Integration, Concurrency Testing & Deployment
* **Objective:** Conduct end-to-end quality assurance, load and concurrency verification, and deploy the application.
* **Dependencies:** Phases 1 through 7 complete.
* **Tasks & Subtasks:**
  1. *Concurrency & Race Condition Validation:*
     - Execute automated concurrent booking test scripts simulating 50 simultaneous users.
     - Confirm zero duplicate bookings occur.
  2. *End-to-End Test Suite:*
     - Implement Playwright regression tests covering full voice-to-booking journeys.
  3. *Deployment Architecture Execution:*
     - Configure production environment variables and HTTPS certificates.
     - Containerize backend via Docker and deploy frontend to static host/CDN.
  4. *Final Documentation & User Manual:*
     - Review all documentation files for complete fidelity with production code.
* **Expected Deliverables:** Production-ready Medicall application with verified test reports.
* **Completion Criteria:** All unit, integration, and E2E tests pass; application is deployed and accessible over HTTPS.

