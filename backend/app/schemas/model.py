from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ModelStatusResponse(BaseModel):
    model_loaded: bool
    hgb_loaded: bool
    cat_loaded: bool
    ensemble_weights: List[float]
    ensemble_threshold: float
    total_features_expected: int
    features_list: List[str]
    artifact_paths: Dict[str, str]
    environment_status: str

class ResearchMetricsResponse(BaseModel):
    roc_auc_approx: float
    pr_auc_approx: float
    brier_approx: float
    baseline_pr_auc: float
    counterfactual_switch_rate: float
    ensemble_weights: Dict[str, float]
    ensemble_threshold: float
    feature_importances: List[Dict[str, Any]]
    calibration_data: List[Dict[str, Any]]
    notes: str
