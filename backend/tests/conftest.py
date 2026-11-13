import uuid
from datetime import date, time
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.availability import Availability, AvailabilityStatus

# Create an in-memory SQLite database isolated per test run
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


@pytest.fixture(scope="function")
def db_session():
    """Provides a clean transactional database session per test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_doctor(db_session):
    """Creates a sample doctor in the database."""
    user = User(
        email="doctor.test@example.com",
        hashed_password=hash_password("DoctorPass123!"),
        role=UserRole.DOCTOR,
        phone_number="+1-555-0101",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    doctor = Doctor(
        user_id=user.id,
        first_name="Gregory",
        last_name="House",
        license_number="LIC-MD-998877",
        specialty="Diagnostic Medicine",
        qualifications="MD, Board Certified",
        experience_years=20,
        bio="Head of Diagnostic Medicine",
        consultation_fee=Decimal("150.00"),
        clinic_address="Princeton-Plainsboro Hospital",
        is_accepting_patients=True
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


@pytest.fixture
def sample_patient(db_session):
    """Creates a sample patient in the database."""
    user = User(
        email="patient.test@example.com",
        hashed_password=hash_password("PatientPass123!"),
        role=UserRole.PATIENT,
        phone_number="+1-555-0202",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    patient = Patient(
        user_id=user.id,
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        gender="Male",
        blood_group="O+",
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="+1-555-0203"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def sample_patient_2(db_session):
    """Creates a second patient for data isolation tests."""
    user = User(
        email="patient2.test@example.com",
        hashed_password=hash_password("Patient2Pass123!"),
        role=UserRole.PATIENT,
        phone_number="+1-555-0303",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    patient = Patient(
        user_id=user.id,
        first_name="Alice",
        last_name="Smith",
        date_of_birth=date(1995, 6, 15),
        gender="Female",
        blood_group="A+"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def sample_slot(db_session, sample_doctor):
    """Creates a sample available slot for the sample doctor."""
    slot = Availability(
        doctor_id=sample_doctor.id,
        slot_date=date(2026, 12, 1),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    return slot

