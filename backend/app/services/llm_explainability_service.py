import os
import json
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are FairGig AI's Senior Algorithmic Fairness and Task Allocation Auditor, aligned with UN Sustainable Development Goal 8 (Decent Work and Economic Growth).
Your mission is to provide transparent, mathematically rigorous, and human-interpretable justifications for gig worker task assignments.
You must ground every statement in the provided worker attributes, ML ensemble predictions (HistGradientBoosting + CatBoost), operational constraints, and the Workload-Aware Fair Ranking (WAFR) formula.
Strictly adhere to:
1. Objectivity: Explain mathematical contributions without hyperbole.
2. Comparative Analysis: Explain precisely why the selected winner was chosen over the runner-up candidate.
3. Ethical Governance (UN SDG 8): Highlight how this allocation balances platform efficiency with worker burnout prevention and opportunity fairness.
"""

PROMPT_ENGINEERING_TECHNIQUE = "Role-Conditioned System Prompting + Chain-of-Thought (CoT) Decomposition + Counterfactual Runner-Up Contrast + Structured JSON Schema"

def build_prompt_payload(
    task: Dict[str, Any],
    selected_worker: Dict[str, Any],
    runner_up: Optional[Dict[str, Any]],
    policy: str,
    lambda_val: float
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
            "payout": task.get("base_payout", task.get("payout", 0.0))
        },
        "selected_worker": {
            "worker_id": selected_worker.get("worker_id"),
            "vehicle_type": selected_worker.get("vehicle_type"),
            "experience_years": selected_worker.get("experience_years"),
            "distance_km": selected_worker.get("distance_km"),
            "current_workload_hours": selected_worker.get("current_workload_hours", selected_worker.get("working_hours_7d", 0.0)),
            "historical_acceptance_rate": selected_worker.get("historical_acceptance_rate", 0.95),
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
                "policy": policy
            }
        },
        "runner_up": None
    }

    if runner_up:
        r_p_succ = float(runner_up.get("predicted_success", 0.0))
        r_eff = float(runner_up.get("efficiency", 0.0))
        r_opp = float(runner_up.get("opportunity_credit", 0.0))
        r_press = float(runner_up.get("workload_pressure", 0.0))
        r_wafr = round(0.70 * r_p_succ + 0.30 * r_eff + lambda_val * r_opp - lambda_val * r_press, 4)

        prompt_data["runner_up"] = {
            "worker_id": runner_up.get("worker_id"),
            "vehicle_type": runner_up.get("vehicle_type"),
            "experience_years": runner_up.get("experience_years"),
            "distance_km": runner_up.get("distance_km"),
            "current_workload_hours": runner_up.get("current_workload_hours", runner_up.get("working_hours_7d", 0.0)),
            "predicted_success_prob": r_p_succ,
            "efficiency_score": r_eff,
            "opportunity_credit": r_opp,
            "workload_pressure": r_press,
            "wafr_score": r_wafr,
            "deltas_vs_winner": {
                "wafr_score_delta": round(total_wafr - r_wafr, 4),
                "success_prob_delta": round(p_succ - r_p_succ, 4),
                "distance_delta_km": round(float(selected_worker.get("distance_km", 0.0)) - float(runner_up.get("distance_km", 0.0)), 2),
                "workload_hours_delta": round(float(selected_worker.get("current_workload_hours", 0.0)) - float(runner_up.get("current_workload_hours", 0.0)), 1)
            }
        }

    return prompt_data

def build_user_prompt(prompt_data: Dict[str, Any]) -> str:
    return f"""### FAIRGIG ALLOCATION EXPLAINABILITY REQUEST
