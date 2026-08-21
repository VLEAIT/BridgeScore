
import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("bridgescore.ml.ocr.parser")

DEVANAGARI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    'Y': '5', 'S': '5',
}

def convert_devanagari_digits(text: str) -> str:
   
    for dev, ascii_digit in DEVANAGARI_DIGITS.items():
        text = text.replace(dev, ascii_digit)
    return text


@dataclass
class ParsedLalpurja:
    owner_name: Optional[str] = None
    citizenship_no: Optional[str] = None
    district: Optional[str] = None
    kitta_number: Optional[str] = None
    area_sq_meters: Optional[float] = None
    raw_area_text: Optional[str] = None
    is_valid_lalpurja: bool = False
    extracted_fields: int = 0


class LalpurjaParser:

    def parse(self, ocr_text: str) -> ParsedLalpurja:
        logger.info("Parsing OCR text for Lalpurja schema...")
        result = ParsedLalpurja()
        fields_found = 0

        
        validity_keywords = ["जग्गाधनी", "प्रमाण", "पुर्जा", "भूमिसुधार", "LRIMS", "रैकर"]
        matching_keywords = [kw for kw in validity_keywords if kw in ocr_text]
        if len(matching_keywords) >= 2:
            result.is_valid_lalpurja = True

     
        owner_match = re.search(r"जग्गाधनी[को\s]*नाम\s*थर[ः:\'\s]+([^\n]+)", ocr_text)
        if owner_match:
            result.owner_name = owner_match.group(1).strip()
            fields_found += 1

        cit_match = re.search(r"नागरिकता\s*न[०-९\.\s]*[ः:]?\s*([०-९0-9\s/]+)", ocr_text)
        if cit_match:
            raw_cit = cit_match.group(1).strip().split('\n')[0]
            result.citizenship_no = convert_devanagari_digits(raw_cit)
            fields_found += 1


        district_match = re.search(r"जिल्ला[ः:]?\s*([^\n\s]+)", ocr_text)
        if district_match:
            result.district = district_match.group(1).strip()
            fields_found += 1

       
        kitta_match = re.search(r"([०-९0-9Y]{3,4})\s*राजिनामा", ocr_text)
        if not kitta_match:
            kitta_match = re.search(r"कित्ता\s*नं[०-९\.\s]*[ः:]?\s*([०-९0-9Y]+)", ocr_text)
        
        if kitta_match:
            raw_kitta = kitta_match.group(1).strip()
            result.kitta_number = convert_devanagari_digits(raw_kitta)
            fields_found += 1

     
        area_match = re.search(r"जम्मा\s*अनफल\s*([०-९0-9\.\s]+)", ocr_text)
        if not area_match:
            area_match = re.search(r"([०-९0-9\.\s]+)\s*वर्ग\s*म[िी]", ocr_text)
        
        if area_match:
            raw_area = area_match.group(1).strip()
            result.raw_area_text = raw_area
            clean_digits = convert_devanagari_digits(raw_area)
         
            parts = clean_digits.split()
            if len(parts) == 2 and not "." in clean_digits:
                clean_str = f"{parts[0]}.{parts[1]}"
            else:
                clean_str = clean_digits.replace(" ", "")

            try:
                result.area_sq_meters = float(clean_str)
                fields_found += 1
            except ValueError:
                pass

        result.extracted_fields = fields_found
        logger.info(f"Parsing complete — Valid: {result.is_valid_lalpurja}, Extracted: {fields_found}/5")
        return result