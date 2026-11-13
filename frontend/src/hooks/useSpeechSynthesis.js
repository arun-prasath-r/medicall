import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom React hook for browser Web Speech API Speech Synthesis (Text-to-Speech).
 * Delivers natural audio vocalization of Medicall AI assistant clinical guidance.
 *
 * @param {Object} options
 * @param {boolean} [options.defaultMuted=false] - Whether speech is initially muted.
 * @param {number} [options.defaultRate=1.0] - Speech rate (0.8 to 1.4).
 * @param {string} [options.language='en-IN'] - Preferred speech synthesis voice language.
 * @returns {Object} Speech synthesis state and control methods.
 */
export const useSpeechSynthesis = ({
  defaultMuted = false,
  defaultRate = 1.0,
  language = 'en-IN',
} = {}) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isMuted, setIsMuted] = useState(() => {
    try {
      const stored = localStorage.getItem('medicall_voice_muted');
      return stored !== null ? JSON.parse(stored) : defaultMuted;
    } catch {
      return defaultMuted;
    }
  });
  const [rate, setRate] = useState(defaultRate);
  const [lastSpokenText, setLastSpokenText] = useState('');

  const isSupported =
    typeof window !== 'undefined' && 'speechSynthesis' in window;

  const currentUtteranceRef = useRef(null);

  // Sync mute state to localStorage
  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('medicall_voice_muted', JSON.stringify(next));
      } catch {
        // Ignore
      }
      if (next && isSupported) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
      }
      return next;
    });
  }, [isSupported]);

  // Stop speaking immediately
  const stop = useCallback(() => {
    if (!isSupported) return;
    try {
      window.speechSynthesis.cancel();
    } catch {
      // Ignore
    }
    setIsSpeaking(false);
    setIsPaused(false);
  }, [isSupported]);

  // Clean utterance text for vocalization: remove markdown formatting, bullet symbols, asterisks, URLs
  const cleanTextForSpeech = useCallback((rawText) => {
    if (!rawText) return '';
    return rawText
      .replace(/^[*\-•\u2022]\s+/gm, ', ') // list items/bullets at start of lines become pauses
      .replace(/[*_#`~[\]]/g, '') // remove markdown bold/heading/code syntax
      .replace(/https?:\/\/\S+/g, '') // remove links
      .replace(/[•\u2022]/g, ', ') // remaining bullet symbols
      .replace(/\n+/g, ' ') // normalize whitespace
      .replace(/\s+/g, ' ')
      .trim();
  }, []);

  // Speak text
  const speak = useCallback(
    (text, onEnd) => {
      if (!isSupported || isMuted || !text) {
        return;
      }

      const cleanText = cleanTextForSpeech(text);
      if (!cleanText) return;

      // Always cancel previous speech before beginning a new utterance
      try {
        window.speechSynthesis.cancel();
      } catch {
        // Ignore
      }

      setLastSpokenText(cleanText);

      try {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = Math.max(0.8, Math.min(rate, 1.4));
        utterance.pitch = 1.0;
        utterance.lang = language;

        // Try to select an English voice matching region or natural profile
        const voices = window.speechSynthesis.getVoices();
        if (voices && voices.length > 0) {
          const matchedVoice =
            voices.find((v) => v.lang === language || v.lang === 'en-IN') ||
            voices.find((v) => v.lang.startsWith('en')) ||
            voices[0];
          if (matchedVoice) {
            utterance.voice = matchedVoice;
          }
        }

        utterance.onstart = () => {
          setIsSpeaking(true);
          setIsPaused(false);
        };

        utterance.onend = () => {
          setIsSpeaking(false);
          setIsPaused(false);
          if (onEnd) onEnd();
        };

        utterance.onerror = (event) => {
          // If canceled, ignore; otherwise reset speaking state
          if (event.error !== 'canceled' && event.error !== 'interrupted') {
            console.warn('Speech synthesis error:', event.error);
          }
          setIsSpeaking(false);
          setIsPaused(false);
        };

        currentUtteranceRef.current = utterance;
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn('Could not speak utterance:', err);
        setIsSpeaking(false);
      }
    },
    [isSupported, isMuted, rate, language, cleanTextForSpeech]
  );

  // Replay the most recent response
  const replay = useCallback(() => {
    if (lastSpokenText) {
      speak(lastSpokenText);
    }
  }, [lastSpokenText, speak]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (isSupported) {
        try {
          window.speechSynthesis.cancel();
        } catch {
          // Ignore
        }
      }
    };
  }, [isSupported]);

  return {
    isSpeaking,
    isPaused,
    isMuted,
    isSupported,
    rate,
    lastSpokenText,
    setRate,
    speak,
    stop,
    replay,
    toggleMute,
    cleanTextForSpeech,
  };
};

export default useSpeechSynthesis;
