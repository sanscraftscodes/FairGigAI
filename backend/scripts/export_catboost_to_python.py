"""
FairGig AI — Export CatBoost model to pure-Python inference artifact.

Run this script whenever the CatBoost model is retrained to regenerate
models/cat_model_python.py.  Requires catboost, joblib, and the full
training dataset to be available locally.

Usage:
    python backend/scripts/export_catboost_to_python.py
"""

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Allow running from project root or backend/scripts directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


def main():
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))

    import joblib
    from catboost import Pool

    from app.services.feature_builder import FEATURE_COLUMNS_27

    cat_path = MODELS_DIR / "cat_model.joblib"
    if not cat_path.exists():
        raise FileNotFoundError(f"CatBoost model not found at {cat_path}")

    print("Loading CatBoost model from joblib…")
    cat_model = joblib.load(cat_path)

    # Build a minimal pool covering all known category combinations so the
    # Python exporter can embed the hash → value lookup table.
    task_types = ["delivery", "document", "food", "fragile", "grocery", "medicine"]
    skills = [
        "cold_chain",
        "customer_service",
        "driving",
        "handling",
        "navigation",
        "time_management",
    ]

    rows = []
    for tt in task_types:
        for sk in skills:
            rows.append(
                [tt, sk, 2.0, 60.0, 240.0, 500.0, 2.5, 3.5, 0.3, 3.0,
                 0.85, 0.80, 0.78, 0.1, 0.1, 0.05, 0.08, 20.0, 80.0,
                 0.5, 0.3, 0.7, 1.0, 1.0, 1.0, 1.0, 1.0]
            )

    pool = Pool(rows, cat_features=[0, 1], feature_names=FEATURE_COLUMNS_27)

    out_path = MODELS_DIR / "cat_model_python.py"
    print(f"Exporting to {out_path}…")
    cat_model.save_model(str(out_path), format="python", pool=pool)

    size_kb = out_path.stat().st_size / 1024
    print(f"Export complete: {out_path} ({size_kb:.1f} KB)")
    print()
    print("Validating predictions match the original CatBoost model…")

    import math
    import sys as _sys
    import importlib.util

    spec = importlib.util.spec_from_file_location("cat_model_python", out_path)
    cbpy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cbpy)

    NUMERIC_COLS = FEATURE_COLUMNS_27[2:]  # skip task_type, required_skill
    float_vals = [2.0, 60.0, 240.0, 500.0, 2.5, 3.5, 0.3, 3.0, 0.85, 0.80, 0.78,
                  0.1, 0.1, 0.05, 0.08, 20.0, 80.0, 0.5, 0.3, 0.7, 1.0, 1.0, 1.0, 1.0, 1.0]

    test_cases = [("fragile", "handling"), ("delivery", "driving"), ("medicine", "cold_chain")]
    all_ok = True
    for tt, sk in test_cases:
        row = [[tt, sk] + float_vals]
        p_cb = cat_model.predict_proba(Pool(row, cat_features=[0, 1], feature_names=FEATURE_COLUMNS_27))[0, 1]
        raw = cbpy.apply_catboost_model(float_vals, [tt, sk])
        p_py = 1.0 / (1.0 + math.exp(-raw))
        diff = abs(p_cb - p_py)
        ok = diff < 1e-6
        if not ok:
            all_ok = False
        status = "OK" if ok else f"MISMATCH diff={diff:.2e}"
        print(f"  {tt}/{sk}: CatBoost={p_cb:.6f}  PurePy={p_py:.6f}  {status}")

    if all_ok:
        print("\nAll predictions match. cat_model_python.py is ready for deployment.")
    else:
        print("\nWARNING: Some predictions differ — please investigate before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    main()
