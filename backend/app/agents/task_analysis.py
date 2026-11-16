import time
from typing import Dict, Any, List

class TaskAnalysisAgent:
    name = "Task Analysis Agent"
    agent_id = "agent_task_analysis"
    role_description = "Interprets task attributes, validates completeness, identifies constraints, and assesses data quality."
    stage_number = 1

    def run(self, task: Any) -> Dict[str, Any]:
        start_time = time.time()
        missing_fields = []
        warnings = []

        # Validate mandatory task fields
        for field in ["task_type", "pickup_lat", "pickup_lon", "estimated_duration_min", "deadline_min", "package_weight_kg", "required_skill"]:
            val = getattr(task, field, None)
            if val is None:
                missing_fields.append(field)

        # Check deadline vs duration sanity
        dur = float(getattr(task, "estimated_duration_min", 0) or 0)
        dl = float(getattr(task, "deadline_min", 0) or 0)
        if dl > 0 and dur > dl:
            warnings.append(f"Estimated duration ({dur:.1f}m) exceeds deadline ({dl:.1f}m)")

        # Check payment sanity
        payment = float(getattr(task, "payment", 0) or 0)
        if payment <= 0:
            warnings.append("Payment value is zero or unassigned")

        # Compute data quality score
        quality_score = 100
        quality_score -= len(missing_fields) * 20
        quality_score -= len(warnings) * 10
        quality_score = max(0, min(100, quality_score))

        structured_task = {
            "task_id": str(task.task_id),
            "task_type": str(task.task_type),
            "pickup_location": [float(task.pickup_lat), float(task.pickup_lon)],
            "destination_location": [float(task.destination_lat), float(task.destination_lon)],
            "estimated_duration_min": dur,
            "deadline_min": dl,
            "payment": payment,
            "package_weight_kg": float(getattr(task, "package_weight_kg", 5.0)),
            "vehicle_required": str(getattr(task, "vehicle_required", "none")),
            "required_skill": str(getattr(task, "required_skill", "driving")),
            "priority": str(getattr(task, "priority", "medium")),
            "priority_num": int(getattr(task, "priority_num", 1))
        }

        duration_ms = (time.time() - start_time) * 1000

        status = "Completed" if not missing_fields else "Failed"

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role_description": self.role_description,
            "stage_number": self.stage_number,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "input_summary": {
                "raw_task_id": str(task.task_id),
                "task_type": str(task.task_type)
            },
            "output_summary": {
                "structured_task": structured_task,
                "missing_fields": missing_fields,
                "warnings": warnings,
                "data_quality_score": quality_score
            },
            "error_message": f"Missing critical fields: {missing_fields}" if missing_fields else None
        }
