"""
Database Seeding Script for Medicall
Populates initial verified physicians, schedules, and availability slots on fresh cloud deployments.
"""

import logging
from datetime import date, time, timedelta
from uuid import uuid4

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.availability import Availability, AvailabilityStatus
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.patient import Patient
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medicall_seed")


def seed_database():
    db = SessionLocal()
    try:
        existing_doctors = db.query(Doctor).count()
        if existing_doctors > 0:
            logger.info("Database already contains %d doctors. Skipping seeding.", existing_doctors)
            return

        logger.info("Empty database detected. Seeding initial clinical directory...")

        # 1. Admin User
        admin_user = User(
            id=uuid4(),
            email="admin@medicall.health",
            hashed_password=get_password_hash("MedicallAdmin2026!"),
            role=UserRole.ADMIN,
            phone_number="+919876543210",
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)

        # 2. Test Patient (Sarah Connor)
        patient_user = User(
            id=uuid4(),
            email="sarah.connor@example.com",
            hashed_password=get_password_hash("MedicallDev2026!"),
            role=UserRole.PATIENT,
            phone_number="+919876543211",
            is_active=True,
            is_verified=True,
        )
        db.add(patient_user)
        db.flush()

        patient_profile = Patient(
            id=uuid4(),
            user_id=patient_user.id,
            first_name="Sarah",
            last_name="Connor",
            date_of_birth=date(1990, 5, 15),
            gender="Female",
            blood_group="O+",
            emergency_contact_name="John Connor",
            emergency_contact_phone="+919876543212",
        )
        db.add(patient_profile)

        # 3. Verified Doctors Directory
        doctors_data = [
            {
                "email": "dr.arun@medicall.health",
                "first_name": "Arun",
                "last_name": "Prasath",
                "specialty": "Psychiatry",
                "qualifications": "MBBS, MD (Psychiatry)",
                "license_number": "MED-PSY-2026-001",
                "experience_years": 5,
                "bio": "Specialist in clinical psychology, stress management, cognitive behavioral therapy, and adult mental health.",
                "consultation_fee": 100.00,
                "clinic_address": "Kalasalingam Academy of Research and Education, Krishnankoil, Srivilliputhur, Tamil Nadu",
            },
            {
                "email": "dr.priya@medicall.health",
                "first_name": "Priya",
                "last_name": "Sharma",
                "specialty": "Cardiology",
                "qualifications": "MBBS, MD, DM (Cardiology), FACC",
                "license_number": "MED-CAR-2026-002",
                "experience_years": 12,
                "bio": "Senior interventional cardiologist with expertise in preventive cardiology, hypertension, and arrhythmia management.",
                "consultation_fee": 150.00,
                "clinic_address": "Apollo Specialty Health Institute, Greams Road, Chennai, Tamil Nadu",
            },
            {
                "email": "dr.rajesh@medicall.health",
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "specialty": "General Medicine",
                "qualifications": "MBBS, MD (General Medicine)",
                "license_number": "MED-GEN-2026-003",
                "experience_years": 15,
                "bio": "Compassionate primary care physician experienced in chronic disease management, diabetes, and lifestyle medicine.",
                "consultation_fee": 80.00,
                "clinic_address": "Fortis Care Medical Centre, Bannerghatta Road, Bangalore, Karnataka",
            },
            {
                "email": "dr.ananya@medicall.health",
                "first_name": "Ananya",
                "last_name": "Sen",
                "specialty": "Dermatology",
                "qualifications": "MBBS, MD (Dermatology, Venereology & Leprosy)",
                "license_number": "MED-DER-2026-004",
                "experience_years": 8,
                "bio": "Consultant dermatologist specializing in eczema, psoriasis, medical dermatology, and pediatric skin conditions.",
                "consultation_fee": 120.00,
                "clinic_address": "Skin & Wellness Clinic, Park Street, Kolkata, West Bengal",
            },
            {
                "email": "dr.vikram@medicall.health",
                "first_name": "Vikram",
                "last_name": "Mehta",
                "specialty": "Pediatrics",
                "qualifications": "MBBS, DCH, DNB (Pediatrics)",
                "license_number": "MED-PED-2026-005",
                "experience_years": 10,
                "bio": "Dedicated pediatrician focused on neonatal care, childhood development milestones, and immunization.",
                "consultation_fee": 90.00,
                "clinic_address": "Max Children's Care Centre, Andheri West, Mumbai, Maharashtra",
            },
        ]

        today = date.today()
        slot_times = [
            (time(9, 0), time(9, 30)),
            (time(9, 30), time(10, 0)),
            (time(10, 0), time(10, 30)),
            (time(10, 30), time(11, 0)),
            (time(11, 0), time(11, 30)),
            (time(11, 30), time(12, 0)),
            (time(14, 0), time(14, 30)),
            (time(14, 30), time(15, 0)),
        ]

        for doc_item in doctors_data:
            doc_user = User(
                id=uuid4(),
                email=doc_item["email"],
                hashed_password=get_password_hash("MedicallDoctor2026!"),
                role=UserRole.DOCTOR,
                phone_number="+919876543200",
                is_active=True,
                is_verified=True,
            )
            db.add(doc_user)
            db.flush()

            doctor = Doctor(
                id=uuid4(),
                user_id=doc_user.id,
                first_name=doc_item["first_name"],
                last_name=doc_item["last_name"],
                specialty=doc_item["specialty"],
                qualifications=doc_item["qualifications"],
                license_number=doc_item["license_number"],
                experience_years=doc_item["experience_years"],
                bio=doc_item["bio"],
                consultation_fee=doc_item["consultation_fee"],
                clinic_address=doc_item["clinic_address"],
                is_accepting_patients=True,
            )
            db.add(doctor)
            db.flush()

            # Add schedules for Monday to Friday (0 to 4)
            for day_idx in range(5):
                schedule = DoctorSchedule(
                    id=uuid4(),
                    doctor_id=doctor.id,
                    day_of_week=day_idx,
                    start_time=time(9, 0),
                    end_time=time(15, 0),
                    slot_duration_minutes=30,
                    is_active=True,
                )
                db.add(schedule)

            # Generate slots for next 14 days (excluding Sundays)
            for offset in range(1, 15):
                slot_date = today + timedelta(days=offset)
                if slot_date.weekday() == 6:  # Sunday
                    continue
                for st, et in slot_times:
                    slot = Availability(
                        id=uuid4(),
                        doctor_id=doctor.id,
                        slot_date=slot_date,
                        start_time=st,
                        end_time=et,
                        status=AvailabilityStatus.AVAILABLE,
                    )
                    db.add(slot)

        db.commit()
        logger.info("Successfully seeded admin, patient, 5 verified doctors, schedules, and availability slots.")
    except Exception as exc:
        db.rollback()
        logger.error("Seeding failed: %s", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
