from pathlib import Path
from app.agents.document_verification import dva_node
from app.agents.state import initial_state


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LALPURJA_IMAGE_PATH = str(PROJECT_ROOT / "data" / "sample_lalpurja.png")


def test_dva_node_with_lalpurja_image(monkeypatch) -> None:
    
    assert Path(LALPURJA_IMAGE_PATH).exists(), f"Image file not found at: {LALPURJA_IMAGE_PATH}"

    
    def mock_verify_land_record(*args, **kwargs):
        return {"verified": True}

    def mock_verify_citizen(*args, **kwargs):
        return {"verified": True}

    monkeypatch.setattr(
        "app.agents.document_verification.verify_land_record",
        mock_verify_land_record,
    )
    monkeypatch.setattr(
        "app.agents.document_verification.verify_citizen",
        mock_verify_citizen,
    )

   
    state = initial_state(
        {
            "farmer_name": "Ramesh Kumar",
            "district": "Kavrepalanchok",
            "citizenship_number": "12345678",
            "document_path": LALPURJA_IMAGE_PATH,
            "land_area_hectares": 0.5,
            "land_grade": "Aabal",
            "sarkaari_mool_nrs": 516129,
        }
    )

  
    result = dva_node(state)

    assert result["ocr_confidence"] > 0.0, "OCR confidence should be greater than 0 for a valid image"
    assert isinstance(result["lalpurja_fields"], dict), "lalpurja_fields should contain a parsed dict"
    
    # Assertions for Identity & Verification
    assert result["lalpurja_verified"] is True
    assert result["malpot_cross_checked"] is True
    assert result["dva_hard_blocks"] == []

    # Assertions for FSV Calculations
    assert result["fsv_nrs"] > 0
    assert result["max_loan_from_fsv"] == result["fsv_nrs"] * 0.60
    assert "DVA: Nagarik identity verified" in result["audit_trail"]