import api from './api';

export const patientService = {
  async getProfile() {
    const response = await api.get('/patients/me');
    return response.data;
  },

  async updateProfile(data) {
    const response = await api.put('/patients/me', data);
    return response.data;
  },

  async recordConsent(consentData = {
    agreed_to_terms: true,
    agreed_to_voice_processing: true,
    agreed_to_non_diagnostic_scope: true
  }) {
    const response = await api.post('/patients/consent', consentData);
    return response.data;
  }
};

