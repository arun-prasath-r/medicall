"""
Central tool dispatcher for Gemini AI function calling.

Resolves tool names, performs argument validation, injects active database session
and verified current_user context, and returns sanitized structured responses.
"""

import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.user import User
from app.ai.tools.doctor_tools import (
    execute_search_doctors,
    execute_get_doctor_availability,
)
from app.ai.tools.appointment_tools import (
    execute_get_my_appointments,
    execute_book_appointment,
    execute_cancel_appointment,
    execute_reschedule_appointment,
)

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """
    Central dispatcher for Gemini function calling in Medicall.
    Safely executes tool calls with database session and authenticated patient context.
    """

    @classmethod
    def dispatch(
        cls,
        name: str,
        arguments: Dict[str, Any],
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Dispatches a Gemini function call to the corresponding backend service handler.
        """
        logger.info("Executing Gemini tool '%s' for user %s", name, getattr(current_user, "id", "anonymous"))
        args = arguments or {}

        try:
            if name == "search_doctors":
                return execute_search_doctors(
                    db=db,
                    specialty=args.get("specialty"),
                    doctor_name=args.get("doctor_name")
                )

            elif name == "get_doctor_availability":
                doctor_id = args.get("doctor_id")
                if not doctor_id:
                    return {"success": False, "error": "Missing required parameter: doctor_id"}
                return execute_get_doctor_availability(
                    db=db,
                    doctor_id=str(doctor_id),
                    date_from=args.get("date_from"),
                    date_to=args.get("date_to")
                )

            elif name == "get_my_appointments":
                return execute_get_my_appointments(
                    db=db,
                    current_user=current_user
                )

            elif name == "book_appointment":
                doctor_id = args.get("doctor_id")
                availability_id = args.get("availability_id")
                chief_complaint = args.get("chief_complaint")
                if not doctor_id or not availability_id or not chief_complaint:
                    return {
                        "success": False,
                        "error": "Missing required parameters: doctor_id, availability_id, and chief_complaint are all required."
                    }
                return execute_book_appointment(
                    db=db,
                    current_user=current_user,
                    doctor_id=str(doctor_id),
                    availability_id=str(availability_id),
                    chief_complaint=str(chief_complaint),
                    confirmation_token=args.get("confirmation_token")
                )

            elif name == "cancel_appointment":
                appointment_id = args.get("appointment_id")
                if not appointment_id:
                    return {"success": False, "error": "Missing required parameter: appointment_id"}
                return execute_cancel_appointment(
                    db=db,
                    current_user=current_user,
                    appointment_id=str(appointment_id),
                    reason=args.get("reason"),
                    confirmation_token=args.get("confirmation_token")
                )

            elif name == "reschedule_appointment":
                appointment_id = args.get("appointment_id")
                new_availability_id = args.get("new_availability_id")
                if not appointment_id or not new_availability_id:
                    return {
                        "success": False,
                        "error": "Missing required parameters: appointment_id and new_availability_id are required."
                    }
                return execute_reschedule_appointment(
                    db=db,
                    current_user=current_user,
                    appointment_id=str(appointment_id),
                    new_availability_id=str(new_availability_id),
                    confirmation_token=args.get("confirmation_token")
                )

            else:
                logger.warning("Unrecognized tool name requested by Gemini: %s", name)
                return {
                    "success": False,
                    "error": (
                        f"Unknown tool '{name}'. Available tools: search_doctors, "
                        "get_doctor_availability, get_my_appointments, book_appointment, "
                        "cancel_appointment, reschedule_appointment."
                    )
                }

        except Exception as e:
            logger.error("Unhandled error dispatching tool '%s': %s", name, str(e), exc_info=True)
            return {
                "success": False,
                "error": f"Internal execution error processing tool '{name}'."
            }

