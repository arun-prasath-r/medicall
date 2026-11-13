import api from './api';

export const doctorService = {
  async getDoctors(params = {}) {
    const response = await api.get('/doctors', { params });
    return response.data;
  },

  async getDoctorById(id) {
    const response = await api.get(`/doctors/${id}`);
    return response.data;
  },

  async getSpecialties() {
    const response = await api.get('/doctors/specialties');
    return response.data;
  },

  async getDoctorSchedules(id) {
    const response = await api.get(`/doctors/${id}/schedules`);
    return response.data;
  },

  async addDoctorSchedule(id, scheduleData) {
    const response = await api.post(`/doctors/${id}/schedules`, scheduleData);
    return response.data;
  }
};

