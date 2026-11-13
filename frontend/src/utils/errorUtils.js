/**
 * Medicall Error Handling Utility
 * Guarantees that API errors (especially FastAPI 422 validation detail arrays)
 * are NEVER rendered as raw JavaScript objects in React children, preventing React crash.
 */

/**
 * Extracts a human-readable, safe error message string from any API error.
 * 
 * @param {any} error - The caught error object, Axios error, or string
 * @param {string} [fallbackMessage] - Fallback message if error details cannot be parsed
 * @returns {string} Human-readable error message guaranteed to be a string
 */
export const formatApiError = (
  error,
  fallbackMessage = 'An unexpected error occurred. Please try again.'
) => {
  if (!error) return fallbackMessage;

  // 1. If error is already a string
  if (typeof error === 'string') {
    return error.trim() || fallbackMessage;
  }

  // 2. Inspect Axios response payload
  if (error.response && error.response.data) {
    const data = error.response.data;

    // A. FastAPI detail field
    if (data.detail !== undefined && data.detail !== null) {
      // If detail is a simple string (e.g. HTTPException(400, "Slot already booked"))
      if (typeof data.detail === 'string') {
        return data.detail.trim() || fallbackMessage;
      }

      // If detail is an array (FastAPI 422 validation error list: [{ loc, msg, type, ... }])
      if (Array.isArray(data.detail)) {
        if (data.detail.length === 0) return fallbackMessage;

        const messages = data.detail
          .map((item) => {
            if (!item) return null;
            if (typeof item === 'string') return item;
            if (typeof item === 'object') {
              // Extract field name from loc array: e.g. ["body", "chief_complaint"] -> "Chief complaint"
              let fieldName = '';
              if (Array.isArray(item.loc) && item.loc.length > 0) {
                const rawField = String(item.loc[item.loc.length - 1]);
                if (rawField && rawField !== 'body') {
                  fieldName = rawField
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, (c) => c.toUpperCase());
                }
              }

              let msg = item.msg || item.message || '';
              // Clean common pydantic messages
              if (msg.includes('Field required')) {
                return fieldName ? `Please provide ${fieldName.toLowerCase()}.` : 'Required field missing.';
              }
              if (msg.includes('at least 3 characters')) {
                return `${fieldName || 'Chief complaint'} must be at least 3 characters long.`;
              }

              return fieldName ? `${fieldName}: ${msg}` : msg;
            }
            return String(item);
          })
          .filter(Boolean);

        if (messages.length > 0) {
          return messages.join('. ');
        }
      }

      // If detail is a single dictionary/object
      if (typeof data.detail === 'object') {
        if (data.detail.msg && typeof data.detail.msg === 'string') {
          return data.detail.msg;
        }
        if (data.detail.message && typeof data.detail.message === 'string') {
          return data.detail.message;
        }
      }
    }

    // B. Direct 'message' field
    if (typeof data.message === 'string' && data.message.trim()) {
      return data.message.trim();
    }
  }

  // 3. Status code defaults if data.detail was missing
  if (error.response && error.response.status) {
    switch (error.response.status) {
      case 400:
        return 'Invalid request details. Please check the information provided.';
      case 401:
        return 'Your session has expired or you are not authorized. Please sign in again.';
      case 403:
        return 'You do not have permission to perform this medical action.';
      case 404:
        return 'The requested healthcare record or consultation slot could not be found.';
      case 409:
        return 'This consultation slot has just been reserved by another patient. Please choose an alternative time.';
      case 422:
        return 'Please verify that all consultation details and required fields are properly filled.';
      case 500:
        return 'A clinical server error occurred. Our team has been notified. Please try again shortly.';
      default:
        break;
    }
  }

  // 4. Client / Network errors
  if (error.message) {
    if (error.message.includes('Network Error')) {
      return 'Unable to communicate with the Medicall server. Please verify your internet connection.';
    }
    if (error.message.includes('timeout')) {
      return 'The request timed out. Please check your network and try again.';
    }
    return String(error.message);
  }

  return fallbackMessage;
};

/**
 * Extracts validation message for a specific field from FastAPI 422 errors.
 * 
 * @param {any} error 
 * @param {string} fieldName 
 * @returns {string|null}
 */
export const getFieldError = (error, fieldName) => {
  if (
    error &&
    error.response &&
    error.response.data &&
    Array.isArray(error.response.data.detail)
  ) {
    const match = error.response.data.detail.find(
      (item) =>
        item &&
        Array.isArray(item.loc) &&
        item.loc.some((l) => String(l).toLowerCase() === fieldName.toLowerCase())
    );
    if (match) {
      return match.msg || match.message || 'Invalid value.';
    }
  }
  return null;
};

