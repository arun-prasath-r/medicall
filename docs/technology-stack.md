# Medicall - Technology Stack Specification

**Project Name:** Medicall  
**Document Version:** 1.0.0  
**Status:** Architecture & Specifications  
**Last Updated:** November 2026  

---

## 1. Overview & Stack Matrix

Medicall employs a decoupled, modern web architecture organized as a monorepo containing two distinct applications: a client-side Single Page Application (SPA) and an asynchronous RESTful API backend service. The technology choices prioritize developer productivity, low latency, real-time voice responsiveness, strong relational data guarantees, and clinical safety.

### 1.1 Complete Technology Summary

| Architecture Layer | Technology | Version | Primary Purpose | Selection Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Framework** | React.js | `^18.3.0` | Reactive component-based user interface | Vast ecosystem, declarative UI state handling, high performance with Virtual DOM. |
| **Frontend Build Tool** | Vite | `^5.4.0` | Frontend bundler & dev server | Ultra-fast Hot Module Replacement (HMR), optimized Rollup production builds. |
| **Language (Frontend)** | JavaScript (ES2023) | ES Modules | Client-side application logic | Universal browser support, native Web Speech API compatibility. |
| **Styling** | Modern CSS3 & Tailwind CSS | `^3.4.0` | Responsive, accessible styling | Utility-first architecture, responsive breakpoints, high-contrast healthcare accessibility. |
| **Backend Framework** | FastAPI | `^0.115.0` | Asynchronous RESTful API framework | High performance (Starlette/Uvicorn), native async/await, automated OpenAPI documentation. |
| **Backend Runtime** | Python | `>=3.11.0` | Server runtime environment | Mature healthcare/AI libraries, modern type hinting, exception handling performance improvements. |
| **ASGI Web Server** | Uvicorn | `^0.30.0` | High-concurrency ASGI server | Lightning-fast async request execution based on `uvloop` and `httptools`. |
| **Data Validation** | Pydantic | `^2.8.0` | Request/response schema validation | Rust-backed performance, strict typing, auto-generated OpenAPI schemas. |
| **Database** | PostgreSQL | `>=15.0` | Relational data persistence | ACID compliance, robust transaction isolation, row-level locking for concurrent booking safety. |
| **ORM** | SQLAlchemy | `^2.0.30` | Data modeling & query abstraction | Full async support (`asyncpg`), unit-of-work pattern, enterprise-grade schema mapping. |
| **Schema Migrations** | Alembic | `^1.13.0` | Database schema version control | Deterministic migration history, seamless autogeneration from SQLAlchemy models. |
| **AI Engine** | Google Gemini API | Configurable | Conversational triage & function calling | Multimodal reasoning, structured JSON tool calling, configurable models via environment variables. |
| **Speech-to-Text (STT)**| Web Speech API | Browser Native | Real-time speech transcription | Client-side processing, zero audio transmission overhead, zero external transcription billing. |
| **Text-to-Speech (TTS)**| Speech Synthesis API | Browser Native | Natural voice audio feedback | Native client synthesis, zero network latency, adjustable pitch and speed controls. |
| **Streaming Protocol** | Server-Sent Events (SSE)| HTTP/2 | Token-by-token AI response streaming | Simpler than WebSockets, unidirectional server-to-client streaming, automatic reconnects. |
| **Authentication** | JWT (PyJWT / python-jose)| `^2.9.0` | Stateless token authorization | Industry-standard role claims (`PATIENT`, `DOCTOR`, `ADMIN`), low validation overhead. |
| **Password Security** | Passlib / bcrypt | `^4.0.1` | Cryptographic password hashing | Salted slow hashing to protect against brute-force credential stuffing. |

---

## 2. Frontend Technology Stack (`/frontend`)

