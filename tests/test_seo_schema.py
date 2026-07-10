from app.seo import build_medical_business_ld, physician_ld_for_doctor


def test_build_medical_business_ld(app):
    with app.app_context():
        data = build_medical_business_ld()
    assert data is not None
    assert data["@type"] == "MedicalBusiness"
    assert "Embu Town" in data["address"]["addressLocality"]
    assert len(data["medicalSpecialty"]) >= 8


def test_physician_ld_for_doctor(app, sample_doctor):
    with app.app_context():
        data = physician_ld_for_doctor(sample_doctor)
    assert data["@type"] == "Physician"
    assert data["name"] == sample_doctor.doctor_name
    assert data["medicalSpecialty"] == sample_doctor.specialty
