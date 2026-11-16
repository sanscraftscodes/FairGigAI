import csv
import importlib.util
import math
import os
import json
import sys
import numpy as np
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Tuple, Optional, List

from app.config import MODELS_DIR, PREDICTIONS_DIR
from app.services.feature_builder import NUMERIC_COLUMNS_25, FEATURE_COLUMNS_27


class ModelService:
    def __init__(self):
        self.cat_model = None   # pure-Python catboost inference module
        self.hgb_model = None   # JSON-based HGB inference artifact
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
            # --- Load pure-Python CatBoost model ---
            cat_py_path = MODELS_DIR / "cat_model_python.py"
            if not cat_py_path.exists():
                raise FileNotFoundError(
                    f"CatBoost Python inference artifact not found at {cat_py_path}"
                )
            spec = importlib.util.spec_from_file_location("cat_model_python", cat_py_path)
            cat_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cat_module)
            if not hasattr(cat_module, "apply_catboost_model"):
                raise ValueError(
                    "cat_model_python.py does not expose apply_catboost_model()"
                )
            self.cat_model = cat_module

            # --- Load HistGradientBoosting JSON inference artifact ---
            hgb_path = MODELS_DIR / "hist_gradient_boosting.json"
            if not hgb_path.exists():
                raise FileNotFoundError(
                    f"HistGradientBoosting inference artifact not found at {hgb_path}"
                )
            with open(hgb_path, "r", encoding="utf-8") as model_file:
                self.hgb_model = json.load(model_file)
            self._validate_hgb_artifact(self.hgb_model)

            # --- Load ensemble configuration ---
            ensemble_config_path = MODELS_DIR / "ensemble_configuration.json"
            if ensemble_config_path.exists():
                try:
                    with open(ensemble_config_path, "r") as f:
                        cfg = json.load(f)
                        if "best_weights" in cfg and isinstance(cfg["best_weights"], list):
                            self.ensemble_weights = cfg["best_weights"]
                        if "ensemble_threshold" in cfg and isinstance(
                            cfg["ensemble_threshold"], (int, float)
                        ):
                            self.ensemble_threshold = float(cfg["ensemble_threshold"])
                except Exception as e:
                    print(f"Warning reading ensemble_configuration.json: {e}")

            self.is_loaded = True
            print(
                "FairGig AI ML Service: HistGradientBoosting and CatBoost loaded successfully."
            )

        except Exception as e:
            self.is_loaded = False
            self.load_error = str(e)
            print(f"FairGig AI ML Service Load Error: {e}")

    # ------------------------------------------------------------------
    # HGB inference (pure NumPy — unchanged)
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_hgb_artifact(model: Dict[str, Any]) -> None:
        if model.get("format_version") != 1:
            raise ValueError("Unsupported HistGradientBoosting inference artifact version")
        if model.get("feature_columns") != NUMERIC_COLUMNS_25:
            raise ValueError(
                "HistGradientBoosting feature ordering does not match the application"
            )
        if model.get("classes") != [0, 1]:
            raise ValueError(
                "HistGradientBoosting artifact must contain binary classes [0, 1]"
            )
        if not model.get("trees") or not isinstance(model.get("trees"), list):
            raise ValueError("HistGradientBoosting inference artifact contains no trees")
        for tree in model["trees"]:
            if not tree or any(len(node) != 7 for node in tree):
                raise ValueError(
                    "HistGradientBoosting inference artifact contains an invalid tree"
                )
            for node in tree:
                if not node[6] and not 0 <= node[1] < len(NUMERIC_COLUMNS_25):
                    raise ValueError(
                        "HistGradientBoosting tree references an invalid feature"
                    )

    def _predict_hgb_probabilities(self, numeric_features: np.ndarray) -> np.ndarray:
        model = self.hgb_model
        raw_predictions = np.full(
            numeric_features.shape[0],
            float(model["baseline_prediction"]),
            dtype=np.float64,
        )
        for tree in model["trees"]:
            for row_index, row in enumerate(numeric_features):
                node_index = 0
                while True:
                    node = tree[node_index]
                    if node[6]:
                        raw_predictions[row_index] += float(node[0])
                        break
                    value = row[int(node[1])]
                    if np.isnan(value):
                        node_index = int(node[4] if node[3] else node[5])
                    elif value <= float(node[2]):
                        node_index = int(node[4])
                    else:
                        node_index = int(node[5])

        probabilities = np.empty_like(raw_predictions)
        positive = raw_predictions >= 0
        probabilities[positive] = 1.0 / (1.0 + np.exp(-raw_predictions[positive]))
        exp_values = np.exp(raw_predictions[~positive])
        probabilities[~positive] = exp_values / (1.0 + exp_values)
        return probabilities

    # ------------------------------------------------------------------
    # CatBoost inference (pure Python — no catboost package at runtime)
    # ------------------------------------------------------------------

    def _predict_cat_probabilities(
        self, feature_rows: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Run CatBoost inference using the exported pure-Python module.

        The module's apply_catboost_model(float_features, cat_features) function
        expects:
          float_features: list of 25 numeric feature values in NUMERIC_COLUMNS_25 order
          cat_features:   list of 2 categorical strings [task_type, required_skill]
        and returns the raw log-odds score. We apply the sigmoid to get a probability.
        """
        cat_py = self.cat_model
        probs = np.empty(len(feature_rows), dtype=np.float64)
        for i, row in enumerate(feature_rows):
            float_vals = [float(row[col]) for col in NUMERIC_COLUMNS_25]
            cat_vals = [str(row["task_type"]), str(row["required_skill"])]
            raw_score = cat_py.apply_catboost_model(float_vals, cat_vals)
            # Numerically-stable sigmoid
            if raw_score >= 0:
                probs[i] = 1.0 / (1.0 + math.exp(-raw_score))
            else:
                exp_val = math.exp(raw_score)
                probs[i] = exp_val / (1.0 + exp_val)
        return probs

    # ------------------------------------------------------------------
    # Public ensemble predict
    # ------------------------------------------------------------------

    def predict_probabilities(
        self, feature_rows: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates predicted success probabilities for candidate feature rows.
        Returns:
            (ensemble_probs, hgb_probs, cat_probs)
        """
        self.ensure_loaded()

        missing_columns = set()
        for row in feature_rows:
            missing_columns.update(set(FEATURE_COLUMNS_27) - set(row))
        if missing_columns:
            raise ValueError(
                f"Missing required model features: {', '.join(sorted(missing_columns))}"
            )
        if not feature_rows:
            empty = np.array([], dtype=float)
            return empty, empty, empty

        cat_probs = self._predict_cat_probabilities(feature_rows)

        numeric_features = np.asarray(
            [
                [row[column] for column in NUMERIC_COLUMNS_25]
                for row in feature_rows
            ],
            dtype=np.float64,
        )
        hgb_probs = self._predict_hgb_probabilities(numeric_features)

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

    # ------------------------------------------------------------------
    # Status / metadata
    # ------------------------------------------------------------------

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
                "cat_model_python": str(MODELS_DIR / "cat_model_python.py"),
                "hgb_inference": str(MODELS_DIR / "hist_gradient_boosting.json"),
                "ensemble_config": str(MODELS_DIR / "ensemble_configuration.json"),
            },
            "environment_status": "Operational"
            if self.is_loaded
            else f"Degraded: {self.load_error}",
        }

    def get_feature_importances(self) -> List[Dict[str, Any]]:
        """
        Returns approximate feature importances from the HGB model.
        Since we no longer load the catboost package at runtime, we derive
        importances from the HGB JSON artifact's feature usage frequency.
        """
        self.ensure_loaded()
        # Count how many times each feature is used as a split in the HGB trees
        usage = {col: 0 for col in NUMERIC_COLUMNS_25}
        for tree in self.hgb_model.get("trees", []):
            for node in tree:
                if not node[6]:  # not a leaf
                    feat_idx = int(node[1])
                    if 0 <= feat_idx < len(NUMERIC_COLUMNS_25):
                        usage[NUMERIC_COLUMNS_25[feat_idx]] += 1

        total = max(sum(usage.values()), 1)
        result = [
            {"feature": col, "importance": round(cnt / total * 100, 4)}
            for col, cnt in usage.items()
        ]
        # Add categorical features with zero usage (HGB doesn't use them)
        result.append({"feature": "task_type", "importance": 0.0})
        result.append({"feature": "required_skill", "importance": 0.0})
        result.sort(key=lambda x: x["importance"], reverse=True)
        return result

    def get_calibration_curve_data(self) -> List[Dict[str, Any]]:
        """Calculates calibration curve points from held-out test predictions."""
        try:
            preds_file = PREDICTIONS_DIR / "ensemble_test.csv"
            y_file = PREDICTIONS_DIR / "y_test.csv"
            if preds_file.exists() and y_file.exists():
                with open(preds_file, newline="", encoding="utf-8") as file:
                    predictions = np.asarray(
                        [float(row["ensemble_test"]) for row in csv.DictReader(file)]
                    )
                with open(y_file, newline="", encoding="utf-8") as file:
                    labels = np.asarray(
                        [float(row["y_test"]) for row in csv.DictReader(file)]
                    )
                if predictions.size != labels.size or predictions.size == 0:
                    return []
                bin_edges = np.percentile(predictions, np.linspace(0, 100, 11))
                bin_edges[0] -= 1e-8
                bin_ids = np.searchsorted(bin_edges[1:-1], predictions)
                prob_true = []
                prob_pred = []
                for bin_id in np.unique(bin_ids):
                    mask = bin_ids == bin_id
                    prob_true.append(float(np.mean(labels[mask])))
                    prob_pred.append(float(np.mean(predictions[mask])))
                points = []
                for pt, pp in zip(prob_true, prob_pred):
                    points.append(
                        {
                            "predicted_probability": round(float(pp), 4),
                            "observed_frequency": round(float(pt), 4),
                        }
                    )
                return points
        except Exception as e:
            print(f"Error computing calibration curve: {e}")
        return []


# Singleton instance
model_service = ModelService()
