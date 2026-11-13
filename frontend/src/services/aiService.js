import api from './api.js';
import { formatApiError } from '../utils/errorUtils.js';

/**
 * AI Service for Medicall Voice & Text Clinical Assistant.
 * Connects to FastAPI backend endpoints:
 * - POST /api/v1/ai/chat (Conversational triage with Gemini function-calling)
 * - POST /api/v1/ai/confirm (Deterministic execution of confirmed write proposals)
 * - GET  /api/v1/ai/status (Provider health & model readiness inspection)
 */
export const aiService = {
  /**
   * Send a clinical inquiry or conversational message to the Gemini AI assistant.
   *
   * @param {Object} params
   * @param {string} params.message - The patient message (voice transcript or text input).
   * @param {Array<{role: string, content: string}>} [params.conversationHistory=[]] - Recent conversation turns.
   * @param {string|null} [params.confirmationToken=null] - Optional confirmation token if confirming via chat.
   * @returns {Promise<Object>} AIChatResponse from backend.
   */
  async sendChatMessage({ message, conversationHistory = [], confirmationToken = null }) {
    if (!message || !message.trim()) {
      throw new Error('Message cannot be empty.');
    }

    // Limit conversation history to the most recent 10 turns as required by the backend schema
    const formattedHistory = Array.isArray(conversationHistory)
      ? conversationHistory.slice(-10).map((turn) => ({
          role: turn.role === 'assistant' ? 'assistant' : 'user',
          content: String(turn.content || '').trim(),
        })).filter((turn) => turn.content.length > 0)
      : [];

    const payload = {
      message: message.trim(),
      conversation_history: formattedHistory.length > 0 ? formattedHistory : null,
      confirmation_token: confirmationToken || null,
    };

    try {
      // Allow up to 35 seconds for complex multi-turn function calling & model fallbacks
      const response = await api.post('/ai/chat', payload, {
        timeout: 35000,
      });
      return response.data;
    } catch (error) {
      const formatted = formatApiError(error);
      throw new Error(formatted);
    }
  },

  /**
   * Deterministically confirm and commit a pending write operation (book, cancel, reschedule).
   *
   * @param {Object} params
   * @param {string} params.confirmationToken - The cryptographic token received in pending_confirmation.
   * @returns {Promise<Object>} AIConfirmActionResponse.
   */
  async confirmAction({ confirmationToken }) {
    if (!confirmationToken || !confirmationToken.trim()) {
      throw new Error('A valid confirmation token is required.');
    }

    try {
      const response = await api.post(
        '/ai/confirm',
        { confirmation_token: confirmationToken.trim() },
        { timeout: 20000 }
      );
      return response.data;
    } catch (error) {
      const formatted = formatApiError(error);
      throw new Error(formatted);
    }
  },

  /**
   * Check connection and operational status of the Google Gemini AI provider.
   *
   * @returns {Promise<Object>} Status object.
   */
  async getAiStatus() {
    try {
      const response = await api.get('/ai/status', { timeout: 10000 });
      return response.data;
    } catch (error) {
      const formatted = formatApiError(error);
      throw new Error(formatted);
    }
  },
};

export default aiService;
