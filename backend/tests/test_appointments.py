import uuid
from datetime import date, time
from app.models.availability import Availability, AvailabilityStatus


def test_appointment_booking_and_concurrency_protection(
    client, sample_patient, sample_doctor, sample_slot, sample_patient_2
):
    """
    Verifies successful appointment booking and ensures that duplicate
    booking of the same slot is strictly rejected with 409 Conflict.
    """
    # Patient 1 login
    login_1 = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token_1 = login_1.json()["access_token"]

    booking_payload = {
        "doctor_id": str(sample_doctor.id),
        "availability_id": str(sample_slot.id),
        "chief_complaint": "Persistent headache and fever for 3 days."
    }

    # First booking attempt -> Success (201 Created)
    response_1 = client.post(
        "/api/v1/appointments",
        json=booking_payload,
        headers={"Authorization": f"Bearer {token_1}"}
    )
    assert response_1.status_code == 201
    appt_data = response_1.json()
    assert appt_data["status"] == "SCHEDULED"
    assert "MED-" in appt_data["appointment_reference"]
    assert appt_data["doctor_name"] == "Dr. Gregory House"

    # Patient 2 attempts to book the EXACT SAME slot -> Must fail with 409 Conflict
    login_2 = client.post("/api/v1/auth/login", json={
        "email": "patient2.test@example.com",
        "password": "Patient2Pass123!"
    })
    token_2 = login_2.json()["access_token"]

    response_2 = client.post(
        "/api/v1/appointments",
        json=booking_payload,
        headers={"Authorization": f"Bearer {token_2}"}
    )
    assert response_2.status_code == 409
    assert "already been reserved" in response_2.json()["detail"].lower()


def test_mismatched_doctor_and_slot_rejected(client, sample_patient, sample_slot):
    """Verifies that requesting a doctor different from the slot's doctor is rejected with 400."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]

    random_doctor_id = str(uuid.uuid4())
    payload = {
        "doctor_id": random_doctor_id,  # Does not match sample_slot.doctor_id
        "availability_id": str(sample_slot.id),
        "chief_complaint": "Mild stomach ache."
    }

    response = client.post(
        "/api/v1/appointments",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"].lower()


def test_appointment_cancellation_and_slot_restoration(
    client, sample_patient, sample_doctor, sample_slot, db_session
):
    """Verifies cancelling an appointment frees the availability slot back to AVAILABLE."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]

    # Book appointment
    book_resp = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(sample_slot.id),
            "chief_complaint": "Flu symptoms."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # Cancel appointment
    cancel_resp = client.patch(
        f"/api/v1/appointments/{appt_id}/cancel",
        json={"cancellation_reason": "Feeling much better."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED_PATIENT"

    # Verify slot is restored to AVAILABLE in database
    db_session.expire_all()
    slot = db_session.query(Availability).filter(Availability.id == sample_slot.id).first()
    assert slot.status == AvailabilityStatus.AVAILABLE


def test_appointment_rescheduling(
    client, sample_patient, sample_doctor, sample_slot, db_session
):
    """Verifies rescheduling releases the old slot and reserves the new slot."""
    # Create second slot
    new_slot = Availability(
        doctor_id=sample_doctor.id,
        slot_date=date(2026, 12, 1),
        start_time=time(11, 0),
        end_time=time(11, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    db_session.add(new_slot)
    db_session.commit()
    db_session.refresh(new_slot)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]

    # Book initial slot
    book_resp = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(sample_slot.id),
            "chief_complaint": "Annual checkup."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    appt_id = book_resp.json()["id"]

    # Reschedule to new_slot
    resched_resp = client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_availability_id": str(new_slot.id)},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resched_resp.status_code == 200
    assert resched_resp.json()["status"] == "RESCHEDULED"

    # Verify old slot is restored and new slot is BOOKED
    db_session.expire_all()
    old_s = db_session.query(Availability).filter(Availability.id == sample_slot.id).first()
    new_s = db_session.query(Availability).filter(Availability.id == new_slot.id).first()
    assert old_s.status == AvailabilityStatus.AVAILABLE
    assert new_s.status == AvailabilityStatus.BOOKED


def test_patient_data_isolation(client, sample_patient, sample_patient_2, sample_doctor, sample_slot):
    """Verifies Patient A cannot view or manipulate Patient B's appointment records (IDOR protection)."""
    # Book appointment as Patient 1
    login_1 = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token_1 = login_1.json()["access_token"]

    book_resp = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(sample_slot.id),
            "chief_complaint": "Personal medical condition."
        },
        headers={"Authorization": f"Bearer {token_1}"}
    )
    appt_id = book_resp.json()["id"]

    # Patient 2 attempts to query Patient 1's appointment
    login_2 = client.post("/api/v1/auth/login", json={
        "email": "patient2.test@example.com",
        "password": "Patient2Pass123!"
    })
    token_2 = login_2.json()["access_token"]

    get_resp = client.get(
        f"/api/v1/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {token_2}"}
    )
    assert get_resp.status_code == 403
    assert "Access denied" in get_resp.json()["detail"]

    # Patient 2 attempts to cancel Patient 1's appointment
    cancel_resp = client.patch(
        f"/api/v1/appointments/{appt_id}/cancel",
        json={"cancellation_reason": "Malicious cancellation attempt"},
        headers={"Authorization": f"Bearer {token_2}"}
    )
    assert cancel_resp.status_code == 403
    assert "Access denied" in cancel_resp.json()["detail"]

