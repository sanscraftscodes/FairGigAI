import math
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from app.services.eligibility import check_worker_eligibility, haversine_distance
from app.services.feature_builder import extract_candidate_features, build_features_dataframe
from app.services.model_service import model_service
from app.services.fairness_service import (
    compute_efficiency, compute_opportunity_credit, compute_workload_pressure,
    compute_wafr_score, calculate_jain_index, calculate_gini_index
)
from app.schemas.allocation import CandidateEvaluation, AllocationResponse

def evaluate_candidates_for_task(
    task: Any,
    workers: List[Any],
    lambda_val: float = 0.08,
    policy: str = "WAFR",
    max_candidates: int = 100
) -> Dict[str, Any]:
    """
    Evaluates worker candidates for a given task through eligibility, ML prediction, and fairness scoring.
    """
    candidate_evals = []
    eligible_workers = []
    eligible_feature_rows = []

    # Step 1: Evaluate eligibility for each worker
    for w in workers:
        is_eligible, reasons, details = check_worker_eligibility(task, w)
        if is_eligible:
            eligible_workers.append(w)
            feat = extract_candidate_features(task, w)
            eligible_feature_rows.append(feat)

        candidate_evals.append({
            "worker_id": str(w.worker_id),
            "eligible": is_eligible,
            "ineligibility_reasons": reasons,
            "distance_km": details["distance_km"],
            "experience_years": float(w.experience_years),
            "current_workload_hours": float(w.working_hours_7d),
            "vehicle_type": str(w.vehicle_type),
            "availability_status": str(w.availability_status),
            "recent_exposure": float(w.recent_exposure),
            "predicted_success": None,
            "efficiency": None,
            "opportunity_credit": None,
            "workload_pressure": None,
            "wafr_score": None,
            "hgb_prob": None,
            "cat_prob": None,
            "rank": 9999
        })

    total_examined = len(candidate_evals)
    eligible_count = len(eligible_workers)
    ineligible_count = total_examined - eligible_count

    # If no eligible workers found, return early
    if eligible_count == 0:
        return {
            "task_id": str(task.task_id),
            "policy": policy,
            "lambda_val": lambda_val,
            "total_candidates_examined": total_examined,
            "eligible_count": 0,
            "ineligible_count": ineligible_count,
            "selected_worker": None,
            "top_candidates": candidate_evals[:15],
            "decision_summary": "No eligible workers found for this task.",
            "detailed_explanation": (
                "All examined workers failed at least one hard feasibility constraint "
                "(e.g., vehicle incompatibility, missing required skill, capacity limitation, "
                "or deadline infeasibility). No assignment could be made."
            ),
            "status": "no_eligible_workers"
        }

    # Step 2: Run ML Inference on eligible workers
    df_features = build_features_dataframe(eligible_feature_rows)
    ens_probs, hgb_probs, cat_probs = model_service.predict_probabilities(df_features)

    # Step 3: Compute Fairness & Efficiency signals
    distances = np.array([row["distance_km"] for row in eligible_feature_rows])
    pressures = np.array([row["deadline_pressure"] for row in eligible_feature_rows])
    exposures = np.array([w.recent_exposure for w in eligible_workers])
    work_hours = np.array([w.working_hours_7d for w in eligible_workers])

    efficiencies = compute_efficiency(distances, pressures)
    opportunity_credits = compute_opportunity_credit(exposures)
    median_work_hours = float(np.median(work_hours)) if len(work_hours) > 0 else 20.0
    workload_pressures = compute_workload_pressure(work_hours, median_work_hours)

    # Step 4: Populate scores and calculate ranking metric
    eligible_eval_map = {}
    for i, w in enumerate(eligible_workers):
        wid = str(w.worker_id)
        p_succ = float(ens_probs[i])
        eff = float(efficiencies[i])
        opp = float(opportunity_credits[i])
        w_press = float(workload_pressures[i])
        wafr = compute_wafr_score(p_succ, eff, opp, w_press, lambda_val)

        eval_data = {
            "predicted_success": round(p_succ, 4),
            "efficiency": round(eff, 4),
            "opportunity_credit": round(opp, 4),
            "workload_pressure": round(w_press, 4),
            "wafr_score": round(wafr, 4),
            "hgb_prob": round(float(hgb_probs[i]), 4),
            "cat_prob": round(float(cat_probs[i]), 4),
        }
        eligible_eval_map[wid] = eval_data

    # Merge scores back into candidate list
    for c in candidate_evals:
        wid = c["worker_id"]
        if wid in eligible_eval_map:
            c.update(eligible_eval_map[wid])

    # Step 5: Rank eligible candidates based on selected policy
    eligible_candidates = [c for c in candidate_evals if c["eligible"]]

    if policy == "Nearest Eligible":
        eligible_candidates.sort(key=lambda x: (x["distance_km"], -x["predicted_success"]))
    elif policy == "ML-Only":
        eligible_candidates.sort(key=lambda x: (-x["predicted_success"], x["distance_km"]))
    else:  # WAFR default
        eligible_candidates.sort(key=lambda x: (-x["wafr_score"], -x["predicted_success"]))

    # Assign ranks
    for rank_idx, c in enumerate(eligible_candidates, 1):
        c["rank"] = rank_idx

    selected_worker = eligible_candidates[0] if eligible_candidates else None

    # Step 6: Generate structured, data-grounded explanation
    if selected_worker:
        decision_summary = (
            f"Worker {selected_worker['worker_id']} selected under policy '{policy}' "
            f"(Predicted Success: {selected_worker['predicted_success']:.1%}, "
            f"WAFR Score: {selected_worker['wafr_score']:.4f}, Distance: {selected_worker['distance_km']:.1f}km)."
        )
        detailed_explanation = (
            f"Worker {selected_worker['worker_id']} was selected because they satisfied all mandatory constraints "
            f"(vehicle: {selected_worker['vehicle_type']}, available, deadline feasible). "
            f"Under policy '{policy}', they achieved the top ranking with a predicted task success probability of "
            f"{selected_worker['predicted_success']:.1%} (CatBoost: {selected_worker['cat_prob']:.4f}, "
            f"HistGradientBoosting: {selected_worker['hgb_prob']:.4f}), operational efficiency of "
            f"{selected_worker['efficiency']:.4f}, opportunity credit of {selected_worker['opportunity_credit']:.4f}, "
            f"and workload pressure of {selected_worker['workload_pressure']:.4f} (recent 7d workload: {selected_worker['current_workload_hours']:.1f}h). "
            f"At fairness parameter λ = {lambda_val:.2f}, this candidate represents the optimal balance of efficiency and equity."
        )
    else:
        decision_summary = "No allocation possible."
        detailed_explanation = "No eligible workers found."

    # Sort full list: eligible ranked first, followed by ineligible
    ineligible_candidates = [c for c in candidate_evals if not c["eligible"]]
    full_ranked = eligible_candidates + ineligible_candidates

    return {
        "task_id": str(task.task_id),
        "policy": policy,
        "lambda_val": lambda_val,
        "total_candidates_examined": total_examined,
        "eligible_count": eligible_count,
        "ineligible_count": ineligible_count,
        "selected_worker": selected_worker,
        "top_candidates": full_ranked[:20],
        "decision_summary": decision_summary,
        "detailed_explanation": detailed_explanation,
        "status": "preview"
    }

