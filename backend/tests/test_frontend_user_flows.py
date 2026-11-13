import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.user import User, UserRole


def test_complete_frontend_user_flows_and_api_contracts(client: TestClient, db_session: Session):
    """
    Simulates the exact end-to-end API workflows and payloads used by the Medicall React frontend:
    1. Admin user seeding & Admin Login
    2. Patient Registration & Login
    3. Doctor Registration (Unverified State)
    4. Admin Doctor Verification Flow
    5. Doctor Schedule Creation & Slot Generation
    6. Patient Doctor Directory Search & Filtering
    7. Patient Slot Booking (with 409 Race Condition Handling)
    8. Patient Appointment Rescheduling
    9. Patient Appointment Cancellation
    """
    timestamp = uuid.uuid4().hex[:8]

    # --- Step 0: Admin Account Setup ---
    admin_email = f"admin_{timestamp}@example.com"
    admin_user = User(
        email=admin_email,
        hashed_password=hash_password("AdminSecure123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(admin_user)
    db_session.commit()

    admin_login_resp = client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": "AdminSecure123!"
    })
    assert admin_login_resp.status_code == 200
    admin_token = admin_login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # --- Step 1: Patient Registration ---
    patient_email = f"patient_{timestamp}@example.com"
    patient_reg_payload = {
        "email": patient_email,
        "password": "SecurePassword123!",
        "role": "PATIENT",
        "first_name": "Eleanor",
        "last_name": "Vance",
        "phone_number": "+15550192834",
        "date_of_birth": "1992-06-15",
        "gender": "Female",
        "blood_group": "A+",
        "allergies": "Penicillin",
    }
    reg_resp = client.post("/api/v1/auth/register", json=patient_reg_payload)
    assert reg_resp.status_code == 201, reg_resp.text
    patient_reg_data = reg_resp.json()
    assert patient_reg_data["email"] == patient_email
    assert patient_reg_data["role"] == "PATIENT"

    # Patient Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": patient_email,
        "password": "SecurePassword123!"
    })
    assert login_resp.status_code == 200
    patient_token = login_resp.json()["access_token"]
    patient_user = login_resp.json()["user"]
    assert patient_user["first_name"] == "Eleanor"
    assert patient_user["last_name"] == "Vance"
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # Verify Patient /auth/me
    me_resp = client.get("/api/v1/auth/me", headers=patient_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == patient_email

    # --- Step 2: Doctor Registration ---
    doctor_email = f"dr_{timestamp}@example.com"
    doctor_reg_payload = {
        "email": doctor_email,
        "password": "DoctorSecure123!",
        "role": "DOCTOR",
        "first_name": "Arthur",
        "last_name": "Conan",
        "phone_number": "+15550987654",
        "license_number": f"MD-{timestamp.upper()}",
        "specialty": "Cardiology",
        "qualifications": "MD, FACC, Harvard Medical School",
        "experience_years": 14,
        "consultation_fee": 150.00,
        "clinic_address": "742 Evergreen Terrace, Suite 300",
        "bio": "Experienced cardiologist specializing in preventive cardiology."
    }
    doc_reg_resp = client.post("/api/v1/auth/register", json=doctor_reg_payload)
    assert doc_reg_resp.status_code == 201
    doctor_id = doc_reg_resp.json()["profile_id"]

    # Unverified doctor cannot be booked yet
    doc_login_resp = client.post("/api/v1/auth/login", json={
        "email": doctor_email,
        "password": "DoctorSecure123!"
    })
    assert doc_login_resp.status_code == 200
    doctor_token = doc_login_resp.json()["access_token"]
    doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
    doctor_user = doc_login_resp.json()["user"]
    assert doctor_user["is_verified"] is False
    assert doctor_user["first_name"] == "Arthur"

    # --- Step 3: Admin Doctor Verification ---
    # Check pending list
    pending_resp = client.get("/api/v1/admin/doctors/pending", headers=admin_headers)
    assert pending_resp.status_code == 200
    pending_ids = [d["id"] for d in pending_resp.json()]
    assert doctor_id in pending_ids

    # Approve Doctor
    verify_resp = client.patch(f"/api/v1/admin/doctors/{doctor_id}/verify", headers=admin_headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_verified"] is True

    # --- Step 4: Doctor Schedule Creation & Slot Generation ---
    today = date.today()
    day_of_week = today.weekday()

    sched_payload = {
        "day_of_week": day_of_week,
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "slot_duration_minutes": 30,
        "is_active": True
    }
    add_sched_resp = client.post(
        f"/api/v1/doctors/{doctor_id}/schedules",
        json=sched_payload,
        headers=doctor_headers
    )
    assert add_sched_resp.status_code == 201

    # Generate slots for today
    gen_resp = client.post(
        f"/api/v1/doctors/{doctor_id}/availability/generate",
        json={
            "start_date": today.isoformat(),
            "end_date": today.isoformat()
        },
        headers=doctor_headers
    )
    assert gen_resp.status_code in (200, 201)
    generated_slots = gen_resp.json()
    assert len(generated_slots) >= 4  # 9:00, 9:30, 10:00, 10:30

    # Also add a manual discrete slot for tomorrow
    tomorrow = today + timedelta(days=1)
    manual_slot_resp = client.post(
        f"/api/v1/doctors/{doctor_id}/availability",
        json={
            "slot_date": tomorrow.isoformat(),
            "start_time": "14:00:00",
            "end_time": "14:30:00",
            "status": "AVAILABLE"
        },
        headers=doctor_headers
    )
    assert manual_slot_resp.status_code == 201
    manual_slot = manual_slot_resp.json()

    # --- Step 5: Patient Doctor Directory Search & Filtering ---
    # Filter by specialty
    dir_resp = client.get("/api/v1/doctors?specialty=Cardiology")
    assert dir_resp.status_code == 200
    cardiologists = dir_resp.json()
    assert any(d["id"] == doctor_id for d in cardiologists)

    # Doctor Detail
    doc_detail_resp = client.get(f"/api/v1/doctors/{doctor_id}")
    assert doc_detail_resp.status_code == 200
    assert doc_detail_resp.json()["is_verified"] is True

    # Availability query
    avail_resp = client.get(
        f"/api/v1/doctors/{doctor_id}/availability?start_date={today.isoformat()}&end_date={tomorrow.isoformat()}&status=AVAILABLE"
    )
    assert avail_resp.status_code == 200
    available_slots = avail_resp.json()
    assert len(available_slots) >= 5

    # --- Step 6: Patient Slot Booking & Race Condition Handling ---
    target_slot = available_slots[0]
    booking_payload = {
        "doctor_id": doctor_id,
        "availability_id": target_slot["id"],
        "chief_complaint": "Experiencing mild chest palpitations during exercise.",
        "patient_notes": "Please check previous ECG records."
    }
    book_resp = client.post("/api/v1/appointments", json=booking_payload, headers=patient_headers)
    assert book_resp.status_code == 201, book_resp.text
    appointment_data = book_resp.json()
    assert appointment_data["status"] == "SCHEDULED"
    assert appointment_data["doctor_name"] == f"Dr. {doctor_reg_payload['first_name']} {doctor_reg_payload['last_name']}"
    assert appointment_data["doctor_specialty"] == "Cardiology"
    appt_id = appointment_data["id"]

    # Concurrency test: attempting to book the SAME slot must return 409
    dup_book_resp = client.post("/api/v1/appointments", json=booking_payload, headers=patient_headers)
    assert dup_book_resp.status_code == 409

    # --- Step 7: Patient Appointment Rescheduling ---
    reschedule_target_slot = manual_slot["id"]
    resched_resp = client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_availability_id": reschedule_target_slot},
        headers=patient_headers
    )
    assert resched_resp.status_code == 200
    rescheduled_data = resched_resp.json()
    assert rescheduled_data["status"] == "RESCHEDULED"
    assert rescheduled_data["availability_id"] == reschedule_target_slot

    # Verify original slot was freed back to AVAILABLE
    freed_slot_resp = client.get(
        f"/api/v1/doctors/{doctor_id}/availability?start_date={today.isoformat()}&end_date={today.isoformat()}&status=AVAILABLE"
    )
    assert freed_slot_resp.status_code == 200
    freed_slot_ids = [s["id"] for s in freed_slot_resp.json()]
    assert target_slot["id"] in freed_slot_ids

    # --- Step 8: Patient Appointment Cancellation ---
    cancel_resp = client.patch(
        f"/api/v1/appointments/{appt_id}/cancel",
        json={"cancellation_reason": "Schedule conflict with work meeting."},
        headers=patient_headers
    )
    assert cancel_resp.status_code == 200
    cancelled_data = cancel_resp.json()
    assert cancelled_data["status"] == "CANCELLED_PATIENT"

    # List appointments for patient
    my_appts_resp = client.get("/api/v1/appointments/me", headers=patient_headers)
    assert my_appts_resp.status_code == 200
    my_appts = my_appts_resp.json()
    assert any(a["id"] == appt_id for a in my_appts)
