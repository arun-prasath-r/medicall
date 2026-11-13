import api from './api';

export const availabilityService = {
  async getDoctorAvailability(doctorId, startDate, endDate, status = 'AVAILABLE') {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (status) params.status = status;

    const response = await api.get(`/doctors/${doctorId}/availability`, { params });
    return response.data;
  },

  async createSlot(doctorId, slotData) {
    const response = await api.post(`/doctors/${doctorId}/availability`, slotData);
    return response.data;
  },

  async generateSlots(doctorId, startDate, endDate) {
    const response = await api.post(`/doctors/${doctorId}/availability/generate`, {
      start_date: startDate,
      end_date: endDate
    });
    return response.data;
  }
};

