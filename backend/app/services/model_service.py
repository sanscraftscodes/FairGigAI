import os
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Tuple, Optional, List

# Scikit-learn backwards compatibility shim for 1.6.1 -> 1.8.0
try:
    import sklearn.compose._column_transformer as ct
    if not hasattr(ct, "_RemainderColsList"):
        class _RemainderColsList(list):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.__dict__ = {}
        ct._RemainderColsList = _RemainderColsList
except Exception:
    pass

from app.config import MODELS_DIR, PREDICTIONS_DIR
from app.services.feature_builder import NUMERIC_COLUMNS_25, FEATURE_COLUMNS_27

class ModelService:
    def __init__(self):
        self.cat_model = None
        self.hgb_model = None
        self.ensemble_weights = [0.5, 0.0, 0.0, 0.5]
        self.ensemble_threshold = 0.155
        self.is_loaded = False
        self.load_error = None
        self._load_attempted = False
        self._load_lock = Lock()

    def ensure_loaded(self):
        if self.is_loaded:
            return
        with self._load_lock:
            if not self._load_attempted:
                self.load_models()
                self._load_attempted = True
        if not self.is_loaded:
            raise RuntimeError(f"ML Model service is not loaded: {self.load_error}")

    def load_models(self):
        try:
            # 1. Load CatBoost
            cat_path = MODELS_DIR / "cat_model.joblib"
            if cat_path.exists():
                self.cat_model = joblib.load(cat_path)
            else:
                raise FileNotFoundError(f"CatBoost model artifact not found at {cat_path}")

            # 2. Load HistGradientBoosting from all_trained_models.joblib
            all_models_path = MODELS_DIR / "all_trained_models.joblib"
            if all_models_path.exists():
                class SafeUnpickler(joblib.numpy_pickle.NumpyUnpickler):
                    def find_class(self, module, name):
                        if "xgboost" in module:
                            class DummyXGB:
                                def __setstate__(self, state): pass
                            return DummyXGB
                        return super().find_class(module, name)

                with open(all_models_path, "rb") as f:
                    u = SafeUnpickler(str(all_models_path), f, True)
                    all_models = u.load()
                    if isinstance(all_models, dict) and "HistGradientBoosting" in all_models:
                        self.hgb_model = all_models["HistGradientBoosting"]
                    else:
                        raise ValueError("HistGradientBoosting not found in all_trained_models.joblib")
            else:
                raise FileNotFoundError(f"all_trained_models.joblib not found at {all_models_path}")

            # 3. Load ensemble configuration if available
            ensemble_config_path = MODELS_DIR / "ensemble_configuration.json"
            if ensemble_config_path.exists():
                try:
                    with open(ensemble_config_path, "r") as f:
                        cfg = json.load(f)
                        if "best_weights" in cfg and isinstance(cfg["best_weights"], list):
                            self.ensemble_weights = cfg["best_weights"]
                        if "ensemble_threshold" in cfg and isinstance(cfg["ensemble_threshold"], (int, float)):
                            self.ensemble_threshold = float(cfg["ensemble_threshold"])
                except Exception as e:
                    print(f"Warning reading ensemble_configuration.json: {e}")

            self.is_loaded = True
            print("FairGig AI ML Service: HistGradientBoosting and CatBoost loaded successfully.")

        except Exception as e:
            self.is_loaded = False
            self.load_error = str(e)
            print(f"FairGig AI ML Service Load Error: {e}")

    def predict_probabilities(self, df_features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates predicted success probabilities for candidate feature rows.
        Returns:
            (ensemble_probs, hgb_probs, cat_probs)
        """
        self.ensure_loaded()

        missing_columns = set(FEATURE_COLUMNS_27) - set(df_features.columns)
        if missing_columns:
            raise ValueError(
                f"Missing required model features: {', '.join(sorted(missing_columns))}"
            )
        if df_features.empty:
            empty = np.array([], dtype=float)
            return empty, empty, empty

        # CatBoost expects all 27 features with native categorical handling
        cat_df = df_features.loc[:, FEATURE_COLUMNS_27].copy()
        cat_probs = self.cat_model.predict_proba(cat_df)[:, 1]

        # HistGradientBoosting was trained on 25 numeric features (excluding task_type, required_skill)
        hgb_df = df_features[NUMERIC_COLUMNS_25].copy()
        hgb_probs = self.hgb_model.predict_proba(hgb_df)[:, 1]

        # Ensemble weights: 0.5 * HGB + 0.5 * CatBoost
        w_hgb = self.ensemble_weights[0] if len(self.ensemble_weights) >= 1 else 0.5
        w_cat = self.ensemble_weights[3] if len(self.ensemble_weights) >= 4 else 0.5
        ensemble_probs = w_hgb * hgb_probs + w_cat * cat_probs

        if not all(
            np.isfinite(probabilities).all()
            for probabilities in (ensemble_probs, hgb_probs, cat_probs)
        ):
            raise RuntimeError("ML models returned non-finite prediction values")
        if any(
            np.any((probabilities < 0) | (probabilities > 1))
            for probabilities in (ensemble_probs, hgb_probs, cat_probs)
        ):
            raise RuntimeError("ML models returned probabilities outside [0, 1]")

        return ensemble_probs, hgb_probs, cat_probs

    def get_status(self) -> Dict[str, Any]:
        try:
            self.ensure_loaded()
        except RuntimeError:
            pass
        return {
            "model_loaded": self.is_loaded,
            "hgb_loaded": self.hgb_model is not None,
            "cat_loaded": self.cat_model is not None,
            "ensemble_weights": self.ensemble_weights,
            "ensemble_threshold": self.ensemble_threshold,
            "total_features_expected": len(FEATURE_COLUMNS_27),
            "features_list": FEATURE_COLUMNS_27,
            "artifact_paths": {
                "cat_model": str(MODELS_DIR / "cat_model.joblib"),
                "all_models": str(MODELS_DIR / "all_trained_models.joblib"),
                "ensemble_config": str(MODELS_DIR / "ensemble_configuration.json")
            },
            "environment_status": "Operational" if self.is_loaded else f"Degraded: {self.load_error}"
        }

    def get_feature_importances(self) -> List[Dict[str, Any]]:
        """Returns feature importances from the CatBoost model."""
        self.ensure_loaded()

        importances = self.cat_model.get_feature_importance()
        result = []
        for name, val in zip(FEATURE_COLUMNS_27, importances):
            result.append({
                "feature": name,
                "importance": round(float(val), 4)
            })
        result.sort(key=lambda x: x["importance"], reverse=True)
        return result

    def get_calibration_curve_data(self) -> List[Dict[str, Any]]:
        """Calculates calibration curve points from held-out test predictions."""
        try:
            from sklearn.calibration import calibration_curve

            preds_file = PREDICTIONS_DIR / "ensemble_test.csv"
            y_file = PREDICTIONS_DIR / "y_test.csv"
            if preds_file.exists() and y_file.exists():
                p = pd.read_csv(preds_file)["ensemble_test"].values
                y = pd.read_csv(y_file)["y_test"].values
                prob_true, prob_pred = calibration_curve(y, p, n_bins=10, strategy="quantile")
                points = []
                for pt, pp in zip(prob_true, prob_pred):
                    points.append({
                        "predicted_probability": round(float(pp), 4),
                        "observed_frequency": round(float(pt), 4)
                    })
                return points
        except Exception as e:
            print(f"Error computing calibration curve: {e}")
        return []

# Singleton instance
model_service = ModelService()
