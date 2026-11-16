from typing import Any, Dict
import pandas as pd
from app.services.eligibility import haversine_distance

FEATURE_COLUMNS_27 = [
    "task_type",
    "required_skill",
    "priority_num",
    "estimated_duration_min",
    "deadline_min",
    "payment",
    "package_weight_kg",
    "distance_km",
    "deadline_pressure",
    "experience_years",
    "historical_success_7d",
    "historical_success_30d",
    "historical_success_90d",
    "cancellation_7d",
    "cancellation_30d",
    "delay_7d",
    "delay_30d",
    "work_hours_7d",
    "work_hours_30d",
    "workload_trend",
    "recent_exposure",
    "task_affinity",
    "skill_match",
    "vehicle_match",
    "weight_ok",
    "available",
    "deadline_feasible"
]

NUMERIC_COLUMNS_25 = [c for c in FEATURE_COLUMNS_27 if c not in ["task_type", "required_skill"]]

PRIORITY_MAP = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "urgent": 3
}

def extract_candidate_features(task: Any, worker: Any) -> Dict[str, Any]:
    """
    Extracts the exact 27 features expected by the trained ML pipeline for a (task, worker) pair.
    """
    dist_km = haversine_distance(
        worker.current_lat, worker.current_lon,
        task.pickup_lat, task.pickup_lon
    )
    pressure = float(task.estimated_duration_min) / (float(task.deadline_min) + 1e-6)

    t_veh = (task.vehicle_required or "none").lower()
    w_veh = (worker.vehicle_type or "").lower()
    vehicle_match = int(
        t_veh == "none" or
        w_veh == t_veh or
        (t_veh == "bike" and w_veh == "scooter")
    )

    req_skill = (task.required_skill or "").strip().lower()
    worker_skills = [s.strip().lower() for s in (worker.skills or "").split(",") if s.strip()]
    skill_match = int(req_skill in worker_skills)

    weight_ok = int(float(worker.max_package_weight_kg) >= float(task.package_weight_kg))

    avail_status = (worker.availability_status or "").lower()
    available = int(avail_status == "available" and bool(worker.vehicle_available))

    est_travel_min = (dist_km / 25.0) * 60.0
    est_total_min = est_travel_min + float(task.estimated_duration_min)
    deadline_feasible = int(est_total_min <= float(task.deadline_min))

    # Priority mapping
    priority_num = getattr(task, "priority_num", None)
    if priority_num is None:
        priority_num = PRIORITY_MAP.get(str(task.priority).lower(), 1)

    # Task affinity from worker record
    affinity_attr = f"success_{str(task.task_type).lower()}"
    affinity = getattr(worker, affinity_attr, None)
    if affinity is None or pd.isna(affinity):
        affinity = getattr(worker, "success_rate_30d", 0.75)

    row = {
        "task_type": str(task.task_type),
        "required_skill": str(task.required_skill),
        "priority_num": int(priority_num),
        "estimated_duration_min": float(task.estimated_duration_min),
        "deadline_min": float(task.deadline_min),
        "payment": float(task.payment),
        "package_weight_kg": float(task.package_weight_kg),
        "distance_km": float(dist_km),
        "deadline_pressure": float(pressure),
        "experience_years": float(worker.experience_years),
        "historical_success_7d": float(worker.success_rate_7d),
        "historical_success_30d": float(worker.success_rate_30d),
        "historical_success_90d": float(worker.success_rate_90d),
        "cancellation_7d": float(worker.cancellation_rate_7d),
        "cancellation_30d": float(worker.cancellation_rate_30d),
        "delay_7d": float(worker.avg_delay_min_7d),
        "delay_30d": float(worker.avg_delay_min_30d),
        "work_hours_7d": float(worker.working_hours_7d),
        "work_hours_30d": float(worker.working_hours_30d),
        "workload_trend": float(worker.workload_trend),
        "recent_exposure": float(worker.recent_exposure),
        "task_affinity": float(affinity),
        "skill_match": int(skill_match),
        "vehicle_match": int(vehicle_match),
        "weight_ok": int(weight_ok),
        "available": int(available),
        "deadline_feasible": int(deadline_feasible)
    }

    return row

def build_features_dataframe(candidate_rows: list) -> pd.DataFrame:
    """Builds a Pandas DataFrame with guaranteed column order."""
    df = pd.DataFrame(candidate_rows)
    return df[FEATURE_COLUMNS_27]
