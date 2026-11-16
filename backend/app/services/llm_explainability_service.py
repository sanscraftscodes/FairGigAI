import json
from typing import Any, Dict, Optional

SYSTEM_PROMPT = """You are FairGig AI's Senior Algorithmic Fairness and Task Allocation Auditor, aligned with UN Sustainable Development Goal 8 (Decent Work and Economic Growth).
Provide concise, transparent, mathematically grounded justifications for gig worker task assignments.
Use only the supplied worker attributes, ML ensemble predictions (HistGradientBoosting + CatBoost), operational constraints, and Workload-Aware Fair Ranking (WAFR) values. Do not invent facts or allocation results.
Do not reveal private chain-of-thought or hidden reasoning. Present only the decision, relevant supplied factors, score calculations, and concise conclusions.
Strictly adhere to:
1. Objectivity: Explain mathematical contributions without hyperbole.
2. Comparative Analysis: Explain precisely why the selected winner was chosen over the runner-up candidate.
3. Ethical Governance (UN SDG 8): Highlight how this allocation balances platform efficiency with worker burnout prevention and opportunity fairness.
"""

PROMPT_ENGINEERING_TECHNIQUE = (
    "Role-Conditioned System Prompting + Zero-Shot Structured Explanation + "
    "Counterfactual Runner-Up Comparison"
)


def build_prompt_payload(
    task: Dict[str, Any],
    selected_worker: Dict[str, Any],
    runner_up: Optional[Dict[str, Any]],
    policy: str,
    lambda_val: float,
) -> Dict[str, Any]:
    p_succ = float(selected_worker.get("predicted_success", 0.0))
    eff = float(selected_worker.get("efficiency", 0.0))
    opp = float(selected_worker.get("opportunity_credit", 0.0))
    press = float(selected_worker.get("workload_pressure", 0.0))

    ml_contrib = round(0.70 * p_succ, 4)
    eff_contrib = round(0.30 * eff, 4)
    opp_contrib = round(lambda_val * opp, 4)
    workload_penalty = round(-lambda_val * press, 4)
    total_wafr = round(ml_contrib + eff_contrib + opp_contrib + workload_penalty, 4)

    prompt_data = {
        "task": {
            "task_id": task.get("task_id"),
            "task_type": task.get("task_type"),
            "priority": task.get("priority"),
            "estimated_duration_min": task.get("estimated_duration_min"),
            "package_weight_kg": task.get("package_weight_kg"),
            "required_vehicle": task.get("required_vehicle"),
            "payout": task.get("base_payout", task.get("payout", 0.0)),
        },
        "selected_worker": {
            "worker_id": selected_worker.get("worker_id"),
            "vehicle_type": selected_worker.get("vehicle_type"),
            "experience_years": selected_worker.get("experience_years"),
            "distance_km": selected_worker.get("distance_km"),
            "current_workload_hours": selected_worker.get(
                "current_workload_hours", selected_worker.get("working_hours_7d", 0.0)
            ),
            "historical_acceptance_rate": selected_worker.get(
                "historical_acceptance_rate", 0.95
            ),
            "predicted_success_prob": p_succ,
            "efficiency_score": eff,
            "opportunity_credit": opp,
            "workload_pressure": press,
            "wafr_score": total_wafr,
            "score_decomposition": {
                "ml_success_weight_70pct": ml_contrib,
                "efficiency_weight_30pct": eff_contrib,
                "opportunity_credit_plus_lambda": opp_contrib,
                "workload_penalty_minus_lambda": workload_penalty,
                "lambda_coefficient": lambda_val,
                "policy": policy,
            },
        },
        "runner_up": None,
    }

    if runner_up:
        r_p_succ = float(runner_up.get("predicted_success", 0.0))
        r_eff = float(runner_up.get("efficiency", 0.0))
        r_opp = float(runner_up.get("opportunity_credit", 0.0))
        r_press = float(runner_up.get("workload_pressure", 0.0))
        r_wafr = round(
            0.70 * r_p_succ + 0.30 * r_eff + lambda_val * r_opp - lambda_val * r_press,
            4,
        )

        prompt_data["runner_up"] = {
            "worker_id": runner_up.get("worker_id"),
            "vehicle_type": runner_up.get("vehicle_type"),
            "experience_years": runner_up.get("experience_years"),
            "distance_km": runner_up.get("distance_km"),
            "current_workload_hours": runner_up.get(
                "current_workload_hours", runner_up.get("working_hours_7d", 0.0)
            ),
            "predicted_success_prob": r_p_succ,
            "efficiency_score": r_eff,
            "opportunity_credit": r_opp,
            "workload_pressure": r_press,
            "wafr_score": r_wafr,
            "deltas_vs_winner": {
                "wafr_score_delta": round(total_wafr - r_wafr, 4),
                "success_prob_delta": round(p_succ - r_p_succ, 4),
                "distance_delta_km": round(
                    float(selected_worker.get("distance_km", 0.0))
                    - float(runner_up.get("distance_km", 0.0)),
                    2,
                ),
                "workload_hours_delta": round(
                    float(selected_worker.get("current_workload_hours", 0.0))
                    - float(runner_up.get("current_workload_hours", 0.0)),
                    1,
                ),
            },
        }

    return prompt_data