def simulate_policy_comparison(tasks: List[Any], workers: List[Any], lambda_val: float = 0.08) -> List[Dict[str, Any]]:
    """
    Runs policy comparison across multiple tasks for:
    - Nearest Eligible
    - ML-Only
    - WAFR (at specified lambda)
    """
    policies = ["Nearest Eligible", "ML-Only", f"WAFR (λ={lambda_val:.2f})"]
    results = []

    for pol_name in ["Nearest Eligible", "ML-Only", "WAFR"]:
        chosen_records = []
        for task in tasks:
            res = evaluate_candidates_for_task(task, workers, lambda_val=lambda_val, policy=pol_name, max_candidates=50)
            if res["selected_worker"]:
                chosen_records.append(res["selected_worker"])

        if not chosen_records:
            continue

        worker_ids = [r["worker_id"] for r in chosen_records]
        exposure_series = pd.Series(worker_ids).value_counts()
        total_unique_workers = len(workers)
        active_workers_count = len(exposure_series)

        jain = calculate_jain_index(exposure_series)
        gini = calculate_gini_index(exposure_series)
        coverage = active_workers_count / max(1, total_unique_workers)
        zero_exposure = 1.0 - coverage

        mean_dist = float(np.mean([r["distance_km"] for r in chosen_records]))
        mean_pred = float(np.mean([r["predicted_success"] for r in chosen_records]))
        mean_eff = float(np.mean([r["efficiency"] for r in chosen_records]))

        display_name = f"WAFR (λ={lambda_val:.2f})" if pol_name == "WAFR" else pol_name

        results.append({
            "policy": display_name,
            "lambda_val": lambda_val if pol_name == "WAFR" else None,
            "tasks_allocated": len(chosen_records),
            "mean_distance_km": round(mean_dist, 2),
            "mean_predicted_success": round(mean_pred, 4),
            "jain_exposure": round(jain, 4),
            "gini_exposure": round(gini, 4),
            "worker_coverage": round(coverage, 4),
            "zero_exposure_rate": round(zero_exposure, 4),
            "efficiency_avg": round(mean_eff, 4)
        })

    return results

def run_lambda_sweep(tasks: List[Any], workers: List[Any], lambdas: Optional[List[float]] = None) -> List[Dict[str, Any]]:
    """
    Runs a fairness coefficient sweep across lambda values to measure the trade-off.
    """
    if lambdas is None:
        lambdas = [0.0, 0.04, 0.08, 0.12, 0.16, 0.20, 0.25, 0.30, 0.40, 0.50]

    sweep_points = []
    total_unique_workers = len(workers)

    for lam in lambdas:
        chosen_records = []
        for task in tasks:
            res = evaluate_candidates_for_task(task, workers, lambda_val=lam, policy="WAFR", max_candidates=50)
            if res["selected_worker"]:
                chosen_records.append(res["selected_worker"])

        if not chosen_records:
            continue

        worker_ids = [r["worker_id"] for r in chosen_records]
        exposure_series = pd.Series(worker_ids).value_counts()
        active_count = len(exposure_series)

        jain = calculate_jain_index(exposure_series)
        gini = calculate_gini_index(exposure_series)
        coverage = active_count / max(1, total_unique_workers)
        mean_pred = float(np.mean([r["predicted_success"] for r in chosen_records]))
        mean_dist = float(np.mean([r["distance_km"] for r in chosen_records]))

        sweep_points.append({
            "lambda_val": round(lam, 2),
            "jain_exposure": round(jain, 4),
            "gini_exposure": round(gini, 4),
            "worker_coverage": round(coverage, 4),
            "mean_predicted_success": round(mean_pred, 4),
            "mean_distance_km": round(mean_dist, 2)
        })

    return sweep_points
