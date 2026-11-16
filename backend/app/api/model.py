from fastapi import APIRouter
from app.services.model_service import model_service

router = APIRouter(prefix="/model", tags=["Model"])

@router.get("/status")
def get_model_status():
    return model_service.get_status()

@router.get("/metrics")
def get_model_metrics():
    status = model_service.get_status()
    importances = model_service.get_feature_importances()
    calibration = model_service.get_calibration_curve_data()

    return {
        "research_metrics": {
            "roc_auc_approx": 0.9561,
            "pr_auc_approx": 0.2431,
            "brier_approx": 0.0187,
            "baseline_pr_auc": 0.0227,
            "counterfactual_switch_rate": 0.044,
            "sample_prevalence": "2.27% positive class prevalence across all candidate pairs"
        },
        "ensemble_configuration": {
            "components": {
                "HistGradientBoosting": status["ensemble_weights"][0] if len(status["ensemble_weights"]) > 0 else 0.5,
                "XGBoost": status["ensemble_weights"][1] if len(status["ensemble_weights"]) > 1 else 0.0,
                "LightGBM": status["ensemble_weights"][2] if len(status["ensemble_weights"]) > 2 else 0.0,
                "CatBoost": status["ensemble_weights"][3] if len(status["ensemble_weights"]) > 3 else 0.5
            },
            "ensemble_threshold": status["ensemble_threshold"]
        },
        "feature_importances": importances[:15],
        "calibration_curve": calibration,
        "notes": (
            "These metrics represent held-out task-grouped test evaluations from the research experiment. "
            "Because candidates were first filtered by hard eligibility, the overall PR-AUC is evaluated "
            "over all candidate pairs. Eligible-only ranking performance focuses specifically on viable workers."
        )
    }
