import api from './api';

export const appointmentService = {
  async bookAppointment(data) {
    const response = await api.post('/appointments', data);
    return response.data;
  },

  async getMyAppointments() {
    const response = await api.get('/appointments/me');
    return response.data;
  },

  async getAppointmentById(id) {
    const response = await api.get(`/appointments/${id}`);
    return response.data;
  },

  async cancelAppointment(id, reason = '') {
    const response = await api.patch(`/appointments/${id}/cancel`, {
      cancellation_reason: reason
    });
    return response.data;
  },

  async rescheduleAppointment(id, newAvailabilityId) {
    const response = await api.patch(`/appointments/${id}/reschedule`, {
      new_availability_id: newAvailabilityId
    });
    return response.data;
  }
};

