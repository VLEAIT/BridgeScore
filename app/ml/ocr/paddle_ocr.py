import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("bridgescore.ml.ocr")


@dataclass
class OCRResult:
    raw_text: str
    lines: list[str]
    confidence: float
    low_confidence: bool
    word_boxes: list[dict]
    image_path: str
    error: Optional[str] = None


class LalpurjaOCR:

    CONFIDENCE_THRESHOLD = 0.70

    def __init__(self):
        self._reader = self._initialize_easyocr()

    def _initialize_easyocr(self):
        try:
            import easyocr

            # 'hi' covers Devanagari (Hindi/Nepali script), 'en' covers digits/English text
            reader = easyocr.Reader(["hi", "en"], gpu=False)
            logger.info("EasyOCR initialized successfully (CPU Mode)")
            return reader

        except ImportError:
            logger.error(
                "EasyOCR not installed. Run: pip install easyocr torch"
            )
            raise

        except Exception as e:
            logger.error(f"EasyOCR initialization failed: {e}")
            raise

    def extract(self, image_path: str) -> OCRResult:
        path = Path(image_path)

        if not path.exists():
            logger.error(f"Image not found: {image_path}")
            return OCRResult(
                raw_text="",
                lines=[],
                confidence=0.0,
                low_confidence=True,
                word_boxes=[],
                image_path=image_path,
                error=f"Image not found: {image_path}",
            )

        logger.info(f"Running EasyOCR on: {image_path}")

        try:
            # reader.readtext returns: [(bbox, text, prob), ...]
            raw_results = self._reader.readtext(str(path))

            if not raw_results:
                logger.warning(f"No text detected in image: {image_path}")
                return OCRResult(
                    raw_text="",
                    lines=[],
                    confidence=0.0,
                    low_confidence=True,
                    word_boxes=[],
                    image_path=image_path,
                    error="No text detected — image may be blank or unreadable",
                )

            lines = []
            confidences = []
            word_boxes = []

            for box, text, conf in raw_results:
                # Convert numpy types to native python floats/lists for JSON serializability
                clean_conf = float(conf)
                clean_box = [[float(point[0]), float(point[1])] for point in box]

                lines.append(text)
                confidences.append(clean_conf)
                word_boxes.append(
                    {
                        "text": text,
                        "confidence": round(clean_conf, 4),
                        "box": clean_box,
                    }
                )

            avg_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            low_confidence = avg_confidence < self.CONFIDENCE_THRESHOLD
            raw_text = "\n".join(lines)

            if low_confidence:
                logger.warning(
                    f"Low OCR confidence: {avg_confidence:.2f} — consider requesting clearer image"
                )
            else:
                logger.info(
                    f"OCR complete — {len(lines)} lines, confidence: {avg_confidence:.2f}"
                )

            return OCRResult(
                raw_text=raw_text,
                lines=lines,
                confidence=round(avg_confidence, 4),
                low_confidence=low_confidence,
                word_boxes=word_boxes,
                image_path=image_path,
            )

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return OCRResult(
                raw_text="",
                lines=[],
                confidence=0.0,
                low_confidence=True,
                word_boxes=[],
                image_path=image_path,
                error=str(e),
            )

    def extract_with_retry(
        self,
        image_path: str,
        min_confidence: float = 0.70,
    ) -> OCRResult:
        result = self.extract(image_path)

        if result.error:
            logger.error(f"OCR failed entirely: {result.error}")
        elif result.confidence < min_confidence:
            logger.warning(
                f"OCR confidence {result.confidence:.2f} below threshold {min_confidence} — DVA will flag for human review"
            )

        return result


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    image_path = (
        sys.argv[1] if len(sys.argv) > 1 else "data/sample_lalpurja.png"
    )

    print(f"\nTesting EasyOCR on: {image_path}")
    print("─" * 50)

    ocr = LalpurjaOCR()
    result = ocr.extract(image_path)

    if result.error:
        print(f"ERROR: {result.error}")
    else:
        print(f"Confidence  : {result.confidence:.2f}")
        print(f"Lines found : {len(result.lines)}")
        print(f"Low conf    : {result.low_confidence}")
        print(f"\nExtracted text:")
        print("─" * 50)
        print(result.raw_text)
        print("─" * 50)
        print("\nWord boxes (first 5):")
        for box in result.word_boxes[:5]:
            print(f"  '{box['text']}' — conf: {box['confidence']}")