import api from './api';

export const adminService = {
  async getPendingDoctors() {
    const response = await api.get('/admin/doctors/pending');
    return response.data;
  },

  async getAllDoctors() {
    const response = await api.get('/admin/doctors');
    return response.data;
  },

  async verifyDoctor(doctorId) {
    const response = await api.patch(`/admin/doctors/${doctorId}/verify`);
    return response.data;
  }
};

