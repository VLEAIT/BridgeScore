import json
from decimal import Decimal
from pathlib import Path

from app.ml.fsv import FSVCalculator


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


with (DATA_DIR / "synthetic_profiles.json").open("r", encoding="utf-8") as fh:
    profiles = json.load(fh)["profiles"]

with (DATA_DIR / "district_fsv_multipliers.json").open("r", encoding="utf-8") as fh:
    district_data = json.load(fh)


def test_fsv_calculator_matches_all_synthetic_profiles() -> None:
    calculator = FSVCalculator()

    for profile in profiles:
        land = profile["land"]
        expected = profile["expected"]

        result = calculator.calculate(
            district=profile["district"],
            land_grade=land["land_grade"],
            land_area_hectares=float(land["land_area_hectares"]),
            sarkaari_mool=Decimal(str(land["sarkaari_mool_nrs"])),
            malpot_verified=land["malpot_verified"],
        )

        assert abs(result.fsv - Decimal(str(expected["fsv_nrs"]))) <= Decimal("1")
        assert abs(result.max_loan_amount - Decimal(str(expected["max_loan_nrs"]))) <= Decimal("1")
        assert result.district_multiplier == Decimal(
            str(district_data["districts"][profile["district"]]["multiplier"])
        )
        assert result.land_grade_factor == Decimal(
            str(district_data["land_grade_factors"][land["land_grade"]])
        )


def test_unknown_district_falls_back_to_default_hill() -> None:
    calculator = FSVCalculator()

    result = calculator.calculate(
        district="Unknown Hill District",
        land_grade="Aabal",
        land_area_hectares=1.0,
        sarkaari_mool=Decimal("200000"),
        malpot_verified=True,
    )

    assert result.multiplier_source == "default_hill"
    assert result.district_multiplier == Decimal("0.45")
    assert result.zone == "hill"


def test_unverified_malpot_applies_confidence_penalty() -> None:
    calculator = FSVCalculator()

    result = calculator.calculate(
        district="Karnali",
        land_grade="Sim",
        land_area_hectares=0.2,
        sarkaari_mool=Decimal("48000"),
        malpot_verified=False,
    )

    assert result.confidence == 0.85
    assert result.multiplier_source == "exact"


def test_unknown_land_grade_falls_back_to_chahar() -> None:
    calculator = FSVCalculator()

    result = calculator.calculate(
        district="Kavrepalanchok",
        land_grade="UnknownGrade",
        land_area_hectares=0.5,
        sarkaari_mool=Decimal("516129"),
        malpot_verified=True,
    )

    assert result.land_grade == "Chahar"
    assert result.land_grade_factor == Decimal("0.30")
