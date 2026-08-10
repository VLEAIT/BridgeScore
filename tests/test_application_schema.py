from decimal import Decimal

from app.schemas.application import ApplicationCreate


def test_application_create_requires_phone_number() -> None:
    payload = {
        "farmer_name": "Ramesh Kumar",
        "district": "Kavrepalanchok",
        "citizenship_number": "12345678",
        "phone_number": "9800000000",
        "land_area_hectares": 0.5,
        "land_type": "Khet",
        "land_grade": "Aabal",
        "coop_income_monthly": Decimal("18000.0"),
        "remittance_monthly": Decimal("40000.0"),
        "remittance_channel": "IME",
        "requested_amount": Decimal("200000"),
        "consent_given": True,
    }

    model = ApplicationCreate.model_validate(payload)

    assert model.phone_number == "9800000000"
