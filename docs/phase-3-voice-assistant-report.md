# MEDICALL — PHASE 3: AI VOICE ASSISTANT & FRONTEND INTEGRATION REPORT

**Project Name:** Medicall  
**Document Version:** 3.0.0  
**Phase:** 3 — AI Voice Assistant & Frontend Integration  
**Date:** November 2026  
**Roles:** Senior React Engineer, AI Application Architect, UX Engineer, Healthcare Software Developer  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

Phase 3 successfully integrated a full-featured, healthcare-grade AI voice assistant into the Medicall React application. Connected directly to the FastAPI + Google Gemini backend established in Phases 2 and 2.1, the voice assistant enables patients to speak naturally, receive real-time clinical triage navigation, and perform authenticated doctor searches, availability checks, and appointment scheduling with explicit, deterministic patient confirmation.

The system uses browser-native Web Speech APIs (`SpeechRecognition` / `webkitSpeechRecognition` and `SpeechSynthesis`) for zero-cost, privacy-conscious voice interaction without introducing paid speech-to-text or text-to-speech services. The implementation adheres to strict clinical safety boundaries, deterministic emergency detection, single-use replay protection, and the Forest Green, Sage Green, and Warm Ivory design language.

---

## 2. Frontend Architecture & Component Directory

The AI voice assistant frontend architecture is modularized under `frontend/src/`:

```text
frontend/src/
├── components/
│   └── ai/
│       ├── VoiceAssistant.jsx       # Master orchestrator container
│       ├── MicrophoneButton.jsx     # Multi-state animated circular microphone button
│       ├── ConversationPanel.jsx    # Auto-scrolling chat log with suggestion chips
│       ├── MessageBubble.jsx        # Patient vs Assistant turns, timestamps & replay
│       ├── ConfirmationCard.jsx     # Dedicated proposal card with explicit confirm/cancel
│       ├── EmergencyBanner.jsx      # High-visibility red alert directive with tel:112
│       ├── VoiceControls.jsx        # Mute, stop, replay, and speech rate toggles
│       └── AssistantStatus.jsx      # Header status pill showing Gemini model & JWT state
├── hooks/
│   ├── useSpeechRecognition.js      # Web Speech Recognition hook (STT)
│   └── useSpeechSynthesis.js        # Web Speech Synthesis hook (TTS)
├── services/
│   ├── aiService.js                 # API client for /ai/chat, /ai/confirm, /ai/status
│   ├── aiService.test.js            # Automated unit tests for AI service
│   └── api.js                       # Axios instance with JWT interceptor & auto-refresh
├── pages/
│   ├── VoiceAssistantPage.jsx       # Page wrapper mounted at /assistant
│   └── PatientDashboardPage.jsx     # Updated with active "Launch Assistant" CTA
├── styles/
│   └── voiceAssistant.css           # Brand palette, wave animations, responsive layout
└── App.jsx                          # Route registration under ProtectedRoute (PATIENT)
```

---

## 3. Speech Recognition Implementation (`useSpeechRecognition.js`)

- **Browser APIs:** Utilizes `window.SpeechRecognition || window.webkitSpeechRecognition`.
- **User-Initiated Activation:** Microphone hardware capture starts strictly upon explicit user interaction (tapping the microphone button). No background recording occurs.
- **Language Localization:** Defaults to `en-IN` (English - India) with dynamic configuration support.
- **Interim Speech Streaming:** Captures intermediate hypotheses as the patient speaks, rendering live italicized interim text bubbles in the conversation panel.
- **Final Transcript Deduplication:** Tracks the last processed final utterance (`lastProcessedTranscriptRef`), ensuring identical transcripts from speech engine silence pauses are not re-submitted to the backend.
- **Comprehensive Error Resilience:**
  - `not-allowed` / `service-not-allowed`: Sets permission state to `denied` with actionable instructions to enable browser permissions.
  - `no-speech`: Gracefully returns to idle state without disruptive error toasts.
  - `audio-capture`: Informs the patient if no microphone device is connected.
  - `network`: Guides the patient to check network connectivity or switch to text input.
  - `unsupported`: Gracefully degrades to text-only mode with visual indicators.
- **Teardown & Cleanup:** Cancels and aborts ongoing recognition sessions on component unmount, preventing memory leaks or lingering microphone capture locks.

---

## 4. Speech Synthesis Implementation (`useSpeechSynthesis.js`)

- **Browser API:** Leverages `window.speechSynthesis` and `SpeechSynthesisUtterance`.
- **Assistant-Only Speech:** Only vocalizes assistant responses and emergency directives. Patient messages and prior history turns are never read aloud automatically.
- **Text Sanitization for Natural Vocalization:**
  - Converts bullet symbols (`*`, `•`, `-`) into natural pauses (`, `).
  - Strips markdown formatting (`**bold**`, `# headers`, `` `code` ``).
  - Excludes raw URLs and http links from audio output.
- **Playback Controls:**
  - **Mute / Voice On Toggle:** Persists user preference in browser `localStorage`.
  - **Stop Button:** Instantly invokes `window.speechSynthesis.cancel()`.
  - **Replay Button:** Replays the most recent assistant response.
  - **Speech Speed Selector:** Allows cycling through `0.9x`, `1.0x`, and `1.2x` rates, clamped between safe bounds (0.8x to 1.4x).
- **Emergency Priority:** Emergency directives are spoken promptly when audio is unmuted, while immediately displaying the persistent visual banner without delay.

---

## 5. Gemini API Integration & Function Calling Flow

