# Medicall - Architecture Decision Records (ADRs)

**Project Name:** Medicall  
**Document Version:** 1.0.0  
**Status:** Approved Architectural Baseline  
**Last Updated:** November 2026  

---

## 1. Overview of Architecture Decision Records

This document chronicles the fundamental architectural and engineering decisions governing the Medicall application. Each record outlines the technical context, evaluated alternatives, the final decision, and the architectural consequences.

---

### ADR-001: Independent Frontend and Backend in a Monorepo
* **Status:** Accepted
* **Context:** The project requires a clean boundary between user interface logic and server-side clinical business logic, while maintaining a single, unified source repository.
* **Decision:** Enforce a strict monorepo architecture containing two top-level, completely independent applications: `/frontend` (React + Vite) and `/backend` (FastAPI + SQLAlchemy).
* **Consequences:**
  - **Positive:** Independent dependency trees (`package.json` vs `requirements.txt`); separate CI/CD build pipelines; independent horizontal scaling; zero cross-contamination of client/server code.
  - **Trade-offs:** Requires running two local development servers during development; coordinated deployments when API contracts evolve.
* **Alternatives Considered:**
  - *Full-stack frameworks (Next.js / Remix):* Rejected because Python is the premier ecosystem for AI and healthcare triage logic; keeping React pure client-side simplifies native Web Speech API interactions.
  - *Multi-repo (polyrepo):* Rejected because keeping everything in one repository simplifies versioning, documentation, and student collaboration.

---

### ADR-002: Selection of React.js (Vite) and FastAPI (Python)
* **Status:** Accepted
* **Context:** The application demands an accessible, reactive client interface for voice transcription paired with a high-throughput, asynchronous server to coordinate AI streaming and database transactions.
* **Decision:** Utilize React 18 with Vite for the frontend Single Page Application, and Python 3.11 with FastAPI and Uvicorn for the backend.
* **Consequences:**
  - **Positive:** React's reactive state handles live speech transcript streaming effortlessly; FastAPI natively manages high-concurrency async I/O (Gemini API calls and PostgreSQL queries) without blocking worker threads; automated OpenAPI schema generation.
  - **Trade-offs:** Developers must be comfortable across two programming languages (JavaScript and Python).
* **Alternatives Considered:**
  - *Django / Flask:* Rejected due to inferior native async/await performance and lack of built-in Pydantic data validation compared to FastAPI.
  - *Vue / Svelte:* Rejected due to React's extensive component ecosystem and ubiquitous community support.

---

### ADR-003: Selection of PostgreSQL as Central Relational Datastore
* **Status:** Accepted
* **Context:** Healthcare appointments and doctor availability require strict relational consistency, ACID transactions, and zero tolerance for booking collisions.
* **Decision:** Adopt PostgreSQL 15+ as the primary source of truth.
* **Consequences:**
  - **Positive:** Native support for row-level locking (`SELECT ... FOR UPDATE`), check constraints, composite unique indexes, and strong transactional isolation.
  - **Trade-offs:** Requires relational schema migrations when entity models change.
* **Alternatives Considered:**
  - *MongoDB / Document DB:* Rejected because document databases lack native relational constraints across entities and risk subtle race conditions during concurrent slot reservations.
  - *SQLite:* Suitable only for localized test fixtures; rejected for production due to database-level write locking bottlenecks.

---

### ADR-004: Adoption of SQLAlchemy 2.0 with Asyncpg and Alembic
* **Status:** Accepted
* **Context:** The backend requires a type-safe, asynchronous Object-Relational Mapper (ORM) with automated schema migration management.
* **Decision:** Standardize on SQLAlchemy 2.0 using the asyncpg driver, paired with Alembic for migrations.
* **Consequences:**
  - **Positive:** Explicit transaction control; unit-of-work pattern; programmatic schema drift detection; native integration with FastAPI dependency injection.
  - **Trade-offs:** Slight learning curve for SQLAlchemy 2.0 `select()` syntax compared to legacy 1.4 query APIs.
* **Alternatives Considered:**
  - *Tortoise ORM / Peewee:* Rejected due to smaller community size and less mature migration ecosystems compared to Alembic.

---

