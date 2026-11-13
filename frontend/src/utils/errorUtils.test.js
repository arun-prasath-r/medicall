import { describe, it } from 'node:test';
import assert from 'node:assert';
import { formatApiError, getFieldError } from './errorUtils.js';

describe('formatApiError Tests', () => {
  it('should return simple string error intact', () => {
    const result = formatApiError('Invalid credentials');
    assert.strictEqual(result, 'Invalid credentials');
  });

  it('should return fallback message when error is undefined', () => {
    const result = formatApiError(undefined, 'Fallback error');
    assert.strictEqual(result, 'Fallback error');
  });

  it('should format simple FastAPI HTTPException string detail', () => {
    const err = {
      response: {
        status: 400,
        data: {
          detail: 'The requested appointment slot has already been reserved or is unavailable.'
        }
      }
    };
    const result = formatApiError(err);
    assert.strictEqual(result, 'The requested appointment slot has already been reserved or is unavailable.');
  });

  it('CRITICAL BUG FIX: should format FastAPI 422 validation array of objects into a safe string, NOT an object', () => {
    const err = {
      response: {
        status: 422,
        data: {
          detail: [
            {
              type: 'missing',
              loc: ['body', 'availability_id'],
              msg: 'Field required',
              input: null,
              ctx: {}
            },
            {
              type: 'string_too_short',
              loc: ['body', 'chief_complaint'],
              msg: 'String should have at least 3 characters',
              input: 'ab',
              ctx: { min_length: 3 }
            }
          ]
        }
      }
    };

    const result = formatApiError(err);
    assert.strictEqual(typeof result, 'string');
    assert(result.includes('availability id') || result.includes('Availability id'));
    assert(result.includes('at least 3 characters'));
    // Ensure it NEVER returns an object or array
    assert.notStrictEqual(typeof result, 'object');
  });

  it('should handle Network Error cleanly', () => {
    const err = new Error('Network Error');
    const result = formatApiError(err);
    assert.strictEqual(typeof result, 'string');
    assert(result.includes('Unable to communicate with the Medicall server'));
  });

  it('should extract specific field error using getFieldError', () => {
    const err = {
      response: {
        status: 422,
        data: {
          detail: [
            {
              type: 'string_too_short',
              loc: ['body', 'chief_complaint'],
              msg: 'String should have at least 3 characters'
            }
          ]
        }
      }
    };

    const msg = getFieldError(err, 'chief_complaint');
    assert.strictEqual(msg, 'String should have at least 3 characters');

    const nonExistent = getFieldError(err, 'email');
    assert.strictEqual(nonExistent, null);
  });
});