### 2.1 React.js (v18+)
- **Purpose:** Powers the interactive user interface, managing state for the conversational voice interface, interactive calendar slot pickers, triage notifications, and authentication portals.
- **Selection Justification:**
  - Robust state and effect primitives (`useState`, `useEffect`, `useReducer`, `useRef`) allow seamless management of browser audio streams, mic capture sessions, and dynamic UI transitions.
  - Component reusability enables unified design components (e.g., `EmergencyModal`, `SlotPicker`, `VoiceVisualizer`).
- **Integration Points:**
  - Directly interfaces with native browser APIs (`window.SpeechRecognition`, `window.speechSynthesis`).
  - Communicates with the FastAPI backend over HTTP via Axios/Fetch API.
  - Consumes AI conversational streams using `fetch` with `ReadableStream` (SSE reader).

### 2.2 Vite Build Tooling
- **Purpose:** Development server and production bundling pipeline.
- **Selection Justification:**
  - Sub-millisecond dev server start time via native ES modules.
  - Fast Hot Module Replacement (HMR) allows rapid iteration on voice UI and conversational testing.
  - Highly optimized production bundle output utilizing Rollup with code splitting.
- **Dependencies:** `@vitejs/plugin-react`.

### 2.3 Web Speech API (Client-Side Voice Stack)
- **Speech-to-Text (`SpeechRecognition` / `webkitSpeechRecognition`):**
  - Converts spoken patient symptoms into real-time text in the browser.
  - Configured for continuous recognition with interim results enabled (`interimResults = true`), giving immediate feedback as the patient speaks.
- **Text-to-Speech (`SpeechSynthesis` & `SpeechSynthesisUtterance`):**
  - Converts AI assistant guidance and confirmation prompts into spoken audio.
  - Allows configurable voice selection, volume, rate (0.9x-1.0x recommended for clinical clarity), and pitch.
- **Selection Justification:**
  - **Zero Server Audio Load:** Audio waveforms never leave the browser; only transcribed text is transmitted over the wire, drastically minimizing backend bandwidth and latency.
  - **Cost & Simplicity:** Eliminates third-party paid STT/TTS API quotas (e.g., Whisper, ElevenLabs), making it ideal for self-contained, high-performance academic/student deployments.
  - **Privacy:** Avoids storing raw patient voice biometrics on remote servers.

---

## 3. Backend Technology Stack (`/backend`)

### 3.1 Python 3.11+ & FastAPI
- **Purpose:** Primary application backend serving RESTful API routes, deterministic medical safety filters, Google Gemini AI orchestration, and database operations.
- **Selection Justification:**
  - **Asynchronous Execution:** FastAPI leverages Python's native `asyncio` event loop to handle concurrent I/O operations (PostgreSQL database queries and external Gemini API HTTP requests) without thread starvation.
  - **Schema Enforcement:** Tight integration with Pydantic ensures all input data (e.g., patient phone numbers, appointment timestamps) is strictly parsed and sanitized before reaching the database.
  - **Auto-Generated Documentation:** Automatically exposes interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) based on the OpenAPI 3.1 standard.

### 3.2 Uvicorn ASGI Server
- **Purpose:** Serves the asynchronous FastAPI application over HTTP/1.1 and HTTP/2.
- **Selection Justification:** Built on `uvloop` (a Cython-based drop-in replacement for the standard asyncio event loop) and `httptools`, offering near-C-level HTTP throughput.

### 3.3 SQLAlchemy 2.0 (Async Engine)
- **Purpose:** Relational database object-relational mapping, statement generation, transaction management, and connection pooling.
- **Selection Justification:**
  - Version 2.0 provides native `asyncio` syntax (`async with session.begin():`) with strict typing.
  - Enables granular transaction management required for concurrency safety, specifically `select(...).with_for_update()` to eliminate double-booking race conditions.
- **Driver:** `asyncpg` (ultra-high-performance asynchronous PostgreSQL driver).

### 3.4 Alembic (Database Migrations)
- **Purpose:** Manages schema evolution and reproducible database versions.
- **Selection Justification:** Integrates natively with SQLAlchemy declarative metadata, enabling automated drift detection (`alembic revision --autogenerate`) and deterministic rollout/rollback scripts.

