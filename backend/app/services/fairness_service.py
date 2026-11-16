import numpy as np
from typing import List, Dict, Any, Sequence, Tuple

def compute_efficiency(distance_km: np.ndarray, deadline_pressure: np.ndarray) -> np.ndarray:
    """
    Computes operational efficiency:
    eff = 0.65 / (1 + distance_km) + 0.35 / (1 + deadline_pressure)
    min-max normalized.
    """
    raw_eff = 0.65 / (1.0 + np.maximum(0.0, distance_km)) + 0.35 / (1.0 + np.maximum(0.0, deadline_pressure))
    if len(raw_eff) <= 1:
        return np.array([0.5])

    eff_min = np.min(raw_eff)
    eff_max = np.max(raw_eff)
    if eff_max - eff_min < 1e-9:
        return np.full_like(raw_eff, 0.5)

    return (raw_eff - eff_min) / (eff_max - eff_min + 1e-9)

def compute_opportunity_credit(recent_exposure: np.ndarray) -> np.ndarray:
    """
    Computes opportunity credit = 1 - percentile_rank(recent_exposure)
    Workers with lower recent exposure receive higher opportunity credit.
    """
    values = np.asarray(recent_exposure)
    if values.size == 0:
        return np.array([], dtype=float)

    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and values[order[end]] == values[order[start]]:
            end += 1
        average_rank = ((start + 1) + end) / 2.0
        ranks[order[start:end]] = average_rank / values.size
        start = end
    return 1.0 - ranks

def compute_workload_pressure(work_hours_7d: np.ndarray, median_work_hours: float = 20.0) -> np.ndarray:
    """
    Computes workload pressure:
    pressure = (work_hours_7d / (median_work_hours + 1e-6)).clip(0, 2) / 2.0
    """
    ratio = work_hours_7d / (median_work_hours + 1e-6)
    return np.clip(ratio, 0.0, 2.0) / 2.0

def compute_wafr_score(
    predicted_success: float,
    efficiency: float,
    opportunity_credit: float,
    workload_pressure: float,
    lambda_val: float = 0.08
) -> float:
    """
    WAFR formula:
    0.70 * predicted_success + 0.30 * efficiency + lambda * opportunity_credit - lambda * workload_pressure
    """
    score = (
        0.70 * predicted_success +
        0.30 * efficiency +
        lambda_val * opportunity_credit -
        lambda_val * workload_pressure
    )
    return float(score)

def calculate_jain_index(allocations: Sequence[float]) -> float:
    """
    Jain's Fairness Index across worker exposure counts:
    J = (sum(x_i))^2 / (n * sum(x_i^2))
    """
    x = np.asarray(allocations, dtype=float)
    if x.size == 0:
        return 0.0
    n = len(x)
    sum_x = np.sum(x)
    sum_x_sq = np.sum(x**2)
    if sum_x_sq == 0:
        return 1.0
    return float((sum_x**2) / (n * sum_x_sq + 1e-9))

def calculate_gini_index(allocations: Sequence[float]) -> float:
    """
    Gini Index of worker exposure:
    G = sum(|x_i - x_j|) / (2 * n^2 * mean(x))
    """
    x = np.asarray(allocations, dtype=float)
    if x.size == 0:
        return 0.0
    n = len(x)
    mean_x = np.mean(x)
    if mean_x == 0:
        return 0.0
    diff_sum = np.sum(np.abs(x[:, None] - x[None, :]))
    return float(diff_sum / (2.0 * (n**2) * mean_x + 1e-9))
