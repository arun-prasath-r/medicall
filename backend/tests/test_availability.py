def test_get_doctor_availability(client, sample_doctor, sample_slot):
    """Verifies querying available slots for a doctor."""
    response = client.get(
        f"/api/v1/doctors/{sample_doctor.id}/availability",
        params={"start_date": "2026-12-01", "end_date": "2026-12-01"}
    )
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 1
    assert slots[0]["id"] == str(sample_slot.id)
    assert slots[0]["status"] == "AVAILABLE"


def test_create_discrete_slot(client, sample_doctor):
    """Verifies creating an individual availability slot."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "doctor.test@example.com",
        "password": "DoctorPass123!"
    })
    token = login_resp.json()["access_token"]

    payload = {
        "slot_date": "2026-12-02",
        "start_time": "14:00:00",
        "end_time": "14:30:00",
        "status": "AVAILABLE"
    }

    response = client.post(
        f"/api/v1/doctors/{sample_doctor.id}/availability",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slot_date"] == "2026-12-02"
    assert data["start_time"] == "14:00:00"


def test_prevent_overlapping_availability_slots(client, sample_doctor, sample_slot):
    """Verifies that attempting to create an overlapping slot is rejected with 400 Bad Request."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "doctor.test@example.com",
        "password": "DoctorPass123!"
    })
    token = login_resp.json()["access_token"]

    # sample_slot is 2026-12-01 10:00:00 - 10:30:00
    # Overlapping slot: 10:15:00 - 10:45:00
    payload = {
        "slot_date": "2026-12-01",
        "start_time": "10:15:00",
        "end_time": "10:45:00",
        "status": "AVAILABLE"
    }

    response = client.post(
        f"/api/v1/doctors/{sample_doctor.id}/availability",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "overlaps" in response.json()["detail"].lower()


def test_generate_slots_from_schedules(client, sample_doctor):
    """Verifies dynamic slot generation for recurring doctor schedule templates."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "doctor.test@example.com",
        "password": "DoctorPass123!"
    })
    token = login_resp.json()["access_token"]

    # Set schedule for Wednesday (weekday=2) from 09:00 to 11:00 with 30-min slots
    client.post(
        f"/api/v1/doctors/{sample_doctor.id}/schedules",
        json={
            "day_of_week": 2,  # Wednesday
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "slot_duration_minutes": 30,
            "is_active": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # 2026-12-02 is a Wednesday
    gen_resp = client.post(
        f"/api/v1/doctors/{sample_doctor.id}/availability/generate",
        json={
            "start_date": "2026-12-02",
            "end_date": "2026-12-02"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert gen_resp.status_code == 200
    slots = gen_resp.json()
    # 09:00-09:30, 09:30-10:00, 10:00-10:30, 10:30-11:00 -> 4 slots
    assert len(slots) == 4

