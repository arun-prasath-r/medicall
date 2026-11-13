import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from app.models.availability import Availability, AvailabilityStatus
from app.models.appointment import Appointment, AppointmentStatus


def test_reschedule_already_rescheduled_appointment_allowed(
    client, sample_patient, sample_doctor, sample_slot, db_session
):
    """
    Verifies that a patient can reschedule an appointment that has previously
    been rescheduled (status=RESCHEDULED), maintaining clinical scheduling flexibility.
    """
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create slot 2 and slot 3 for the doctor
    tomorrow = date.today() + timedelta(days=1)
    slot_2 = Availability(
        doctor_id=sample_doctor.id,
        slot_date=tomorrow,
        start_time=datetime.strptime("11:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("11:30:00", "%H:%M:%S").time(),
        status=AvailabilityStatus.AVAILABLE
    )
    day_after = date.today() + timedelta(days=2)
    slot_3 = Availability(
        doctor_id=sample_doctor.id,
        slot_date=day_after,
        start_time=datetime.strptime("15:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("15:30:00", "%H:%M:%S").time(),
        status=AvailabilityStatus.AVAILABLE
    )
    db_session.add_all([slot_2, slot_3])
    db_session.commit()
    db_session.refresh(slot_2)
    db_session.refresh(slot_3)

    # 1. Initial Booking
    book_resp = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(sample_slot.id),
            "chief_complaint": "Persistent migraines."
        },
        headers=headers
    )
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # 2. First Reschedule -> status becomes RESCHEDULED
    resched_1 = client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_availability_id": str(slot_2.id)},
        headers=headers
    )
    assert resched_1.status_code == 200
    assert resched_1.json()["status"] == "RESCHEDULED"
    assert resched_1.json()["availability_id"] == str(slot_2.id)

    # 3. Second Reschedule from RESCHEDULED status -> should SUCCEED
    resched_2 = client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_availability_id": str(slot_3.id)},
        headers=headers
    )
    assert resched_2.status_code == 200
    assert resched_2.json()["status"] == "RESCHEDULED"
    assert resched_2.json()["availability_id"] == str(slot_3.id)

    # Verify slot_2 was released back to AVAILABLE
    db_session.refresh(slot_2)
    assert slot_2.status == AvailabilityStatus.AVAILABLE

    # Verify slot_3 is now BOOKED
    db_session.refresh(slot_3)
    assert slot_3.status == AvailabilityStatus.BOOKED


def test_reschedule_to_same_slot_rejected(
    client, sample_patient, sample_doctor, sample_slot, db_session
):
    """
    Verifies that attempting to reschedule to the same slot returns 400 Bad Request.
    """
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Book initial slot
    book_resp = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(sample_slot.id),
            "chief_complaint": "General consultation."
        },
        headers=headers
    )
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # Attempt to reschedule to the exact same slot
    resched_resp = client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_availability_id": str(sample_slot.id)},
        headers=headers
    )
    assert resched_resp.status_code == 400
    assert "already scheduled for this slot" in resched_resp.json()["detail"].lower()