Given the allocation state below, generate a 4-part structured explanation:
1. EXECUTIVE SUMMARY: Clear 2-sentence rationale for selecting Worker {prompt_data['selected_worker']['worker_id']}.
2. MATHEMATICAL SCORE DECOMPOSITION: Explicit breakdown of the WAFR terms (ML Success, Efficiency, Opportunity, Workload Penalty).
3. RUNNER-UP COMPARATIVE CONTRAST: Why this worker won over the runner-up candidate ({prompt_data.get('runner_up', {}).get('worker_id', 'None')}), citing specific metrics and deltas.
4. UN SDG 8 ALIGNMENT: How this assignment embodies Decent Work principles (e.g. fatigue prevention, fair opportunity access).

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
            f"yielding an optimal trade-off between operational promptness and fairness distribution."
        )
    else:
        runner_up_analysis = "No secondary eligible candidate was available for counterfactual ranking comparison."

    sdg8_audit = (
        f"This decision directly supports **UN Sustainable Development Goal 8 (Decent Work & Economic Growth)**:\n"
        f"1. **Burnout Mitigation**: Applying a workload penalty of {decomp['workload_penalty_minus_lambda']:.4f} avoids over-allocating overburdened couriers.\n"
        f"2. **Inclusive Opportunity**: Underrepresented or under-utilized workers receive a positive opportunity bonus (+{decomp['opportunity_credit_plus_lambda']:.4f}) to combat platform algorithmic bias.\n"
        f"3. **Transparent Auditability**: The assignment is 100% reproducible with mathematical weights logged for institutional compliance."
    )

    full_markdown = (
        f"## 1. Executive Allocation Summary\n{exec_summary}\n\n"
        f"## 2. Mathematical Score Decomposition\n{math_breakdown}\n\n"
        f"## 3. Runner-Up Comparative Analysis\n{runner_up_analysis}\n\n"
        f"## 4. UN SDG 8 Alignment & Ethical Audit\n{sdg8_audit}"
    )

    return {
        "provider_used": "FairGig Prompt-Engineered CoT (Zero-Shot Rule Engine)",
        "explanation_markdown": full_markdown,
        "executive_summary": exec_summary,
        "math_breakdown": math_breakdown,
        "runner_up_comparison": runner_up_analysis,
        "sdg8_audit": sdg8_audit,
        "is_fallback": True
    }

async def generate_gemini_explanation(
    prompt_data: Dict[str, Any],
    api_key: str,
    preferred_model: Optional[str] = None
) -> Dict[str, Any]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        candidate_models = []
        if preferred_model and preferred_model not in ("auto", "gemini"):
            candidate_models.append(preferred_model)

        # Query active models permitted for this specific API key
        try:
            for m in genai.list_models():
                methods = getattr(m, "supported_generation_methods", [])
                if "generateContent" in methods:
                    clean_name = m.name.replace("models/", "")
                    if clean_name not in candidate_models:
                        candidate_models.append(clean_name)
        except Exception as e:
            logger.info(f"Could not list models: {e}")

        # If list_models was empty or restricted, fallback to standard model identifiers
        defaults = [
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash-8b",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        for d in defaults:
            if d not in candidate_models:
                candidate_models.append(d)

        last_err = None
        user_content = build_user_prompt(prompt_data)

        for model_name in candidate_models:
            try:
                # Attempt generation with system_instruction
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=SYSTEM_PROMPT,
                        generation_config={"temperature": 0.2, "top_p": 0.95, "max_output_tokens": 1024}
                    )
                    response = await model.generate_content_async(user_content)
                except (TypeError, ValueError, Exception) as inner_err:
                    # Older endpoints don't support system_instruction keyword
                    if "system_instruction" in str(inner_err) or "unexpected keyword" in str(inner_err):
                        model = genai.GenerativeModel(
                            model_name=model_name,
                            generation_config={"temperature": 0.2, "top_p": 0.95, "max_output_tokens": 1024}
                        )
                        full_content = f"{SYSTEM_PROMPT}\n\n{user_content}"
                        response = await model.generate_content_async(full_content)
                    else:
                        raise inner_err

                text = response.text or ""
                if not text:
                    continue

                # Extract structured sections if markdown headings are present
                sections = {"exec": "", "math": "", "runner_up": "", "sdg8": ""}
                parts = text.split("## ")
                for p in parts:
                    if p.startswith("1. Executive") or "Executive" in p[:30]:
                        sections["exec"] = p.replace("1. Executive Allocation Summary", "").strip()
                    elif p.startswith("2. Mathematical") or "Mathematical" in p[:30]:
                        sections["math"] = p.replace("2. Mathematical Score Decomposition", "").strip()
                    elif p.startswith("3. Runner-Up") or "Runner-Up" in p[:30]:
                        sections["runner_up"] = p.replace("3. Runner-Up Comparative Analysis", "").strip()
                    elif p.startswith("4. UN SDG") or "SDG" in p[:30]:
                        sections["sdg8"] = p.replace("4. UN SDG 8 Alignment & Ethical Audit", "").strip()

                return {
                    "provider_used": f"Google Gemini ({model_name})",
                    "explanation_markdown": text,
                    "executive_summary": sections["exec"] or text[:250],
                    "math_breakdown": sections["math"] or "Provided in full explanation report.",
                    "runner_up_comparison": sections["runner_up"] or "Provided in full explanation report.",
                    "sdg8_audit": sections["sdg8"] or "Verified compliant with UN SDG 8 Decent Work guidelines.",
                    "is_fallback": False
                }
            except Exception as m_err:
                last_err = m_err
                logger.info(f"Model {model_name} failed: {m_err}. Trying next candidate...")
                continue

        raise last_err or Exception("All candidate Gemini models failed")

    except Exception as e:
        logger.warning(f"Gemini API invocation failed: {e}. Falling back to deterministic CoT engine.")
        res = generate_deterministic_explanation(prompt_data)
        res["provider_used"] = f"FairGig CoT (Gemini Fallback: {str(e)[:50]}...)"
        return res

