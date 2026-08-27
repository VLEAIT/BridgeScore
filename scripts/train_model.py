import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.scoring.synthetic_data import generate, save
from app.ml.scoring.train import run_training_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("bridgescore.scripts.train")

if __name__ == "__main__":
    logger.info("Step 1/2 — Generating synthetic training data...")
    profiles = generate(n_variations=494)
    save(profiles)

    logger.info("Step 2/2 — Training XGBoost model...")
    run_training_pipeline()

    logger.info("Done — model ready for inference")
