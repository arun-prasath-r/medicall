import pytest
from app.models.user import UserRole


def test_patient_registration(client):
    """Verifies successful registration of a patient account."""
    payload = {
        "email": "sarah.connor@example.com",
        "password": "StrongPassword123!",
        "role": "PATIENT",
        "first_name": "Sarah",
        "last_name": "Connor",
        "date_of_birth": "1985-05-12",
        "phone_number": "+1-555-0999"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "sarah.connor@example.com"
    assert data["role"] == "PATIENT"
    assert data["is_verified"] is True
    assert "user_id" in data
    assert "profile_id" in data


def test_doctor_registration(client):
    """Verifies registration of a doctor account requiring verification."""
    payload = {
        "email": "dr.smith@example.com",
        "password": "DoctorStrong123!",
        "role": "DOCTOR",
        "first_name": "John",
        "last_name": "Smith",
        "license_number": "MED-LIC-12345",
        "specialty": "Cardiology",
        "qualifications": "MD, FACC",
        "experience_years": 10,
        "consultation_fee": 200.00
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "dr.smith@example.com"
    assert data["role"] == "DOCTOR"
    assert data["is_verified"] is False  # Doctor requires admin verification


def test_duplicate_email_registration_rejected(client, sample_patient):
    """Verifies that duplicate email addresses are rejected with 400 Bad Request."""
    payload = {
        "email": "patient.test@example.com",  # Already exists from fixture
        "password": "AnotherPassword123!",
        "role": "PATIENT",
        "first_name": "Copy",
        "last_name": "Cat",
        "date_of_birth": "1990-01-01"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, sample_patient):
    """Verifies successful login returning a valid JWT bearer token."""
    payload = {
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "patient.test@example.com"


def test_login_invalid_password(client, sample_patient):
    """Verifies that an incorrect password returns 401 Unauthorized."""
    payload = {
        "email": "patient.test@example.com",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


def test_get_me_authenticated(client, sample_patient):
    """Verifies retrieving current user identity with valid JWT token."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "patient.test@example.com"
    assert data["role"] == "PATIENT"


def test_role_based_authorization(client, sample_doctor, sample_patient):
    """Verifies that doctors cannot access patient-only endpoints."""
    # Doctor login
    doc_login = client.post("/api/v1/auth/login", json={
        "email": "doctor.test@example.com",
        "password": "DoctorPass123!"
    })
    doc_token = doc_login.json()["access_token"]

    # Doctor tries to access patient /patients/me
    response = client.get(
        "/api/v1/patients/me",
        headers={"Authorization": f"Bearer {doc_token}"}
    )
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]

