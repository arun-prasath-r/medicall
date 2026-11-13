"""
Doctor lookup and availability inspection tools for Gemini AI.

Strictly reuses existing DoctorService and AvailabilityService.
Gemini NEVER accesses PostgreSQL directly.
"""

import logging
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.availability import AvailabilityStatus
from app.models.doctor import Doctor
from app.services.availability_service import AvailabilityService
from app.services.doctor_service import DoctorService

logger = logging.getLogger(__name__)


def execute_search_doctors(
    db: Session,
    specialty: Optional[str] = None,
    doctor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search verified clinic doctors accepting patients by medical specialty or name.
    """
    try:
        clean_specialty = specialty.strip() if specialty else None
        doctors = DoctorService.list_doctors(
            db=db,
            specialty=clean_specialty,
            is_accepting_patients=True,
            limit=20
        )

        # Filter strictly for verified doctors
        verified_doctors = [
            doc for doc in doctors
            if doc.user and doc.user.is_verified
        ]

        # Filter by name if provided
        if doctor_name and doctor_name.strip():
            name_term = doctor_name.strip().lower()
            filtered = []
            for doc in verified_doctors:
                full_name = f"{doc.first_name} {doc.last_name}".lower()
                prefixed = f"dr. {full_name}".lower()
                if (name_term in full_name or
                    name_term in prefixed or
                    name_term in doc.first_name.lower() or
                    name_term in doc.last_name.lower()):
                    filtered.append(doc)
            verified_doctors = filtered

        result_list = [
            {
                "id": str(doc.id),
                "name": f"Dr. {doc.first_name} {doc.last_name}",
                "specialty": doc.specialty,
                "qualifications": doc.qualifications,
                "experience_years": doc.experience_years,
                "consultation_fee": float(doc.consultation_fee),
                "clinic_address": doc.clinic_address or "Main Clinic Campus",
                "is_accepting_patients": doc.is_accepting_patients,
            }
            for doc in verified_doctors
        ]

        return {
            "success": True,
            "total_found": len(result_list),
            "doctors": result_list,
            "message": f"Found {len(result_list)} verified doctor(s)." if result_list else "No matching verified doctors found."
        }

    except Exception as e:
        logger.error("Error executing search_doctors: %s", str(e))
        return {
            "success": False,
            "error": "Failed to search doctors. Please try again."
        }


def execute_get_doctor_availability(
    db: Session,
    doctor_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve active available slots for a specified doctor.
    """
    try:
        try:
            doc_uuid = uuid.UUID(doctor_id.strip())
        except (ValueError, AttributeError):
            return {
                "success": False,
                "error": f"Invalid doctor_id format: '{doctor_id}'. Must be a valid UUID."
            }

        doctor = db.query(Doctor).filter(Doctor.id == doc_uuid).first()
        if not doctor:
            return {
                "success": False,
                "error": f"Doctor with ID {doctor_id} not found."
            }

        if not doctor.user or not doctor.user.is_verified:
            return {
                "success": False,
                "error": "The specified doctor is not yet verified for consultations."
            }

        # Parse date range
        start_d: Optional[date] = None
        end_d: Optional[date] = None

        if date_from:
            try:
                start_d = datetime.strptime(date_from.strip(), "%Y-%m-%d").date()
            except ValueError:
                return {"success": False, "error": f"Invalid date_from format: '{date_from}'. Use YYYY-MM-DD."}
        else:
            start_d = date.today()

        if date_to:
            try:
                end_d = datetime.strptime(date_to.strip(), "%Y-%m-%d").date()
            except ValueError:
                return {"success": False, "error": f"Invalid date_to format: '{date_to}'. Use YYYY-MM-DD."}

        slots = AvailabilityService.get_doctor_availability(
            db=db,
            doctor_id=doc_uuid,
            start_date=start_d,
            end_date=end_d,
            slot_status=AvailabilityStatus.AVAILABLE
        )

        formatted_slots = [
            {
                "slot_id": str(slot.id),
                "date": slot.slot_date.isoformat(),
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "status": slot.status.value
            }
            for slot in slots
        ]

        return {
            "success": True,
            "doctor_id": str(doctor.id),
            "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}",
            "specialty": doctor.specialty,
            "consultation_fee": float(doctor.consultation_fee),
            "available_slots_count": len(formatted_slots),
            "slots": formatted_slots,
            "message": f"Found {len(formatted_slots)} available slot(s)." if formatted_slots else "No available slots in the requested period."
        }

    except Exception as e:
        logger.error("Error executing get_doctor_availability: %s", str(e))
        return {
            "success": False,
            "error": "Failed to retrieve doctor availability."
        }

