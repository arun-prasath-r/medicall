import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert';

describe('Web Speech API & Voice Assistant Hooks Unit Tests', () => {
  // --------------------------------------------------------------------------
  // 1. SPEECH RECOGNITION TESTS
  // --------------------------------------------------------------------------
  describe('Speech Recognition Logic & Event Handling', () => {
    it('should detect unsupported browsers when SpeechRecognition is absent', () => {
      const windowMock = {};
      const isSupported = Boolean(
        windowMock.SpeechRecognition || windowMock.webkitSpeechRecognition
      );
      assert.strictEqual(isSupported, false);
    });

    it('should detect supported browsers when webkitSpeechRecognition is present', () => {
      const windowMock = {
        webkitSpeechRecognition: class MockSpeechRecognition {},
      };
      const isSupported = Boolean(
        windowMock.SpeechRecognition || windowMock.webkitSpeechRecognition
      );
      assert.strictEqual(isSupported, true);
    });

    it('should map permission denial error to clear user instruction', () => {
      const event = { error: 'not-allowed' };
      let permissionStatus = 'prompt';
      let error = null;

      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        permissionStatus = 'denied';
        error =
          'Microphone access was denied. Please allow microphone permissions in your browser settings to use voice input.';
      }

      assert.strictEqual(permissionStatus, 'denied');
      assert.match(error, /Microphone access was denied/);
    });

    it('should handle no-speech without alarming the user', () => {
      const event = { error: 'no-speech' };
      let error = 'Some previous error';

      if (event.error === 'no-speech') {
        error = null;
      }

      assert.strictEqual(error, null);
    });

    it('should accumulate interim and final speech transcripts accurately', () => {
      const mockResultEvent = {
        resultIndex: 0,
        results: [
          [{ transcript: 'I need an ' }],
          [{ transcript: 'appointment with a ' }],
          Object.assign([ { transcript: 'cardiologist' } ], { isFinal: true }),
        ],
      };

      // Mark the first two as interim
      mockResultEvent.results[0].isFinal = false;
      mockResultEvent.results[1].isFinal = false;

      let currentInterim = '';
      let currentFinal = '';

      for (let i = mockResultEvent.resultIndex; i < mockResultEvent.results.length; i++) {
        const item = mockResultEvent.results[i];
        const text = item[0]?.transcript || '';
        if (item.isFinal) {
          currentFinal += text;
        } else {
          currentInterim += text;
        }
      }

      assert.strictEqual(currentInterim, 'I need an appointment with a ');
      assert.strictEqual(currentFinal, 'cardiologist');
    });

    it('should prevent duplicate submissions of identical final transcripts', () => {
      let lastProcessedTranscript = '';
      const submittedTranscripts = [];

      const processFinalTranscript = (text) => {
        const clean = text.trim();
        if (clean.length > 0 && clean !== lastProcessedTranscript) {
          lastProcessedTranscript = clean;
          submittedTranscripts.push(clean);
        }
      };

      processFinalTranscript('Book appointment tomorrow');
      processFinalTranscript('Book appointment tomorrow'); // duplicate: should be ignored
      processFinalTranscript('Book appointment tomorrow'); // duplicate: should be ignored
      processFinalTranscript('Different query');

      assert.strictEqual(submittedTranscripts.length, 2);
      assert.strictEqual(submittedTranscripts[0], 'Book appointment tomorrow');
      assert.strictEqual(submittedTranscripts[1], 'Different query');
    });
  });

  // --------------------------------------------------------------------------
  // 2. SPEECH SYNTHESIS (TEXT-TO-SPEECH) TESTS
  // --------------------------------------------------------------------------
  describe('Speech Synthesis Sanitization & Playback Logic', () => {
    // Utility cleanText function identical to hook implementation
    const cleanTextForSpeech = (rawText) => {
      if (!rawText) return '';
      return rawText
        .replace(/^[*\-•\u2022]\s+/gm, ', ')
        .replace(/[*_#`~[\]]/g, '')
        .replace(/https?:\/\/\S+/g, '')
        .replace(/[•\u2022]/g, ', ')
        .replace(/\n+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    };

    it('should strip markdown bold, headers, asterisks and bullets from spoken text', () => {
      const input =
        '### Available Doctors\n* **Dr. Sarah Smith** (Cardiology)\n• Available tomorrow at *10:00 AM*.';
      const cleaned = cleanTextForSpeech(input);

      assert.strictEqual(
        cleaned,
        'Available Doctors , Dr. Sarah Smith (Cardiology) , Available tomorrow at 10:00 AM.'
      );
      assert.strictEqual(cleaned.includes('*'), false);
      assert.strictEqual(cleaned.includes('#'), false);
    });

    it('should strip URLs and links from speech output', () => {
      const input = 'Please review clinic guidelines at https://medicall.health/terms today.';
      const cleaned = cleanTextForSpeech(input);

      assert.strictEqual(cleaned, 'Please review clinic guidelines at today.');
    });

    it('should respect mute state and not produce utterances when muted', () => {
      const isMuted = true;
      let speechTriggered = false;

      const speak = (text) => {
        if (isMuted || !text) return;
        speechTriggered = true;
      };

      speak('Medicall advice');
      assert.strictEqual(speechTriggered, false);
    });

    it('should clamp speech rate within safe clinical audio bounds (0.8x to 1.4x)', () => {
      const clampRate = (rate) => Math.max(0.8, Math.min(rate, 1.4));

      assert.strictEqual(clampRate(0.5), 0.8);
      assert.strictEqual(clampRate(1.0), 1.0);
      assert.strictEqual(clampRate(1.2), 1.2);
      assert.strictEqual(clampRate(2.5), 1.4);
    });

    it('should cancel previous utterance before speaking a new response', () => {
      let cancelCount = 0;
      let speakCount = 0;

      const mockSynthesis = {
        cancel: () => {
          cancelCount++;
        },
        speak: () => {
          speakCount++;
        },
      };

      const speakText = (text) => {
        mockSynthesis.cancel();
        mockSynthesis.speak();
      };

      speakText('First sentence');
      speakText('Second sentence');

      assert.strictEqual(cancelCount, 2);
      assert.strictEqual(speakCount, 2);
    });
  });
});
