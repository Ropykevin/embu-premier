"""Clinic specialty list for booking and services (not tied to DB doctor count)."""

CLINIC_SPECIALTIES = [
    "Family Physician",
    "General Surgeon",
    "Neurosurgeon",
    "ENT Surgeon",
    "Obstetrician & Gynaecologist",
    "Radiologist",
    "Ophthalmologist",
    "Urologist",
]

SPECIALTY_INFO = {
    "Family Physician": (
        "Provides comprehensive healthcare for children, adults and the elderly "
        "including preventive care, diagnosis and treatment of common illnesses."
    ),
    "General Surgeon": (
        "Provides diagnosis and surgical treatment for abdominal conditions, hernias, "
        "breast disorders, thyroid diseases and other general surgical conditions."
    ),
    "Neurosurgeon": (
        "Specializes in the diagnosis and surgical treatment of disorders affecting "
        "the brain, spine and nervous system."
    ),
    "ENT Surgeon": (
        "Treats diseases affecting the ear, nose, throat, head and neck using "
        "medical and surgical approaches."
    ),
    "Obstetrician & Gynaecologist": (
        "Provides comprehensive care for women's reproductive health, pregnancy, "
        "childbirth and gynaecological conditions."
    ),
    "Radiologist": (
        "Provides diagnostic imaging services including X-rays, ultrasound, CT scan "
        "and MRI interpretation."
    ),
    "Ophthalmologist": (
        "Diagnoses and treats eye diseases, performs eye surgery and helps preserve "
        "and restore vision."
    ),
    "Urologist": (
        "Specializes in diseases affecting the urinary tract and male reproductive system."
    ),
}


def normalize_specialty_name(name):
    """Map common spelling variants to the canonical clinic specialty name."""
    if not name:
        return None
    aliases = {
        "Obstetrician & Gynecologist": "Obstetrician & Gynaecologist",
        "Gynaecologist": "Obstetrician & Gynaecologist",
        "Gynecologist": "Obstetrician & Gynaecologist",
        "Family Medicine": "Family Physician",
        "ENT": "ENT Surgeon",
    }
    cleaned = name.strip()
    return aliases.get(cleaned, cleaned)


def is_valid_clinic_specialty(name):
    normalized = normalize_specialty_name(name)
    return normalized in CLINIC_SPECIALTIES