The assistant connects to FastAPI backend endpoints via `frontend/src/services/aiService.js`:
- `POST /api/v1/ai/chat`: Sends `{ message, conversation_history, confirmation_token }`. Configured with a 35-second client timeout to accommodate multi-turn LLM reasoning.
- `POST /api/v1/ai/confirm`: Sends `{ confirmation_token }` for deterministic execution of explicit patient confirmations.
- `GET /api/v1/ai/status`: Inspects provider availability and model configuration.

### Tool Execution Sequence:
1. **Patient Speaks:** *"Find me a cardiologist."*
2. **Backend Execution:** Safety service checks red flags (none found). Gemini calls `search_doctors(specialty='Cardiology')`.
3. **Doctor Results:** Gemini returns qualified verified doctors. Assistant speaks the response.
4. **Patient Speaks:** *"Book an appointment with Dr. Sarah Smith tomorrow at 10 AM."*
5. **Stage 1 (Proposal):** Gemini calls `book_appointment(...)` without a confirmation token. Backend generates proposal with a signed single-use JWT containing a unique `jti`. Loop guard halts loop and returns `pending_confirmation`.
6. **Confirmation Card Displayed:** Dedicated card renders with doctor name, specialty, date, time, fee ($150.00), and complaint.
7. **Explicit Confirmation:** Patient clicks **Confirm Booking**. Frontend calls `POST /api/v1/ai/confirm`.
8. **Stage 2 (Commitment):** Backend validates cryptographic signature, patient ownership, single-use nonce consumption in `consumed_confirmation_tokens`, row-locks the slot, and books the appointment.
9. **Success Rendered:** Confirmation message and appointment reference code (`MED-...`) are displayed and vocalized.

---

## 6. Appointment Confirmation Security Architecture

The confirmation workflow strictly fulfills the zero-trust requirements:
- **No Autonomous Write Actions:** Gemini cannot finalize write actions on its own turn. Proposals must be returned to the client.
- **Deterministic Action Button:** The confirmation button calls `POST /api/v1/ai/confirm` directly, eliminating non-deterministic LLM hallucination or tool omission risks during final execution.
- **Single-Use Replay Protection:** Replaying an already-consumed token fails immediately with HTTP 400 (`"Confirmation token has already been used. Tokens are strictly single-use to prevent replay."`).
- **Patient Isolation:** Tokens are cryptographically bound to the authenticated patient's UUID. Attempting to execute a token generated for Patient A while logged in as Patient B raises an unauthorized error.
- **Sensitive Token Redaction:** Tokens are kept in component memory during active proposal review and never printed in visible chat text, markdown bubbles, or console logs.

---

## 7. Browser Compatibility & Limitations

| Browser | Speech Recognition (STT) | Speech Synthesis (TTS) | Experience Level |
| :--- | :--- | :--- | :--- |
| **Google Chrome (Desktop/Android)** | Native (`webkitSpeechRecognition`) | Native (`speechSynthesis`) | **Optimal (Full Voice & Audio)** |
| **Microsoft Edge (Desktop)** | Native (`webkitSpeechRecognition`) | Native (`speechSynthesis`) | **Optimal (Full Voice & Audio)** |
| **Apple Safari (macOS/iOS)** | Native (`webkitSpeechRecognition` on iOS 14.5+) | Native (`speechSynthesis`) | **High (Standard Voice & Audio)** |
| **Mozilla Firefox** | Unsupported (Flags required) | Native (`speechSynthesis`) | **Fallback (Text Input + Audio TTS)** |
| **Brave / Chromium Privacy** | Requires Speech Services enabled | Native (`speechSynthesis`) | **High / Config Dependent** |

*Note: For browsers or operating systems where speech recognition is disabled or unsupported, Medicall displays an informative status pill and provides a responsive, text-based fallback input bar.*

---

## 8. Automated Test Results

### Frontend Test Suite: 50 Tests Passed (100%)
```bash
npm --prefix frontend test
```
**Results:** `50 passed in 153.78ms`
- `src/components/ai/voiceAssistant.test.js`: 13 passed (booking/cancel/reschedule card proposals, explicit confirmation execution, patient cancellation, emergency directives, microphone button state machine)
- `src/hooks/speech.test.js`: 11 passed (speech recognition permissions, unsupported browser handling, transcript deduplication, speech synthesis sanitization, rate limits, audio cancel)
- `src/services/aiService.test.js`: 8 passed (empty message rejection, payload formatting, history slicing to 10 items, error formatting, confirmAction execution, token replay error, status check)
- `src/utils/dateTime.test.js`: 12 passed (IST timezone standardization, UTC conversion, edge cases)
- `src/utils/errorUtils.test.js`: 6 passed (FastAPI 422 array formatting, network errors)

### Backend Regression Test Suite: 109 Tests Passed (100%)
```bash
PYTHONPATH=backend backend/venv/bin/pytest backend/tests -v
```
**Results:** `109 passed in 9.21s`
- Verified `POST /api/v1/ai/confirm` endpoint success, invalid token handling, and token replay rejection against PostgreSQL.
- Verified all 12 mandatory clinical emergency phrases.
- Verified database row locking concurrency on Port 5433 `medicall-postgres`.

---

## 9. Known Limitations & Next Steps

1. **Web Speech API Cloud Dependency:** Chrome's `webkitSpeechRecognition` relies on Google's client speech recognition services. In offline environments, speech recognition will trigger a network error, gracefully handled by falling back to text input.
2. **iOS Audio Autoplay Policies:** Mobile Safari requires user gesture interaction before `speechSynthesis.speak()` can output audio. Medicall handles this because all audio outputs originate from patient tap events.
3. **Phase 4 Preparation:** Future phases may explore full duplex audio streaming or WebRTC integration when low-latency bidirectional voice streams are introduced.

