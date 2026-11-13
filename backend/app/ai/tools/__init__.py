"""
Gemini Function Calling Tools Package for Medicall.
"""

from app.ai.tools.declarations import (
    ALL_TOOL_DECLARATIONS,
    BOOK_APPOINTMENT_DECLARATION,
    CANCEL_APPOINTMENT_DECLARATION,
    GET_DOCTOR_AVAILABILITY_DECLARATION,
    GET_MY_APPOINTMENTS_DECLARATION,
    MEDICALL_GEMINI_TOOL,
    RESCHEDULE_APPOINTMENT_DECLARATION,
    SEARCH_DOCTORS_DECLARATION,
)
from app.ai.tools.dispatcher import ToolDispatcher
from app.ai.tools.confirmation import (
    ConfirmationError,
    generate_confirmation_token,
    verify_confirmation_token,
)
from app.ai.tools.doctor_tools import (
    execute_get_doctor_availability,
    execute_search_doctors,
)
from app.ai.tools.appointment_tools import (
    execute_book_appointment,
    execute_cancel_appointment,
    execute_get_my_appointments,
    execute_reschedule_appointment,
)

__all__ = [
    "ALL_TOOL_DECLARATIONS",
    "MEDICALL_GEMINI_TOOL",
    "SEARCH_DOCTORS_DECLARATION",
    "GET_DOCTOR_AVAILABILITY_DECLARATION",
    "GET_MY_APPOINTMENTS_DECLARATION",
    "BOOK_APPOINTMENT_DECLARATION",
    "CANCEL_APPOINTMENT_DECLARATION",
    "RESCHEDULE_APPOINTMENT_DECLARATION",
    "ToolDispatcher",
    "ConfirmationError",
    "generate_confirmation_token",
    "verify_confirmation_token",
    "execute_search_doctors",
    "execute_get_doctor_availability",
    "execute_get_my_appointments",
    "execute_book_appointment",
    "execute_cancel_appointment",
    "execute_reschedule_appointment",
]