---

## 4. Database Technology Stack

### 4.1 PostgreSQL 15+
- **Purpose:** Central relational datastore for all persistent application data (accounts, patient profiles, doctor directories, schedules, availability slots, and appointment bookings).
- **Selection Justification:**
  - **Strict ACID Guarantees:** Financial and healthcare scheduling operations require absolute atomicity and serializability.
  - **Row-Level Locking:** Supports `SELECT FOR UPDATE` and conditional unique indices, guaranteeing that two concurrent patients cannot reserve the same doctor appointment slot.
  - **Data Integrity:** Enforces foreign key constraints, check constraints (e.g., `end_time > start_time`), and unique constraints natively at the database engine level.

---

## 5. Artificial Intelligence Stack

### 5.1 Google Gemini API
- **Purpose:** Natural language symptom interpretation, contextual conversational assistance, specialist classification, and structured function/tool calling.
- **Configuration & Selection:**
  - SDK: Official Google GenAI SDK (`google-genai` / `google-generativeai`).
  - Model selection is fully decoupled and configured via the `GEMINI_MODEL` environment variable (e.g., `gemini-1.5-flash` for low-latency conversational triage, or `gemini-1.5-pro` for complex multi-symptom analysis).
- **Strict Architecture Rule:**
  - **Zero OpenAI / ChatGPT Dependencies:** No OpenAI packages, GPT endpoints, or ChatGPT APIs are permitted in any part of the Medicall codebase.
  - **Indirect Database Access:** The Gemini model **never** directly accesses PostgreSQL. All database interactions occur through backend-orchestrated function calling (tools) exposed by FastAPI service layers.

### 5.2 Server-Sent Events (SSE) Streaming
- **Purpose:** Streaming response tokens from the backend Gemini service to the React frontend in real-time.
- **Selection Justification:**
  - Provides instant conversational feedback to the user (Time-to-First-Token `< 1.2s`).
  - Standard HTTP/2 protocol eliminates the complex connection state, sticky sessions, and handshake failures associated with WebSockets.

---

## 6. Security, Privacy & Tooling Dependencies

### 6.1 Authentication & Cryptography
- **PyJWT / python-jose:** Generates and validates cryptographically signed JSON Web Tokens (HMAC-SHA256) containing user identity and role claims (`PATIENT`, `DOCTOR`, `ADMIN`).
- **Passlib & bcrypt:** Hashes user passwords with cryptographically randomized salts before persistence.

### 6.2 Development & Operational Tooling
- **Git & GitHub:** Distributed version control, feature branch management, and pull request reviews.
- **Swagger UI:** Built-in interactive API exploration and testing tool at `/docs`.
- **Postman:** Pre-configured collections for end-to-end API regression and edge-case testing.
- **Python Virtual Environment (`venv`):** Strict backend dependency isolation.
- **Node Package Manager (`npm`):** Frontend dependency and build pipeline management.

---

## 7. Component Dependency Mapping

```
┌─────────────────────────────────────────────────────────────┐
│                       React Frontend                        │
│   (Vite + React 18 + Web Speech API + SSE Streaming Client) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                REST HTTP/2 & Server-Sent Events
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                      FastAPI Backend                        │
│ (Python 3.11 + Uvicorn + Pydantic v2 + Security/Safety Core)│
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
        SQLAlchemy 2.0                 Google GenAI SDK
        (asyncpg driver)               (REST / gRPC)
               │                               │
┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
│    PostgreSQL Database      │ │      Google Gemini API      │
│ (Users, Appointments, Slots)│ │ (Triage & Function Calling) │
└─────────────────────────────┘ └─────────────────────────────┘
```

This stack guarantees complete separation between frontend and backend, enforces enterprise-grade database integrity, avoids external audio processing costs, and ensures strict clinical safety boundaries.

