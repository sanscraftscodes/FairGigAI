import math
from typing import Dict, Any, List, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth in kilometers."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2)**2
    return 2 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))

def check_worker_eligibility(task: Any, worker: Any) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Evaluates hard feasibility constraints for a worker-task candidate pair.
    Returns:
        (is_eligible, ineligibility_reasons, check_details)
    """
    reasons = []

    # 1. Travel distance & deadline feasibility
    dist_km = haversine_distance(
        worker.current_lat, worker.current_lon,
        task.pickup_lat, task.pickup_lon
    )
    est_travel_min = (dist_km / 25.0) * 60.0
    est_total_min = est_travel_min + task.estimated_duration_min
    deadline_feasible = est_total_min <= task.deadline_min
    if not deadline_feasible:
        reasons.append(
            f"Deadline infeasible: Total est. time ({est_total_min:.1f}m: {est_travel_min:.1f}m travel + {task.estimated_duration_min:.1f}m duration) exceeds deadline ({task.deadline_min:.1f}m)"
        )

    # 2. Vehicle compatibility
    # Compatible if task requires none, matches worker vehicle, or bike required and worker has scooter
    t_veh = (task.vehicle_required or "none").lower()
    w_veh = (worker.vehicle_type or "").lower()
    vehicle_match = (
        t_veh == "none" or
        w_veh == t_veh or
        (t_veh == "bike" and w_veh == "scooter")
    )
    if not vehicle_match:
        reasons.append(
            f"Vehicle incompatible: Task requires '{t_veh}', worker has '{w_veh}'"
        )

    # 3. Required skill match
    req_skill = (task.required_skill or "").strip().lower()
    worker_skills = [s.strip().lower() for s in (worker.skills or "").split(",") if s.strip()]
    skill_match = req_skill in worker_skills
    if not skill_match:
        reasons.append(
            f"Missing required skill: Task requires '{req_skill}', worker has [{', '.join(worker_skills)}]"
        )

    # 4. Package weight capacity
    weight_ok = float(worker.max_package_weight_kg) >= float(task.package_weight_kg)
    if not weight_ok:
        reasons.append(
            f"Package exceeds capacity: Task package is {task.package_weight_kg:.1f}kg, worker max capacity is {worker.max_package_weight_kg:.1f}kg"
        )

    # 5. Availability status & vehicle readiness
    avail_status = (worker.availability_status or "").lower()
    is_available = avail_status == "available" and bool(worker.vehicle_available)
    if not is_available:
        if avail_status != "available":
            reasons.append(f"Worker status is currently '{avail_status}' (must be 'available')")
        if not bool(worker.vehicle_available):
            reasons.append("Worker vehicle is currently marked unavailable")

    is_eligible = (
        vehicle_match and
        skill_match and
        weight_ok and
        is_available and
        deadline_feasible
    )

    details = {
        "distance_km": round(dist_km, 2),
        "est_travel_min": round(est_travel_min, 1),
        "est_total_min": round(est_total_min, 1),
        "vehicle_match": vehicle_match,
        "skill_match": skill_match,
        "weight_ok": weight_ok,
        "available": is_available,
        "deadline_feasible": deadline_feasible
    }

    return is_eligible, reasons, details
