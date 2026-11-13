def test_list_doctors(client, sample_doctor):
    """Verifies listing active doctors."""
    response = client.get("/api/v1/doctors")
    assert response.status_code == 200
    doctors = response.json()
    assert len(doctors) >= 1
    assert doctors[0]["first_name"] == "Gregory"
    assert doctors[0]["specialty"] == "Diagnostic Medicine"


def test_doctor_specialties(client, sample_doctor):
    """Verifies retrieving distinct doctor specialties."""
    response = client.get("/api/v1/doctors/specialties")
    assert response.status_code == 200
    specialties = response.json()
    assert "Diagnostic Medicine" in specialties


def test_get_doctor_by_id(client, sample_doctor):
    """Verifies retrieving a specific doctor by UUID."""
    response = client.get(f"/api/v1/doctors/{sample_doctor.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_doctor.id)
    assert data["last_name"] == "House"


def test_doctor_schedule_management(client, sample_doctor):
    """Verifies doctor configuring their recurring weekly schedule."""
    # Login doctor
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "doctor.test@example.com",
        "password": "DoctorPass123!"
    })
    token = login_resp.json()["access_token"]

    schedule_payload = {
        "day_of_week": 0,  # Monday
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "slot_duration_minutes": 30,
        "is_active": True
    }

    # Add schedule
    response = client.post(
        f"/api/v1/doctors/{sample_doctor.id}/schedules",
        json=schedule_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["day_of_week"] == 0
    assert data["slot_duration_minutes"] == 30

    # Retrieve schedules
    get_resp = client.get(f"/api/v1/doctors/{sample_doctor.id}/schedules")
    assert get_resp.status_code == 200
    schedules = get_resp.json()
    assert len(schedules) == 1

