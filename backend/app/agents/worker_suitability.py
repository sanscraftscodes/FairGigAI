import time
from typing import Dict, Any, List
from app.services.eligibility import check_worker_eligibility
from app.services.feature_builder import extract_candidate_features

class WorkerSuitabilityAgent:
    name = "Worker Suitability Agent"
    agent_id = "agent_worker_suitability"
    role_description = "Evaluates worker compatibility, verifies hard feasibility constraints, filters candidates, and provides granular ineligibility reasons."
    stage_number = 2

    def run(self, task: Any, workers: List[Any], max_candidates: int = 100) -> Dict[str, Any]:
        start_time = time.time()

        eligible_candidates = []
        ineligible_candidates = []
        reasons_tally = {}

        candidate_pool = workers if not max_candidates or max_candidates >= len(workers) else workers[:max_candidates]
        for w in candidate_pool:
            is_eligible, reasons, details = check_worker_eligibility(task, w)
            feat = extract_candidate_features(task, w)

            candidate_summary = {
                "worker_id": str(w.worker_id),
                "distance_km": details["distance_km"],
                "experience_years": float(w.experience_years),
                "vehicle_type": str(w.vehicle_type),
                "availability_status": str(w.availability_status),
                "working_hours_7d": float(w.working_hours_7d),
                "skills": str(w.skills),
                "reasons": reasons,
                "features": feat
            }

            if is_eligible:
                eligible_candidates.append(candidate_summary)
            else:
                ineligible_candidates.append(candidate_summary)
                for r in reasons:
                    # Categorize reason for tallying
                    cat = r.split(":")[0] if ":" in r else r
                    reasons_tally[cat] = reasons_tally.get(cat, 0) + 1

        duration_ms = (time.time() - start_time) * 1000

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role_description": self.role_description,
            "stage_number": self.stage_number,
            "status": "Completed" if eligible_candidates else "Completed",
            "duration_ms": round(duration_ms, 2),
            "input_summary": {
                "task_id": str(task.task_id),
                "candidates_examined": min(len(workers), max_candidates)
            },
            "output_summary": {
                "total_examined": min(len(workers), max_candidates),
                "eligible_count": len(eligible_candidates),
                "ineligible_count": len(ineligible_candidates),
                "ineligibility_breakdown": reasons_tally,
                "sample_eligible_ids": [c["worker_id"] for c in eligible_candidates[:5]]
            },
            "eligible_candidates": eligible_candidates,
            "ineligible_candidates": ineligible_candidates
        }
