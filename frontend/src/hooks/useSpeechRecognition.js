import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom React hook for browser Web Speech API Speech Recognition.
 * Supports Chrome, Edge, Safari (webkitSpeechRecognition) with graceful fallbacks.
 *
 * @param {Object} options
 * @param {string} [options.language='en-IN'] - Initial recognition language.
 * @param {Function} [options.onFinalTranscript] - Callback triggered when final speech is recognized.
 * @returns {Object} Speech recognition state and control functions.
 */
export const useSpeechRecognition = ({
  language = 'en-IN',
  onFinalTranscript,
} = {}) => {
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [error, setError] = useState(null);
  const [permissionStatus, setPermissionStatus] = useState('prompt'); // 'prompt' | 'granted' | 'denied'
  const [selectedLanguage, setSelectedLanguage] = useState(language);

  // References
  const recognitionRef = useRef(null);
  const lastProcessedTranscriptRef = useRef('');
  const onFinalTranscriptRef = useRef(onFinalTranscript);

  // Keep callback ref fresh without triggering effect re-runs
  useEffect(() => {
    onFinalTranscriptRef.current = onFinalTranscript;
  }, [onFinalTranscript]);

  // Check browser support
  const isSupported = typeof window !== 'undefined' && Boolean(
    window.SpeechRecognition || window.webkitSpeechRecognition
  );

  // Clean stop and cleanup
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore if already stopped
      }
    }
    setIsListening(false);
  }, []);

  // Abort immediately (for cancellations/unmount)
  const abortListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // Ignore
      }
    }
    setIsListening(false);
    setInterimTranscript('');
  }, []);

  // Start listening
  const startListening = useCallback((customLang) => {
    setError(null);
    setInterimTranscript('');
    setFinalTranscript('');

    if (!isSupported) {
      setError(
        'Speech recognition is not supported in this browser. Please use Google Chrome, Microsoft Edge, or Apple Safari, or type your message.'
      );
      return;
    }

    // Stop any existing instance
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // Ignore
      }
    }

    try {
      const SpeechRecognitionClass =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognitionClass();

      const langToUse = customLang || selectedLanguage || 'en-IN';
      recognition.lang = langToUse;
      recognition.continuous = false; // Capture a discrete conversational turn
      recognition.interimResults = true; // Stream interim results to UI
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
        setPermissionStatus('granted');
        setError(null);
      };

      recognition.onresult = (event) => {
        let currentInterim = '';
        let currentFinal = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i];
          const transcriptText = item[0]?.transcript || '';

          if (item.isFinal) {
            currentFinal += transcriptText;
          } else {
            currentInterim += transcriptText;
          }
        }

        if (currentInterim) {
          setInterimTranscript(currentInterim);
        }

        if (currentFinal) {
          const cleanFinal = currentFinal.trim();
          setFinalTranscript(cleanFinal);
          setInterimTranscript('');

          // Deduplicate: prevent submitting the exact same utterance multiple times in quick succession
          if (
            cleanFinal.length > 0 &&
            cleanFinal !== lastProcessedTranscriptRef.current
          ) {
            lastProcessedTranscriptRef.current = cleanFinal;
            if (onFinalTranscriptRef.current) {
              onFinalTranscriptRef.current(cleanFinal);
            }
          }
        }
      };

      recognition.onerror = (event) => {
        setIsListening(false);
        const errType = event.error;

        if (errType === 'not-allowed' || errType === 'service-not-allowed') {
          setPermissionStatus('denied');
          setError(
            'Microphone access was denied. Please allow microphone permissions in your browser settings to use voice input.'
          );
        } else if (errType === 'no-speech') {
          // Patient was silent; gentle notification without scary error banner
          setError(null);
        } else if (errType === 'audio-capture') {
          setError(
            'No microphone was detected on your device. Please ensure an audio input device is connected.'
          );
        } else if (errType === 'network') {
          setError(
            'Speech recognition network error. Please check your internet connection or use text input.'
          );
        } else if (errType !== 'aborted') {
          setError(`Speech recognition error (${errType}). Please try again or type your message.`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      setIsListening(false);
      setError(`Could not initialize speech recognition: ${err.message || 'Unknown error'}`);
    }
  }, [isSupported, selectedLanguage]);

  // Reset transcript buffers
  const resetTranscript = useCallback(() => {
    setInterimTranscript('');
    setFinalTranscript('');
    lastProcessedTranscriptRef.current = '';
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore
        }
      }
    };
  }, []);

  return {
    isListening,
    interimTranscript,
    finalTranscript,
    error,
    isSupported,
    permissionStatus,
    language: selectedLanguage,
    setLanguage: setSelectedLanguage,
    startListening,
    stopListening,
    abortListening,
    resetTranscript,
  };
};

export default useSpeechRecognition;

