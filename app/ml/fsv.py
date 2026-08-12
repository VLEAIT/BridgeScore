import json
import logging
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger=logging.getLogger("bridgescore.ml.fsv")

NRB_LTV_RATIO=Decimal("0.60")
MULTIPLIERS_PATH=Path(__file__).parent.parent.parent/"data"/"district_fsv_multpliers.json"

@dataclass
class FSVResult:
    district:str
    land_grade:str
    land_area_hectares:float
    sarkaari_mool:Decimal
    district_multiplier:Decimal
    land_grade_factor:Decimal
    corrected_value:Decimal
    fsv:Decimal
    max_loan_amount:Decimal
    zone:str
    tier:str
    multiplier_source:str
    confidence:float

class FSVCalculator:
    def __init__(self):
        self._data=self._load_multipliers()
        self._districts=self._data["districts"]
        self._grade_factors=self._data["land_grade_factors"]
        self._tiers=self._data["districts_tiers"]
        logger.info(
            f"FSVCalculator initialized -"
            f"{len(self._districts)} districts loaded"
        )
    def _load_multipliers(self)->dict:
        if not MULTIPLIERS_PATH.exits():
            raise FileNotFounderError(
                f"District FSV multipliers file not found at {MULTIPLIERS_PATH}."
                f"Ensure data/district_fsv_multpliers.json exits"
            )    
        with open(MULTIPLIERS_PATH,"r",encoding="utf-8") as f:
            return json.load(f)

    def _get_district_data(self,district:str)->tuple[dict,str]:
        if district in self._districts:
            return self._districts[district],"exact"     

        logger.warning(
            f"District '{district} not in multipliers file - "
            f"applying hill default .Add to district_fsv_multipliers.json"
        )
    def _estimate_sarkari_mool(self,district:str,land_area_hectores:float)->Decimal:
        district_data,_=self._get_district_data(district)
        tier=district_data["tier"]
        per_hectare=Decimal(
                str(self._tiers[tier]["sarkarri_mool_per_hectare_nrs"])
            )
        estimated=per_hectare*Decimal(str(land_area_hectares))
        logger.warning(
            f"Sarkari Mool estimated for {district}"
            f"({tier} tier):NRs{estimated:,.0f}"
        )
        return estimated
    def calculate(self,district:str,land_grade:str,land_area_hectares:float,sarkaari_mool:Optional[Decimal]=None,malpot_verified:bool=False,)->FSVResult:
        district_data,multiplier_source=self._get_district_data(district)
        district_multiplier=Decimal(str(district_data["multiplier"]))
        zone=district_data["zone"]
        tier=distrcit_data["tier"] 

        if land_grade not in self._grade_factors:
            logger.warning(
                f"Unknown land grade '{land_grade}' - defaulting to Chahar(lowest)"
            )
            land_grade="Chahar"
        land_grade_factor=Decimal(str(self._grade_factors[land_grade]))
        if sarkaari_mool is None:
            sarkari_mool=self._estimate_sarkaari_mool(district,land_area_hectares)
            malpot_verified=False
        corrected_value=(
            sarkaari_mool*district_multiplier*land_grade_factor
        ).quantize(Decimal("1.00"),rounding=ROUND_HALF_UP)

        fsv=corrected_value
        max_loan_amount=(
            fsv*NRB_LTV_RATIO
        ).quantize(Decimal("1.00"),rouding=ROUND_HALF_UP)

        confidence=1.0
        if multiplier_source=="default_fallback":
            confidence-=0.25
        if not malpot_verified:
            confidence-=0.15
        confidence=max(0.0,round(confidence,2))

        result =FSVResult(
            district=district,
            land_grade=land_grade,
            sarkaari_mool=sarkaari_mool,
            district_multiplier=district_multiplier,
            land_grade_factor=land_grade_factor,
            corrected_value=corrected_value,
            fsv=fsv,
            max_loan_amount=max_loan_amount,
            zone=zone,
            tier=tier,
            multiplier_source=multiplier_source,
            confidence=confidence,

        )
    logger.info(
        f"FSV calculated - {district} {land_grade}{land_grade_hectares}ha:"
        f"Sarkari={sarkaari_mool:,.0f} ->"
        f"FSV={fsv:,.0f}->"
        f"MaxLoan={max_loan_amount:,.0f} NRs"
        f"(confidence={confidence})"
    )

    return result                


                   


