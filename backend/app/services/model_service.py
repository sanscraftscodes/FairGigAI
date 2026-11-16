import csv
import os
import json
import joblib
import numpy as np
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Tuple, Optional, List

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
            cat_path = MODELS_DIR / "cat_model.joblib"
            if cat_path.exists():
                self.cat_model = joblib.load(cat_path)
            else:
                raise FileNotFoundError(f"CatBoost model artifact not found at {cat_path}")

            hgb_path = MODELS_DIR / "hist_gradient_boosting.json"
            if not hgb_path.exists():
                raise FileNotFoundError(
                    f"HistGradientBoosting inference artifact not found at {hgb_path}"
                )
            with open(hgb_path, "r", encoding="utf-8") as model_file:
                self.hgb_model = json.load(model_file)
            self._validate_hgb_artifact(self.hgb_model)

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

    @staticmethod
    def _validate_hgb_artifact(model: Dict[str, Any]) -> None:
        if model.get("format_version") != 1:
            raise ValueError("Unsupported HistGradientBoosting inference artifact version")
        if model.get("feature_columns") != NUMERIC_COLUMNS_25:
            raise ValueError("HistGradientBoosting feature ordering does not match the application")
        if model.get("classes") != [0, 1]:
            raise ValueError("HistGradientBoosting artifact must contain binary classes [0, 1]")
        if not model.get("trees") or not isinstance(model.get("trees"), list):
            raise ValueError("HistGradientBoosting inference artifact contains no trees")
        for tree in model["trees"]:
            if not tree or any(len(node) != 7 for node in tree):
                raise ValueError("HistGradientBoosting inference artifact contains an invalid tree")
            for node in tree:
                if not node[6] and not 0 <= node[1] < len(NUMERIC_COLUMNS_25):
                    raise ValueError("HistGradientBoosting tree references an invalid feature")

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

    def predict_probabilities(self, feature_rows: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
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

        from catboost import Pool

        cat_rows = [
            [row[column] for column in FEATURE_COLUMNS_27]
            for row in feature_rows
        ]
        cat_pool = Pool(
            cat_rows,
            cat_features=[0, 1],
            feature_names=FEATURE_COLUMNS_27,
        )
        cat_probs = self.cat_model.predict_proba(cat_pool)[:, 1]

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
                "hgb_inference": str(MODELS_DIR / "hist_gradient_boosting.json"),
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
