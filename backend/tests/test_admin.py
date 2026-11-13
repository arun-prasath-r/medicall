import uuid
from decimal import Decimal
import pytest
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.doctor import Doctor


@pytest.fixture
def sample_admin(db_session):
    admin_user = User(
        email="admin.test@example.com",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def unverified_doctor(db_session):
    user = User(
        email="unverified.doc@example.com",
        hashed_password=hash_password("DocPass123!"),
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    db_session.flush()

    doctor = Doctor(
        user_id=user.id,
        first_name="Pending",
        last_name="Physician",
        license_number="LIC-PENDING-001",
        specialty="Pediatrics",
        qualifications="MBBS, DCH",
        consultation_fee=Decimal("90.00"),
        is_accepting_patients=True
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


def test_admin_verify_doctor_authorized(client, sample_admin, unverified_doctor, db_session):
    """Verifies that an ADMIN can successfully verify/approve a doctor account."""
    # Admin login
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin.test@example.com",
        "password": "AdminPass123!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    # Verify doctor
    resp = client.patch(
        f"/api/v1/admin/doctors/{unverified_doctor.id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_verified"] is True
    assert data["doctor_id"] == str(unverified_doctor.id)

    # Check database state
    db_session.expire_all()
    doc_in_db = db_session.query(Doctor).filter(Doctor.id == unverified_doctor.id).first()
    assert doc_in_db.user.is_verified is True


def test_admin_verify_doctor_unauthorized_patient(client, sample_patient, unverified_doctor):
    """Verifies that a PATIENT cannot verify doctors (403 Forbidden)."""
    pat_login = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    pat_token = pat_login.json()["access_token"]

    resp = client.patch(
        f"/api/v1/admin/doctors/{unverified_doctor.id}/verify",
        headers={"Authorization": f"Bearer {pat_token}"}
    )
    assert resp.status_code == 403


def test_admin_verify_doctor_unauthorized_doctor(client, sample_doctor, unverified_doctor):
    """Verifies that another DOCTOR cannot verify doctors (403 Forbidden)."""
    doc_login = client.post("/api/v1/auth/login", json={
        "email": "doctor.test@example.com",
        "password": "DoctorPass123!"
    })
    doc_token = doc_login.json()["access_token"]

    resp = client.patch(
        f"/api/v1/admin/doctors/{unverified_doctor.id}/verify",
        headers={"Authorization": f"Bearer {doc_token}"}
    )
    assert resp.status_code == 403


def test_admin_verify_doctor_not_found(client, sample_admin):
    """Verifies 404 Not Found for non-existent doctor ID."""
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin.test@example.com",
        "password": "AdminPass123!"
    })
    admin_token = admin_login.json()["access_token"]

    random_id = str(uuid.uuid4())
    resp = client.patch(
        f"/api/v1/admin/doctors/{random_id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 404