def build_user_prompt(prompt_data: Dict[str, Any]) -> str:
    return f"""### FAIRGIG ALLOCATION EXPLAINABILITY REQUEST
Generate a concise, four-part explanation using only the supplied allocation data:
1. EXECUTIVE SUMMARY: Rationale for selecting Worker {prompt_data['selected_worker']['worker_id']}.
2. MATHEMATICAL SCORE DECOMPOSITION: Explain the supplied WAFR terms (ML Success, Efficiency, Opportunity, Workload Penalty).
3. RUNNER-UP COMPARATIVE CONTRAST: Compare the selected worker with the supplied runner-up metrics and deltas ({(prompt_data.get('runner_up') or {}).get('worker_id', 'None')}).
4. UN SDG 8 ALIGNMENT: Briefly describe relevant supplied fairness factors.
Do not provide private chain-of-thought, hidden reasoning, or unsupported facts.

CONTEXT DATA:
{json.dumps(prompt_data, indent=2)}

Format your response in structured markdown with headings:
## 1. Executive Allocation Summary
## 2. Mathematical Score Decomposition
## 3. Runner-Up Comparative Analysis
## 4. UN SDG 8 Alignment & Ethical Audit
"""


def generate_deterministic_explanation(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    sel = prompt_data["selected_worker"]
    tsk = prompt_data["task"]
    rup = prompt_data.get("runner_up")
    decomp = sel["score_decomposition"]

    p_pct = sel["predicted_success_prob"] * 100
    w_id = sel["worker_id"]
    policy = decomp["policy"]
    lam = decomp["lambda_coefficient"]

    exec_summary = (
        f"Worker **{w_id}** was allocated task **{tsk['task_id']}** ({tsk['task_type']}) under the **{policy} policy** "
        f"with fairness coefficient lambda = {lam:.2f}. The candidate satisfied all mandatory constraints (vehicle compatibility: {sel['vehicle_type']}, "
        f"travel radius: {sel['distance_km']} km) and achieved the highest composite score of **{sel['wafr_score']:.4f}** with an ML-predicted "
        f"completion probability of **{p_pct:.1f}%**."
    )

    math_breakdown = (
        f"- **ML Success Term (70% weight)**: $0.70 \\times {sel['predicted_success_prob']:.4f} = +{decomp['ml_success_weight_70pct']:.4f}$\n"
        f"- **Efficiency Term (30% weight)**: $0.30 \\times {sel['efficiency_score']:.4f} = +{decomp['efficiency_weight_30pct']:.4f}$ (Distance: {sel['distance_km']} km)\n"
        f"- **Opportunity Credit (+lambda)**: $+({lam:.2f} \\times {sel['opportunity_credit']:.4f}) = +{decomp['opportunity_credit_plus_lambda']:.4f}$ (Prevents opportunity starvation)\n"
        f"- **Workload Pressure Penalty (-lambda)**: $-({lam:.2f} \\times {sel['workload_pressure']:.4f}) = {decomp['workload_penalty_minus_lambda']:.4f}$ ({sel['current_workload_hours']:.1f} recent hours)\n"
        f"- **Final Composite WAFR Score**: **{sel['wafr_score']:.4f}**"
    )

    if rup:
        r_id = rup["worker_id"]
        deltas = rup.get("deltas_vs_winner", {})
        score_diff = deltas.get("wafr_score_delta", 0.0)
        p_diff = deltas.get("success_prob_delta", 0.0) * 100
        dist_diff = deltas.get("distance_delta_km", 0.0)
        hrs_diff = deltas.get("workload_hours_delta", 0.0)

        runner_up_analysis = (
            f"Compared to Runner-Up Candidate **{r_id}** (WAFR score: {rup['wafr_score']:.4f}):\n"
            f"- **Composite Score Advantage**: Selected worker leads by **+{score_diff:.4f}** points.\n"
            f"- **Predicted Success Delta**: {w_id} is **{'+' if p_diff >= 0 else ''}{p_diff:.1f}%** more likely to succeed "
            f"({p_pct:.1f}% vs {rup['predicted_success_prob']*100:.1f}%).\n"
            f"- **Distance & Workload Balance**: While {r_id} is located {abs(dist_diff):.1f} km {'closer' if dist_diff > 0 else 'farther'}, "
            f"{w_id} has worked {abs(hrs_diff):.1f} {'fewer' if hrs_diff < 0 else 'more'} hours recently, "
            f"yielding an operational and fairness trade-off based on the displayed metrics."
        )
    else:
        runner_up_analysis = "No secondary eligible candidate was available for counterfactual ranking comparison."

    sdg8_audit = (
        f"This decision supports **UN Sustainable Development Goal 8 (Decent Work & Economic Growth)**:\n"
        f"1. **Burnout Mitigation**: Applying a workload penalty of {decomp['workload_penalty_minus_lambda']:.4f} reflects the supplied workload signal.\n"
        f"2. **Inclusive Opportunity**: The supplied opportunity bonus is +{decomp['opportunity_credit_plus_lambda']:.4f}.\n"
        f"3. **Transparent Auditability**: The score terms and ranking metrics are shown for review."
    )

    full_markdown = (
        f"## 1. Executive Allocation Summary\n{exec_summary}\n\n"
        f"## 2. Mathematical Score Decomposition\n{math_breakdown}\n\n"
        f"## 3. Runner-Up Comparative Analysis\n{runner_up_analysis}\n\n"
        f"## 4. UN SDG 8 Alignment & Ethical Audit\n{sdg8_audit}"
    )

    return {
        "provider_used": "FairGig Offline Deterministic Fallback",
        "provider": "offline",
        "mode": "offline",
        "fallback_used": True,
        "explanation_markdown": full_markdown,
        "executive_summary": exec_summary,
        "math_breakdown": math_breakdown,
        "runner_up_comparison": runner_up_analysis,
        "sdg8_audit": sdg8_audit,
        "is_fallback": True,
    }