### ADR-005: Utilization of Google Gemini API for Conversational AI
* **Status:** Accepted
* **Context:** The system requires natural language understanding, clinical symptom inquiry, and structured tool calling without relying on OpenAI APIs.
* **Decision:** Utilize Google Gemini API via the official Google GenAI SDK, with model selection decoupled through the `GEMINI_MODEL` environment variable.
* **Consequences:**
  - **Positive:** Fast Time-to-First-Token (TTFT); native structured tool calling; strict compliance with project constraints (zero OpenAI/ChatGPT dependencies); configurable model upgrades without code changes.
  - **Trade-offs:** External cloud dependency subject to network latency and quota limits.
* **Strict Rule:** No OpenAI or ChatGPT packages or endpoints are permitted in the project.

---

### ADR-006: Client-Side Web Speech API for Voice Processing (STT & TTS)
* **Status:** Accepted
* **Context:** Voice interactions must feel responsive, private, and cost-effective without adding heavy server-side processing burdens.
* **Decision:** Leverage the native W3C Web Speech API (`SpeechRecognition` for STT and `SpeechSynthesis` for TTS) directly in the client browser.
* **Consequences:**
  - **Positive:** Zero server bandwidth or cloud API billing for audio processing; zero persistent voice recordings (high privacy); sub-100ms hardware capture response.
  - **Trade-offs:** Full speech recognition accuracy is optimal on Chromium-based browsers; non-Chromium browsers require clean fallback to standard text input.
* **Alternatives Considered:**
  - *Cloud-hosted Whisper & ElevenLabs:* Rejected due to high per-minute API costs, audio latency overhead, and data privacy concerns regarding storing user audio biometrics.

---

### ADR-007: RESTful Architecture for Standard CRUD Operations
* **Status:** Accepted
* **Context:** The application needs a predictable, standard communication protocol for user management, doctor directories, and appointment lifecycles.
* **Decision:** Use standard REST APIs conforming to JSON standards over HTTP/2.
* **Consequences:**
  - **Positive:** Universal compatibility, stateless scalability, straightforward caching, and automated Swagger/OpenAPI documentation.
* **Alternatives Considered:**
  - *GraphQL:* Rejected as unnecessary complexity for this domain's clear resource hierarchies.

---

### ADR-008: Server-Sent Events (SSE) vs. WebSockets for AI Streaming
* **Status:** Accepted
* **Context:** Conversational responses from Google Gemini must stream tokens to the user in real-time to avoid high perceived latency.
* **Decision:** Use Server-Sent Events (SSE) via `POST /api/v1/assistant/chat/stream`. WebSockets are explicitly rejected.
* **Consequences:**
  - **Positive:** SSE runs over standard HTTP; automatic browser reconnection; full compatibility with HTTP/2 multiplexing; no stateful socket connection management or sticky-session load balancer requirements.
  - **Trade-offs:** Unidirectional only (server-to-client); perfectly matches the AI token streaming requirement since client sends the prompt once and receives streamed tokens.
* **Alternatives Considered:**
  - *WebSockets:* Rejected due to high connection maintenance overhead, complex reconnection logic, and firewall traversal friction with zero architectural benefit for this unidirectional streaming use case.

---

### ADR-009: Strict Prohibition of Direct Database Access by AI Models
* **Status:** Accepted
* **Context:** LLMs cannot be granted direct SQL query or write access to the database due to safety and security risks.
* **Decision:** Google Gemini **never** connects directly to PostgreSQL. All data retrieval and operations occur via authorized backend services executed via structured tool calling.
* **Consequences:**
  - **Positive:** Complete elimination of LLM-generated SQL injection; strict enforcement of business validation logic and Role-Based Access Control (RBAC); deterministic audit logging.
  - **Trade-offs:** Requires maintaining explicit Pydantic tool schemas for every operation the AI is permitted to perform.

---

### ADR-010: Database Concurrency & Double-Booking Elimination Strategy
* **Status:** Accepted
* **Context:** In high-concurrency environments, multiple patients might attempt to reserve the same appointment slot simultaneously.
* **Decision:** Prevent double-bookings through database row-level locking (`SELECT FOR UPDATE`) on the `availability` table combined with a `UNIQUE (availability_id)` constraint on the `appointments` table.
* **Consequences:**
  - **Positive:** Guarantees 100% serializability for appointment bookings without requiring external distributed lock managers (e.g., Redis Redlock). Exactly one transaction succeeds; concurrent transactions fail cleanly with HTTP `409 Conflict`.
  - **Trade-offs:** High-contention slots may experience brief database lock wait times (typically `< 20ms`).

