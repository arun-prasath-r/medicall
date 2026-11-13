import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { aiService } from '../../services/aiService';
import { MicrophoneButton } from './MicrophoneButton';
import { ConversationPanel } from './ConversationPanel';
import { AssistantStatus } from './AssistantStatus';
import { VoiceControls } from './VoiceControls';
import { 
  HeartPulse, 
  ArrowLeft, 
  Send, 
  Trash2, 
  AlertCircle,
  Sparkles
} from 'lucide-react';
import '../../styles/voiceAssistant.css';

/**
 * Medicall AI Voice & Text Clinical Assistant.
 * Full-stack React integration connecting browser Web Speech APIs to FastAPI + Google Gemini backend.
 */
export const VoiceAssistant = () => {
  const navigate = useNavigate();

  // Conversation state
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState(null);
  const [isEmergency, setIsEmergency] = useState(false);
  const [emergencyGuidance, setEmergencyGuidance] = useState(null);
  const [errorBanner, setErrorBanner] = useState(null);

  // Text-to-Speech Hook
  const {
    isSpeaking,
    isMuted,
    rate,
    speak,
    stop: stopSpeaking,
    replay,
    toggleMute,
    setRate,
  } = useSpeechSynthesis();

  // Handle final user speech transcript from Web Speech Recognition
  const handleFinalSpeech = useCallback((transcript) => {
    if (!transcript || !transcript.trim()) return;
    submitMessage(transcript.trim());
  }, []);

  // Speech Recognition Hook
  const {
    isListening,
    interimTranscript,
    error: speechError,
    isSupported: isSpeechSupported,
    permissionStatus,
    startListening,
    stopListening,
    abortListening,
    resetTranscript,
  } = useSpeechRecognition({
    language: 'en-IN',
    onFinalTranscript: handleFinalSpeech,
  });

  // Toggle voice recognition
  const handleMicClick = () => {
    setErrorBanner(null);
    if (isSpeaking) {
      stopSpeaking();
    }

    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Submit message to Gemini AI backend
  const submitMessage = async (messageText) => {
    if (!messageText || !messageText.trim() || isProcessing) return;

    setErrorBanner(null);
    resetTranscript();

    const cleanText = messageText.trim();
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: cleanText,
      timestamp: new Date().toISOString(),
    };

    // Update conversation with user turn
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setTextInput('');
    setIsProcessing(true);

    // Format conversation history for backend (max 10 turns)
    const conversationHistory = updatedMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const response = await aiService.sendChatMessage({
        message: cleanText,
        conversationHistory,
      });

      setIsProcessing(false);

      if (!response || !response.success) {
        throw new Error(response?.error_message || 'The AI assistant was unable to process your request.');
      }

      // Check for clinical emergency escalation
      if (response.is_emergency) {
        setIsEmergency(true);
        setEmergencyGuidance(response.emergency_guidance || response.response);
      }

      // Check for pending confirmation proposal from write tools
      if (response.pending_confirmation && response.pending_confirmation.requires_confirmation) {
        setPendingConfirmation(response.pending_confirmation);
      }

      // Add assistant response to messages
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        disclaimer: response.disclaimer,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Speak response aloud if TTS is enabled
      speak(response.response);
    } catch (err) {
      setIsProcessing(false);
      console.error('AI chat error:', err);
      const errText = err.message || 'Could not communicate with the AI service. Please try again.';
      setErrorBanner(errText);

      const errorMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ ${errText}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  // Handle explicit patient confirmation via ConfirmationCard button
  const handleConfirmProposal = async (confirmationToken, proposal) => {
    setIsConfirming(true);
    setErrorBanner(null);

    try {
      const result = await aiService.confirmAction({ confirmationToken });
      setIsConfirming(false);

      // Successfully confirmed and committed in database
      const successMessage = {
        id: `confirm-success-${Date.now()}`,
        role: 'assistant',
        content: `✅ ${result.message}`,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, successMessage]);
      setPendingConfirmation(null);

      // Speak confirmation success
      speak(result.message);
    } catch (err) {
      setIsConfirming(false);
      const failureMsg = err.message || 'Appointment operation could not be confirmed.';
      setErrorBanner(failureMsg);
      throw err; // Re-throw to display in card
    }
  };

  // Handle user declining or canceling the proposal
  const handleCancelProposal = () => {
    setPendingConfirmation(null);
    const cancelMsg = {
      id: `cancel-${Date.now()}`,
      role: 'assistant',
      content: 'Understood. The proposed operation was cancelled and no changes were made to your schedule.',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, cancelMsg]);
    speak(cancelMsg.content);
  };

  // Text fallback submission
  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (textInput.trim() && !isProcessing) {
      submitMessage(textInput.trim());
    }
  };

  // Clear conversation with prompt
  const handleClearConversation = () => {
    if (messages.length === 0) return;
    if (window.confirm('Are you sure you want to clear your current conversation history?')) {
      stopSpeaking();
      abortListening();
      setMessages([]);
      setPendingConfirmation(null);
      setIsEmergency(false);
      setEmergencyGuidance(null);
      setErrorBanner(null);
      resetTranscript();
    }
  };

  // Determine current high-level status for the header
  const getAssistantStatus = () => {
    if (isListening) return 'listening';
    if (isProcessing) return 'processing';
    if (isSpeaking) return 'speaking';
    if (pendingConfirmation) return 'confirmation';
    return 'ready';
  };

  return (
    <div className="assistant-container">
      {/* Header */}
      <div className="assistant-header">
        <div className="assistant-brand">
          <button
            type="button"
            className="icon-control-btn"
            onClick={() => navigate('/dashboard')}
            title="Return to Dashboard"
            style={{ marginRight: 4 }}
          >
            <ArrowLeft size={16} />
            <span className="hidden-mobile">Dashboard</span>
          </button>

          <div className="assistant-avatar">
            <HeartPulse size={24} />
          </div>

          <div>
            <div className="assistant-title">Medicall Clinical Voice Assistant</div>
            <div className="assistant-subtitle">
              <span>Hands-Free Healthcare Triage & Scheduling</span>
            </div>
          </div>
        </div>

        <AssistantStatus
          status={getAssistantStatus()}
          modelName="gemini-3.5-flash"
        />
      </div>

      {/* Error Alert Banner if an unhandled error occurs */}
      {(errorBanner || speechError) && (
        <div style={{
          backgroundColor: '#fffbeb',
          borderBottom: '1px solid #fde68a',
          padding: '0.65rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.85rem',
          color: '#92400e',
          gap: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} color="#d97706" />
            <span>{errorBanner || speechError}</span>
          </div>
          <button
            type="button"
            onClick={() => { setErrorBanner(null); resetTranscript(); }}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600, color: '#92400e' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Conversation Body */}
      <ConversationPanel
        messages={messages}
        interimTranscript={interimTranscript}
        isProcessing={isProcessing}
        pendingConfirmation={pendingConfirmation}
        emergencyGuidance={emergencyGuidance}
        isEmergency={isEmergency}
        onConfirmProposal={handleConfirmProposal}
        onCancelProposal={handleCancelProposal}
        isConfirming={isConfirming}
        onReplayMessage={(text) => speak(text)}
        onSelectSuggestion={(text) => submitMessage(text)}
      />

      {/* Controls Area */}
      <div className="assistant-controls-area">
        {/* Central Large Microphone Button */}
        <MicrophoneButton
          isListening={isListening}
          isProcessing={isProcessing}
          isSpeaking={isSpeaking}
          permissionStatus={permissionStatus}
          isSupported={isSpeechSupported}
          onClick={handleMicClick}
          disabled={isProcessing || isConfirming}
        />

        {/* Text Fallback Input Bar */}
        <form className="input-fallback-bar" onSubmit={handleTextSubmit}>
          <input
            type="text"
            className="input-fallback-field"
            placeholder={
              isListening
                ? 'Listening to speech...'
                : 'Type your symptoms, inquiry, or question...'
            }
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            disabled={isProcessing || isListening}
            aria-label="Clinical inquiry text input"
          />

          <button
            type="submit"
            className="input-send-btn"
            disabled={!textInput.trim() || isProcessing || isListening}
            title="Send message"
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </form>

        {/* Toolbar: Voice Controls & Conversation Clear */}
        <div className="assistant-toolbar">
          <VoiceControls
            isSpeaking={isSpeaking}
            isMuted={isMuted}
            rate={rate}
            onToggleMute={toggleMute}
            onStop={stopSpeaking}
            onReplay={replay}
            onChangeRate={setRate}
            canReplay={messages.some((m) => m.role === 'assistant')}
          />

          <button
            type="button"
            className="icon-control-btn"
            onClick={handleClearConversation}
            disabled={messages.length === 0 || isProcessing}
            title="Clear conversation"
          >
            <Trash2 size={14} />
            <span>Clear Chat</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistant;

