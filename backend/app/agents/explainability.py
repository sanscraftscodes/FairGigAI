import asyncio
import time
from app.services.ai_service import generate_agent_explanation
from typing import Dict, Any, List, Optional
from app.services.llm_explainability_service import (
    build_prompt_payload,
    SYSTEM_PROMPT,
    PROMPT_ENGINEERING_TECHNIQUE
)

class ExplainabilityAgent:
    name = "Explainability Agent"
    agent_id = "agent_explainability"
    role_description = "Synthesizes transparent, data-grounded justifications explaining why the selected worker was chosen over alternatives using prompt-engineered LLM reasoning."
    stage_number = 6

    def run(
        self,
        task: Any,
        selected_worker: Optional[Dict[str, Any]],
        ranked_candidates: List[Dict[str, Any]],
        policy: str = "WAFR",
        lambda_val: float = 0.08
    ) -> Dict[str, Any]:
        start_time = time.time()

        if not selected_worker:
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "role_description": self.role_description,
                "stage_number": self.stage_number,
                "status": "Completed",
                "duration_ms": 0.0,
                "input_summary": {"has_selected_worker": False},
                "output_summary": {
                    "explanation": "No eligible worker could be assigned. All candidates failed mandatory constraints.",
                    "executive_summary": "Allocation aborted: 0 eligible workers found for this task specification.",
                    "prompt_inspector": {
                        "technique": PROMPT_ENGINEERING_TECHNIQUE,
                        "system_prompt": SYSTEM_PROMPT
                    }
                }
            }

        # Identify runner-up candidate
        runner_up = ranked_candidates[1] if len(ranked_candidates) > 1 else None

        task_dict = {
            "task_id": getattr(task, "task_id", str(task)),
            "task_type": getattr(task, "task_type", "Standard"),
            "priority": getattr(task, "priority", "Medium"),
            "estimated_duration_min": getattr(task, "estimated_duration_min", 60),
            "package_weight_kg": getattr(task, "package_weight_kg", 5.0),
            "required_vehicle": getattr(task, "required_vehicle", "bike"),
            "payout": getattr(task, "base_payout", 25.0)
        }

        prompt_data = build_prompt_payload(task_dict, selected_worker, runner_up, policy, lambda_val)
        explanation = asyncio.run(generate_agent_explanation(prompt_data))

        duration_ms = (time.time() - start_time) * 1000

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role_description": self.role_description,
            "stage_number": self.stage_number,
            "status": "Completed",
            "duration_ms": round(duration_ms, 2),
            "input_summary": {
                "selected_worker_id": selected_worker["worker_id"],
                "policy": policy,
                "alternatives_count": len(ranked_candidates) - 1,
                "lambda_val": lambda_val
            },
            "output_summary": {
                "explanation_text": explanation["executive_summary"],
                "explanation_markdown": explanation["explanation_markdown"],
                "score_decomposition": prompt_data["selected_worker"]["score_decomposition"],
                "runner_up_comparison": explanation["runner_up_comparison"],
                "sdg8_audit": explanation["sdg8_audit"],
                "provider_used": explanation["provider_used"],
                "provider": explanation["provider"],
                "mode": explanation["mode"],
                "fallback_used": explanation["fallback_used"],
                "prompt_inspector": {
                    "system_prompt": SYSTEM_PROMPT.strip(),
                    "prompt_engineering_technique": PROMPT_ENGINEERING_TECHNIQUE,
                    "temperature": 0.2
                }
            }
        }
