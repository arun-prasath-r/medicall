"""
Gemini Function Calling Declarations for Medicall Healthcare Assistant.

Defines the OpenAPI/Gemini function calling schema declarations for:
1. search_doctors
2. get_doctor_availability
3. get_my_appointments
4. book_appointment
5. cancel_appointment
6. reschedule_appointment
"""

from typing import List
from google.genai import types

# 1. Search Doctors Tool
SEARCH_DOCTORS_DECLARATION = types.FunctionDeclaration(
    name="search_doctors",
    description=(
        "Search verified clinic doctors by medical specialty or name. "
        "Returns doctor details including UUID, full name, specialty, experience years, "
        "consultation fee, and clinic location."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "specialty": types.Schema(
                type="STRING",
                description="Medical specialty to filter by (e.g., Cardiology, Dermatology, General Medicine, Pediatrics, Orthopedics, Neurology)."
            ),
            "doctor_name": types.Schema(
                type="STRING",
                description="Doctor's first or last name (or partial name) to filter by."
            )
        }
    )
)

# 2. Get Doctor Availability Tool
GET_DOCTOR_AVAILABILITY_DECLARATION = types.FunctionDeclaration(
    name="get_doctor_availability",
    description=(
        "Retrieve currently available appointment time slots for a specified doctor within "
        "an optional date range. Dates must be formatted as YYYY-MM-DD."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "doctor_id": types.Schema(
                type="STRING",
                description="Unique UUID of the doctor whose schedule is being queried."
            ),
            "date_from": types.Schema(
                type="STRING",
                description="Optional start date in YYYY-MM-DD format (defaults to current date if omitted)."
            ),
            "date_to": types.Schema(
                type="STRING",
                description="Optional end date in YYYY-MM-DD format (e.g., 7 or 14 days from start date)."
            )
        },
        required=["doctor_id"]
    )
)

# 3. Get My Appointments Tool
GET_MY_APPOINTMENTS_DECLARATION = types.FunctionDeclaration(
    name="get_my_appointments",
    description=(
        "Retrieve existing appointment records for the currently authenticated patient. "
        "Returns upcoming and past appointments with reference code, doctor name, specialty, "
        "datetime, status, and chief complaint. Patient identity is securely resolved on the backend."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={}
    )
)

# 4. Book Appointment Tool
BOOK_APPOINTMENT_DECLARATION = types.FunctionDeclaration(
    name="book_appointment",
    description=(
        "Book a medical consultation appointment with a doctor for an available slot. "
        "SAFETY REQUIREMENT: If confirmation_token is omitted, this function returns a confirmation proposal "
        "and a secure confirmation_token. You must present the appointment details to the patient and ask "
        "for their explicit confirmation. When the patient confirms, call this function again with the confirmation_token."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "doctor_id": types.Schema(
                type="STRING",
                description="Unique UUID of the doctor."
            ),
            "availability_id": types.Schema(
                type="STRING",
                description="Unique UUID of the available slot to reserve."
            ),
            "chief_complaint": types.Schema(
                type="STRING",
                description="Patient's primary clinical symptom or reason for visit."
            ),
            "confirmation_token": types.Schema(
                type="STRING",
                description="Optional cryptographically signed confirmation token from an earlier proposal turn. Required to execute transaction."
            )
        },
        required=["doctor_id", "availability_id", "chief_complaint"]
    )
)

# 5. Cancel Appointment Tool
CANCEL_APPOINTMENT_DECLARATION = types.FunctionDeclaration(
    name="cancel_appointment",
    description=(
        "Cancel an active scheduled appointment for the authenticated patient. "
        "SAFETY REQUIREMENT: If confirmation_token is omitted, this function returns a confirmation proposal. "
        "You must ask the patient to confirm cancellation. When confirmed, call this function with the confirmation_token."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "appointment_id": types.Schema(
                type="STRING",
                description="Unique UUID of the appointment to cancel."
            ),
            "reason": types.Schema(
                type="STRING",
                description="Optional reason for appointment cancellation."
            ),
            "confirmation_token": types.Schema(
                type="STRING",
                description="Optional cryptographically signed confirmation token from an earlier proposal turn."
            )
        },
        required=["appointment_id"]
    )
)

# 6. Reschedule Appointment Tool
RESCHEDULE_APPOINTMENT_DECLARATION = types.FunctionDeclaration(
    name="reschedule_appointment",
    description=(
        "Reschedule an active appointment to a new available slot with the same doctor. "
        "SAFETY REQUIREMENT: If confirmation_token is omitted, this function returns a confirmation proposal. "
        "You must ask the patient to confirm rescheduling. When confirmed, call this function with the confirmation_token."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "appointment_id": types.Schema(
                type="STRING",
                description="Unique UUID of the appointment to reschedule."
            ),
            "new_availability_id": types.Schema(
                type="STRING",
                description="Unique UUID of the new available slot."
            ),
            "confirmation_token": types.Schema(
                type="STRING",
                description="Optional cryptographically signed confirmation token from an earlier proposal turn."
            )
        },
        required=["appointment_id", "new_availability_id"]
    )
)

# Bundled list of all declarations
ALL_TOOL_DECLARATIONS: List[types.FunctionDeclaration] = [
    SEARCH_DOCTORS_DECLARATION,
    GET_DOCTOR_AVAILABILITY_DECLARATION,
    GET_MY_APPOINTMENTS_DECLARATION,
    BOOK_APPOINTMENT_DECLARATION,
    CANCEL_APPOINTMENT_DECLARATION,
    RESCHEDULE_APPOINTMENT_DECLARATION,
]

# Google GenAI Tool Object
MEDICALL_GEMINI_TOOL = types.Tool(
    function_declarations=ALL_TOOL_DECLARATIONS
)

