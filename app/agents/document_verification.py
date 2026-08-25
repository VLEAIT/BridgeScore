import logging
import time
from decimal import Decimal

from app.agents.state import BridgeScoreState
from app.ml.fsv import FSVCalculator
from app.integrations.malpot import verify_land_record
from app.integrations.nagarik import verify_citizen

logger = logging.getLogger("bridgescore.agents.dva")


def dva_node(state: BridgeScoreState) -> dict:

    logger.info("DVA: Starting document verification")
    audit = list(state.get("audit_trail", []))
    audit.append("DVA: Initiating Lalpurja verification...")

    soft_blocks = []
    hard_blocks = []
    lalpurja_fields = {}
    ocr_confidence = 0.0
    lalpurja_verified = False
    malpot_cross_checked = False

  
    document_path = state.get("document_path")
    if document_path:
        try:
            from app.ml.ocr.paddle_ocr import LalpurjaOCR
            from app.ml.ocr.lalpurja_parser import LalpurjaParser

            ocr = LalpurjaOCR()
            ocr_result = ocr.extract(document_path)
            ocr_confidence = ocr_result.confidence

            if ocr_result.low_confidence:
                soft_blocks.append(
                    f"OCR confidence low ({ocr_confidence:.2f}) — "
                    f"manual review recommended"
                )
                audit.append(f"DVA: Low OCR confidence {ocr_confidence:.2f}")
            else:
                parser = LalpurjaParser()
                lalpurja_fields = parser.parse(ocr_result.raw_text)
                audit.append(
                    f"DVA: OCR extracted {len(lalpurja_fields)} fields "
                    f"(confidence={ocr_confidence:.2f})"
                )

        except Exception as e:
            logger.warning(f"DVA OCR failed: {e} — using form data")
            soft_blocks.append(f"OCR failed — using farmer-provided land data")
            audit.append("DVA: OCR failed — falling back to form data")
    else:
        audit.append("DVA: No document uploaded — using form data only")
        soft_blocks.append("No Lalpurja uploaded — collateral confidence reduced")

    
    district = state.get("district", "")
    land_grade = lalpurja_fields.get("land_grade") or state.get("land_grade", "Aabal")
    land_area = lalpurja_fields.get("land_area_hectares") or state.get("land_area_hectares", 0.0)

    try:
        malpot_result = verify_land_record(
            district=district,
            citizenship_number=state.get("citizenship_number", ""),
            farmer_name=state.get("farmer_name", ""),
        )
        malpot_cross_checked = malpot_result.get("verified", False)
        lalpurja_verified = malpot_cross_checked

        if not malpot_cross_checked:
            soft_blocks.append("Malpot record not digitized — using form data")
            audit.append("DVA: Malpot unverified — confidence penalty applied")
        else:
            audit.append("DVA: Malpot cross-reference verified")

    except Exception as e:
        logger.warning(f"Malpot integration failed: {e}")
        soft_blocks.append("Malpot unreachable — manual verification required")
        audit.append("DVA: Malpot unreachable")


    try:
        nagarik_result = verify_citizen(
            citizenship_number=state.get("citizenship_number", ""),
            farmer_name=state.get("farmer_name", ""),
        )
        if not nagarik_result.get("verified", False):
            hard_blocks.append("Citizenship verification failed")
            audit.append("DVA: Nagarik identity check FAILED")
        else:
            audit.append("DVA: Nagarik identity verified")

    except Exception as e:
        logger.warning(f"Nagarik integration failed: {e}")
        soft_blocks.append("Nagarik API unreachable — identity unverified")

    sarkaari_mool = lalpurja_fields.get("sarkaari_mool_nrs") or state.get("sarkaari_mool_nrs", 0.0)

    fsv_calc = FSVCalculator()
    fsv_result = fsv_calc.calculate(
        district=district,
        land_grade=land_grade,
        land_area_hectares=float(land_area),
        sarkaari_mool=Decimal(str(sarkaari_mool)) if sarkaari_mool else None,
        malpot_verified=malpot_cross_checked,
    )

    audit.append(
        f"DVA: FSV = NRs {fsv_result.fsv:,.0f} "
        f"MaxLoan = NRs {fsv_result.max_loan_amount:,.0f} "
        f"(confidence={fsv_result.confidence})"
    )

    return {
        "lalpurja_verified":    lalpurja_verified,
        "malpot_cross_checked": malpot_cross_checked,
        "ocr_confidence":       ocr_confidence,
        "lalpurja_fields":      lalpurja_fields,
        "land_area_hectares":   float(land_area),
        "land_grade":           land_grade,
        "fsv_nrs":              float(fsv_result.fsv),
        "max_loan_from_fsv":    float(fsv_result.max_loan_amount),
        "fsv_confidence":       fsv_result.confidence,
        "zone":                 fsv_result.zone,
        "dva_soft_blocks":      soft_blocks,
        "dva_hard_blocks":      hard_blocks,
        "audit_trail":          audit,
    }