from app.specialties import (
    CLINIC_SPECIALTIES,
    is_valid_clinic_specialty,
    normalize_specialty_name,
)


def test_normalize_specialty_aliases():
    assert normalize_specialty_name("Obstetrician & Gynecologist") == (
        "Obstetrician & Gynaecologist"
    )
    assert normalize_specialty_name("Family Medicine") == "Family Physician"


def test_clinic_specialty_list_complete():
    assert len(CLINIC_SPECIALTIES) == 8
    assert is_valid_clinic_specialty("Neurosurgeon")
    assert not is_valid_clinic_specialty("Dentist")
