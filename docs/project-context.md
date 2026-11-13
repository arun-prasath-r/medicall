# Medicall - Project Context & Implementation Overview

**Project Name:** Medicall  
**Document Version:** 4.0.0  
**Phase:** 4 — End-to-End Integration, Real-World Validation & Production Readiness  
**Date:** November 2026  
**Status:** FULL-STACK APPLICATION READY FOR CONTROLLED RELEASE  

---

## 1. Project Objective & Clinical Mission

Medicall is a premium digital healthcare SaaS platform designed to modernize patient-doctor appointment management and triage navigation. The platform integrates an AI-powered clinical assistant combining browser-native voice capabilities (Web Speech API) with Google Gemini large language models.

### Primary Capabilities:
1. **Clinical Triage & Discovery:** Patients describe symptoms or inquiries naturally by voice or text. The system provides non-diagnostic informational guidance, suggests relevant medical specialties, and queries verified physicians from PostgreSQL.
2. **Real-Time Calendar Management:** Doctors establish recurring weekly schedules. Concrete discrete availability slots are generated, booked, cancelled, and rescheduled with row-level transactional concurrency control (`SELECT FOR UPDATE`).
3. **Dual-Layer Medical Safety:** Deterministic red-flag algorithms catch acute life-threatening emergencies (e.g. acute coronary syndrome, stroke, respiratory compromise, anaphylaxis, active hemorrhage, self-harm) before or in parallel with LLM processing, immediately surfacing emergency directives and local emergency hotlines (`112`).
4. **Zero-Trust Two-Stage Confirmation Protocol:** All write operations (`book_appointment`, `cancel_appointment`, `reschedule_appointment`) require explicit, out-of-band patient approval via dedicated UI confirmation cards backed by persistent single-use cryptographic tokens (`consumed_confirmation_tokens`).

---

## 2. Technology Stack & Component Map

| Layer | Technologies & Libraries | Responsibility |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite 5, JavaScript ES2022, React Router v6, Axios, Lucide React, Web Speech API | Client Single Page Application (SPA), speech-to-text, text-to-speech, responsive UI |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Pydantic Settings, Argon2, PyJWT | Asynchronous REST API, JWT authentication, RBAC, domain services, AI orchestration |
| **Persistence** | PostgreSQL 16.4, SQLAlchemy 2.0, Alembic, psycopg3 driver | ACID relational storage, row-level locking, foreign-key cascades, single-use nonce tracking |
| **AI Engine** | Google Gemini API (`google-genai` SDK), `gemini-3.5-flash` with `gemini-3.5-flash-lite` fallback | Natural language symptom understanding, multi-turn tool calling across 6 domain functions |
| **Infrastructure**| Docker, Docker Compose, Nginx (production gateway) | Isolated database containers, volume persistence, environment separation |

---

## 3. Four-Phase Evolution Summary

- **Phase 1 (Backend Foundation & Database Integration):** Established FastAPI backend, PostgreSQL relational schema across 6 core tables, Argon2 authentication, role-based authorization, discrete slot generation, and Alembic migrations.
- **Phase 2 (Gemini Function Calling & Security Hardening):** Integrated `google-genai` SDK, registered 6 domain tools, implemented two-stage action proposal protocol, and established deterministic emergency triage filters.
- **Phase 2.1 (Confirmation Hardening & Clinical Safety Validation):** Created `consumed_confirmation_tokens` PostgreSQL table for persistent single-use replay protection, implemented orchestration loop guard breaking multi-turn auto-execution, resolved "rule out" diagnostic false negatives, and validated 12 mandatory clinical emergency phrases.
- **Phase 3 (AI Voice Assistant & Frontend Integration):** Implemented `useSpeechRecognition` and `useSpeechSynthesis` hooks, developed modular voice assistant components (`VoiceAssistant`, `MicrophoneButton`, `ConfirmationCard`, `EmergencyBanner`, `VoiceControls`), integrated `/assistant` route, and activated patient dashboard integration.
- **Phase 4 (End-to-End Integration & Production Readiness):** Discovered and resolved live GenAI role compatibility (`role="user"`), validated all 8 patient journeys against real PostgreSQL and Gemini APIs, audited bundle security, improved accessibility, and verified zero secret leakage.

