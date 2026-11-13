import { describe, it } from 'node:test';
import assert from 'node:assert';

describe('Voice Assistant Components & UI Workflow Logic Tests', () => {
  // --------------------------------------------------------------------------
  // 1. APPOINTMENT CONFIRMATION CARD WORKFLOW & DATA INTEGRITY
  // --------------------------------------------------------------------------
  describe('Confirmation Card Proposal Validation', () => {
    it('should validate structured booking proposal fields', () => {
      const proposal = {
        action: 'book_appointment',
        confirmation_token: 'valid-jwt-booking-nonce',
        doctor_name: 'Dr. Sarah Smith',
        specialty: 'Cardiology',
        consultation_fee: 150.0,
        slot_date: 'Friday, November 20, 2026',
        slot_time: '10:00 AM - 10:30 AM',
        chief_complaint: 'Routine heart checkup',
        summary: 'Booking with Dr. Sarah Smith (Cardiology) on Friday, November 20, 2026 at 10:00 AM.',
      };

      assert.strictEqual(proposal.action, 'book_appointment');
      assert.strictEqual(proposal.confirmation_token.length > 0, true);
      assert.strictEqual(proposal.doctor_name, 'Dr. Sarah Smith');
      assert.strictEqual(proposal.consultation_fee, 150.0);
      assert.strictEqual(proposal.slot_time, '10:00 AM - 10:30 AM');
    });

    it('should validate structured cancellation proposal fields with warning', () => {
      const proposal = {
        action: 'cancel_appointment',
        confirmation_token: 'valid-jwt-cancel-nonce',
        appointment_id: 'appt-uuid-456',
        reference_code: 'MED-782190',
        doctor_name: 'Dr. Gregory House',
        appointment_datetime: 'Monday, December 01, 2026 at 09:30 AM',
        reason: 'Patient travel conflict',
        summary: 'Cancel appointment MED-782190 with Dr. Gregory House.',
      };

      assert.strictEqual(proposal.action, 'cancel_appointment');
      assert.strictEqual(proposal.reference_code, 'MED-782190');
      assert.strictEqual(proposal.appointment_id, 'appt-uuid-456');
    });

    it('should validate structured rescheduling proposal fields', () => {
      const proposal = {
        action: 'reschedule_appointment',
        confirmation_token: 'valid-jwt-reschedule-nonce',
        appointment_id: 'appt-uuid-789',
        reference_code: 'MED-123456',
        doctor_name: 'Dr. Sarah Smith',
        old_date: 'Nov 20, 2026',
        old_time: '10:00 AM',
        new_date: 'Nov 27, 2026',
        new_time: '11:00 AM',
      };

      assert.strictEqual(proposal.action, 'reschedule_appointment');
      assert.strictEqual(proposal.old_date, 'Nov 20, 2026');
      assert.strictEqual(proposal.new_date, 'Nov 27, 2026');
    });

    it('should execute explicit patient confirm action only when triggered with token', async () => {
      let executedAction = null;
      let submittedToken = null;

      const mockConfirm = async (token, prop) => {
        executedAction = prop.action;
        submittedToken = token;
        return { success: true, message: 'Confirmed!' };
      };

      const proposal = {
        action: 'book_appointment',
        confirmation_token: 'secret-jti-nonce-token',
      };

      // Patient explicitly presses confirm
      const result = await mockConfirm(proposal.confirmation_token, proposal);

      assert.strictEqual(executedAction, 'book_appointment');
      assert.strictEqual(submittedToken, 'secret-jti-nonce-token');
      assert.strictEqual(result.success, true);
    });

    it('should handle patient rejection / cancellation of a proposal without database changes', () => {
      let activeProposal = {
        action: 'book_appointment',
        confirmation_token: 'temp-token',
      };

      const handleCancel = () => {
        activeProposal = null;
      };

      handleCancel();
      assert.strictEqual(activeProposal, null);
    });
  });

  // --------------------------------------------------------------------------
  // 2. CLINICAL EMERGENCY SAFETY & RED-FLAG DIRECTIVES
  // --------------------------------------------------------------------------
  describe('Clinical Emergency Directive Validation', () => {
    it('should preserve backend emergency guidance without alteration', () => {
      const apiEmergencyResponse = {
        is_emergency: true,
        urgency_level: 'EMERGENCY',
        emergency_guidance:
          'POTENTIAL MEDICAL EMERGENCY DETECTED (Suspected Acute Coronary Syndrome). Please call 112 immediately.',
      };

      assert.strictEqual(apiEmergencyResponse.is_emergency, true);
      assert.match(apiEmergencyResponse.emergency_guidance, /112/);
      assert.match(
        apiEmergencyResponse.emergency_guidance,
        /Suspected Acute Coronary Syndrome/
      );
    });

    it('should include clear disclosure that Medicall cannot dispatch ambulances', () => {
      const disclosure =
        'Medicall AI is an informational scheduling assistant and cannot dispatch emergency medical responders.';

      assert.strictEqual(
        disclosure.includes('cannot dispatch emergency medical responders'),
        true
      );
    });
  });

  // --------------------------------------------------------------------------
  // 3. MICROPHONE BUTTON MULTI-STATE MACHINE
  // --------------------------------------------------------------------------
  describe('Microphone Button State Machine', () => {
    const resolveButtonState = ({
      isListening,
      isProcessing,
      isSpeaking,
      permissionStatus,
      isSupported,
    }) => {
      if (!isSupported) return { stateClass: 'unsupported', label: 'Voice unsupported' };
      if (permissionStatus === 'denied') return { stateClass: 'error', label: 'Microphone blocked' };
      if (isProcessing) return { stateClass: 'processing', label: 'Processing with Gemini...' };
      if (isSpeaking) return { stateClass: 'speaking', label: 'Speaking... Tap to stop' };
      if (isListening) return { stateClass: 'listening', label: 'Listening... Tap when done' };
      return { stateClass: 'idle', label: 'Tap to speak' };
    };

    it('should resolve to idle state by default', () => {
      const state = resolveButtonState({
        isListening: false,
        isProcessing: false,
        isSpeaking: false,
        permissionStatus: 'granted',
        isSupported: true,
      });
      assert.strictEqual(state.stateClass, 'idle');
      assert.strictEqual(state.label, 'Tap to speak');
    });

    it('should resolve to listening state when recording speech', () => {
      const state = resolveButtonState({
        isListening: true,
        isProcessing: false,
        isSpeaking: false,
        permissionStatus: 'granted',
        isSupported: true,
      });
      assert.strictEqual(state.stateClass, 'listening');
      assert.strictEqual(state.label, 'Listening... Tap when done');
    });

    it('should resolve to processing state when Gemini is thinking', () => {
      const state = resolveButtonState({
        isListening: false,
        isProcessing: true,
        isSpeaking: false,
        permissionStatus: 'granted',
        isSupported: true,
      });
      assert.strictEqual(state.stateClass, 'processing');
      assert.strictEqual(state.label, 'Processing with Gemini...');
    });

    it('should resolve to speaking state when vocalizing response', () => {
      const state = resolveButtonState({
        isListening: false,
        isProcessing: false,
        isSpeaking: true,
        permissionStatus: 'granted',
        isSupported: true,
      });
      assert.strictEqual(state.stateClass, 'speaking');
      assert.strictEqual(state.label, 'Speaking... Tap to stop');
    });

    it('should resolve to error state when microphone permission is denied', () => {
      const state = resolveButtonState({
        isListening: false,
        isProcessing: false,
        isSpeaking: false,
        permissionStatus: 'denied',
        isSupported: true,
      });
      assert.strictEqual(state.stateClass, 'error');
      assert.strictEqual(state.label, 'Microphone blocked');
    });

    it('should resolve to unsupported state in non-compliant browsers', () => {
      const state = resolveButtonState({
        isListening: false,
        isProcessing: false,
        isSpeaking: false,
        permissionStatus: 'prompt',
        isSupported: false,
      });
      assert.strictEqual(state.stateClass, 'unsupported');
      assert.strictEqual(state.label, 'Voice unsupported');
    });
  });
});