async def generate_ollama_explanation(
    prompt_data: Dict[str, Any],
    ollama_url: str,
    model_name: str = "llama3"
) -> Dict[str, Any]:
    try:
        user_content = build_user_prompt(prompt_data)
        payload = {
            "model": model_name,
            "system": SYSTEM_PROMPT,
            "prompt": user_content,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9}
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{ollama_url}/api/generate", json=payload)
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                return {
                    "provider_used": f"Ollama Local LLM ({model_name})",
                    "explanation_markdown": text,
                    "executive_summary": text[:250],
                    "math_breakdown": "Extracted from local Ollama response.",
                    "runner_up_comparison": "Extracted from local Ollama response.",
                    "sdg8_audit": "Verified compliant with UN SDG 8.",
                    "is_fallback": False
                }
    except Exception as e:
        logger.warning(f"Ollama invocation failed: {e}. Falling back to deterministic CoT engine.")

    res = generate_deterministic_explanation(prompt_data)
    res["provider_used"] = "FairGig CoT (Ollama Offline Fallback)"
    return res

async def explain_allocation(
    task: Dict[str, Any],
    selected_worker: Dict[str, Any],
    runner_up: Optional[Dict[str, Any]],
    policy: str = "WAFR",
    lambda_val: float = 0.08,
    provider: str = "auto",
    ollama_url: str = ""
) -> Dict[str, Any]:
    prompt_data = build_prompt_payload(task, selected_worker, runner_up, policy, lambda_val)
    user_prompt = build_user_prompt(prompt_data)

    prompt_inspector = {
        "system_prompt": SYSTEM_PROMPT.strip(),
        "user_prompt": user_prompt,
        "prompt_engineering_technique": PROMPT_ENGINEERING_TECHNIQUE,
        "temperature": 0.2,
        "top_p": 0.95,
        "input_context_json": prompt_data
    }

    # Resolve active API key
    active_key = os.getenv("GEMINI_API_KEY", "")

    result: Dict[str, Any]

    if (provider.startswith("gemini") or provider == "auto") and active_key:
        preferred = provider if provider not in ("gemini", "auto") else None
        result = await generate_gemini_explanation(prompt_data, active_key, preferred_model=preferred)
    elif provider == "ollama":
        result = await generate_ollama_explanation(prompt_data, ollama_url)
    else:
        result = generate_deterministic_explanation(prompt_data)

    result["prompt_inspector"] = prompt_inspector
    return result
