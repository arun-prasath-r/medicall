import api from './api';

export const authService = {
  async register(registrationData) {
    const response = await api.post('/auth/register', registrationData);
    return response.data;
  },

  async login(email, password) {
    const response = await api.post('/auth/login', { email, password });
    if (response.data.access_token) {
      localStorage.setItem('medicall_token', response.data.access_token);
      localStorage.setItem('medicall_user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  async getMe() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('medicall_token');
    localStorage.removeItem('medicall_user');
  },

  getCurrentStoredUser() {
    try {
      const userStr = localStorage.getItem('medicall_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    return !!localStorage.getItem('medicall_token');
  }
};

