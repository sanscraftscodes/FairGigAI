import json
from pathlib import Path
import sys

from joblib.numpy_pickle import NumpyUnpickler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.feature_builder import NUMERIC_COLUMNS_25


SOURCE = ROOT / "models" / "all_trained_models.joblib"
DESTINATION = ROOT / "models" / "hist_gradient_boosting.json"


class SafeUnpickler(NumpyUnpickler):
    def find_class(self, module, name):
        if "xgboost" in module:
            class DummyXGB:
                def __setstate__(self, state):
                    pass

            return DummyXGB
        return super().find_class(module, name)


def main():
    with open(SOURCE, "rb") as model_file:
        models = SafeUnpickler(str(SOURCE), model_file, True).load()

    model = models.get("HistGradientBoosting") if isinstance(models, dict) else None
    if model is None or list(model.classes_) != [0, 1]:
        raise ValueError("Expected the trained binary HistGradientBoosting model")
    if model.n_features_in_ != len(NUMERIC_COLUMNS_25):
        raise ValueError("HistGradientBoosting feature count does not match the application")

    trees = []
    for iteration in model._predictors:
        if len(iteration) != 1:
            raise ValueError("Expected one HistGradientBoosting tree per binary iteration")
        nodes = iteration[0].nodes
        if any(node["is_categorical"] for node in nodes):
            raise ValueError("Categorical HistGradientBoosting splits are not supported")
        trees.append(
            [
                [
                    float(node["value"]),
                    int(node["feature_idx"]),
                    float(node["num_threshold"]),
                    bool(node["missing_go_to_left"]),
                    int(node["left"]),
                    int(node["right"]),
                    bool(node["is_leaf"]),
                ]
                for node in nodes
            ]
        )

    artifact = {
        "format_version": 1,
        "feature_columns": NUMERIC_COLUMNS_25,
        "classes": [int(value) for value in model.classes_],
        "baseline_prediction": float(model._baseline_prediction[0][0]),
        "learning_rate": float(model.learning_rate),
        "trees": trees,
    }

    temporary_path = DESTINATION.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(artifact, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(DESTINATION)
    print(f"Wrote {DESTINATION} ({DESTINATION.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
