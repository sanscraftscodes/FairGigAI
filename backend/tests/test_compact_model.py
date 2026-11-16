import unittest
from pathlib import Path

import numpy as np
from joblib.numpy_pickle import NumpyUnpickler

from app.services.model_service import model_service


ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_MODELS = ROOT / "models" / "all_trained_models.joblib"


class SafeUnpickler(NumpyUnpickler):
    def find_class(self, module, name):
        if "xgboost" in module:
            class DummyXGB:
                def __setstate__(self, state):
                    pass

            return DummyXGB
        return super().find_class(module, name)


class CompactModelTests(unittest.TestCase):
    def test_hist_gradient_boosting_scores_match_original_model(self):
        model_service.ensure_loaded()
        with open(ORIGINAL_MODELS, "rb") as model_file:
            models = SafeUnpickler(str(ORIGINAL_MODELS), model_file, True).load()

        original_model = models["HistGradientBoosting"]
        random = np.random.default_rng(42)
        features = random.uniform(-1.0, 1.0, size=(128, 25))
        features[0, 0] = np.nan
        features[1, 7] = np.nan

        expected = original_model.predict_proba(features)[:, 1]
        actual = model_service._predict_hgb_probabilities(features)

        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
