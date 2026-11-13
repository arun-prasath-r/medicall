import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert';
import { aiService } from './aiService.js';
import api from './api.js';

describe('aiService Frontend Service Unit Tests', () => {
  let mockPostCalls = [];
  let mockGetCalls = [];
  let originalPost;
  let originalGet;

  beforeEach(() => {
    mockPostCalls = [];
    mockGetCalls = [];
    originalPost = api.post;
    originalGet = api.get;
  });

  const restoreApi = () => {
    api.post = originalPost;
    api.get = originalGet;
  };

  it('should reject empty or whitespace message in sendChatMessage', async () => {
    await assert.rejects(
      async () => {
        await aiService.sendChatMessage({ message: '   ' });
      },
      {
        name: 'Error',
        message: 'Message cannot be empty.',
      }
    );
  });

  it('should send correctly structured payload with history and confirmation token to /ai/chat', async () => {
    api.post = async (url, data, config) => {
      mockPostCalls.push({ url, data, config });
      return {
        data: {
          response: 'I found an appointment with Dr. John Smith.',
          urgency_level: 'ROUTINE',
          is_emergency: false,
          pending_confirmation: {
            requires_confirmation: true,
            action: 'book_appointment',
            confirmation_token: 'mock-token-xyz',
          },
          success: true,
        },
      };
    };

    try {
      const history = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there!' },
      ];
      const res = await aiService.sendChatMessage({
        message: 'Book Dr. Smith',
        conversationHistory: history,
        confirmationToken: 'active-token-123',
      });

      assert.strictEqual(mockPostCalls.length, 1);
      const call = mockPostCalls[0];
      assert.strictEqual(call.url, '/ai/chat');
      assert.strictEqual(call.data.message, 'Book Dr. Smith');
      assert.strictEqual(call.data.confirmation_token, 'active-token-123');
      assert.strictEqual(call.data.conversation_history.length, 2);
      assert.strictEqual(call.config.timeout, 35000);
      assert.strictEqual(res.success, true);
      assert.strictEqual(res.pending_confirmation.action, 'book_appointment');
    } finally {
      restoreApi();
    }
  });

  it('should slice conversation history to 10 items max', async () => {
    api.post = async (url, data) => {
      mockPostCalls.push({ url, data });
      return { data: { success: true, response: 'OK' } };
    };

    try {
      const longHistory = Array.from({ length: 15 }, (_, i) => ({
        role: i % 2 === 0 ? 'user' : 'assistant',
        content: `Message ${i}`,
      }));

      await aiService.sendChatMessage({
        message: 'Latest inquiry',
        conversationHistory: longHistory,
      });

      assert.strictEqual(mockPostCalls.length, 1);
      assert.strictEqual(mockPostCalls[0].data.conversation_history.length, 10);
      assert.strictEqual(mockPostCalls[0].data.conversation_history[9].content, 'Message 14');
    } finally {
      restoreApi();
    }
  });

  it('should format backend API error cleanly on /ai/chat failure', async () => {
    api.post = async () => {
      const error = new Error('Request failed with status code 503');
      error.response = {
        status: 503,
        data: {
          detail: 'Google Gemini AI service is currently experiencing high demand.',
        },
      };
      throw error;
    };

    try {
      await assert.rejects(
        async () => {
          await aiService.sendChatMessage({ message: 'Any doctors?' });
        },
        (err) => {
          assert.match(err.message, /Google Gemini AI service/);
          return true;
        }
      );
    } finally {
      restoreApi();
    }
  });

  it('should reject confirmAction if confirmationToken is empty or missing', async () => {
    await assert.rejects(
      async () => {
        await aiService.confirmAction({ confirmationToken: '' });
      },
      {
        name: 'Error',
        message: 'A valid confirmation token is required.',
      }
    );
  });

  it('should post confirmation token to /ai/confirm successfully', async () => {
    api.post = async (url, data) => {
      mockPostCalls.push({ url, data });
      return {
        data: {
          success: true,
          action: 'book_appointment',
          reference_code: 'MED-AI-999',
          message: 'Appointment successfully confirmed and booked!',
        },
      };
    };

    try {
      const res = await aiService.confirmAction({
        confirmationToken: 'valid-jwt-token-777',
      });

      assert.strictEqual(mockPostCalls.length, 1);
      assert.strictEqual(mockPostCalls[0].url, '/ai/confirm');
      assert.strictEqual(mockPostCalls[0].data.confirmation_token, 'valid-jwt-token-777');
      assert.strictEqual(res.success, true);
      assert.strictEqual(res.reference_code, 'MED-AI-999');
    } finally {
      restoreApi();
    }
  });

  it('should format token replay error from backend on confirmAction', async () => {
    api.post = async () => {
      const error = new Error('Bad Request');
      error.response = {
        status: 400,
        data: {
          detail: 'Confirmation token has already been used. Tokens are strictly single-use to prevent replay.',
        },
      };
      throw error;
    };

    try {
      await assert.rejects(
        async () => {
          await aiService.confirmAction({ confirmationToken: 'already-used-token' });
        },
        (err) => {
          assert.match(err.message, /Confirmation token has already been used/);
          return true;
        }
      );
    } finally {
      restoreApi();
    }
  });

  it('should inspect AI status via getAiStatus', async () => {
    api.get = async (url) => {
      mockGetCalls.push({ url });
      return {
        data: {
          status: 'available',
          configured: true,
          model: 'gemini-3.5-flash',
        },
      };
    };

    try {
      const res = await aiService.getAiStatus();
      assert.strictEqual(mockGetCalls.length, 1);
      assert.strictEqual(mockGetCalls[0].url, '/ai/status');
      assert.strictEqual(res.status, 'available');
      assert.strictEqual(res.configured, true);
    } finally {
      restoreApi();
    }
  });
});

