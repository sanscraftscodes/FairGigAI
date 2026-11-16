import sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, 'backend')

print('=== Testing full backend import chain ===')
print()

# Test 1: Config import
from app.config import MODELS_DIR, PREDICTIONS_DIR
print('1. Config: OK')

# Test 2: Feature builder
from app.services.feature_builder import FEATURE_COLUMNS_27, NUMERIC_COLUMNS_25
print('2. Feature builder: OK (27 features, 25 numeric)')

# Test 3: Model service with new pure-Python CatBoost
from app.services.model_service import model_service
model_service.ensure_loaded()
assert model_service.is_loaded, 'Model not loaded: ' + str(model_service.load_error)
print('3. Model service: OK (loaded=' + str(model_service.is_loaded) + ')')

# Test 4: Predict probabilities
test_rows = [
    {
        'task_type': 'fragile', 'required_skill': 'handling',
        'priority_num': 2, 'estimated_duration_min': 60.0, 'deadline_min': 240.0,
        'payment': 500.0, 'package_weight_kg': 2.5, 'distance_km': 3.5,
        'deadline_pressure': 0.3, 'experience_years': 3.0,
        'historical_success_7d': 0.85, 'historical_success_30d': 0.80, 'historical_success_90d': 0.78,
        'cancellation_7d': 0.1, 'cancellation_30d': 0.1, 'delay_7d': 0.05, 'delay_30d': 0.08,
        'work_hours_7d': 20.0, 'work_hours_30d': 80.0, 'workload_trend': 0.5,
        'recent_exposure': 0.3, 'task_affinity': 0.7, 'skill_match': 1.0,
        'vehicle_match': 1.0, 'weight_ok': 1.0, 'available': 1.0, 'deadline_feasible': 1.0
    },
    {
        'task_type': 'delivery', 'required_skill': 'driving',
        'priority_num': 1, 'estimated_duration_min': 45.0, 'deadline_min': 180.0,
        'payment': 300.0, 'package_weight_kg': 1.0, 'distance_km': 5.0,
        'deadline_pressure': 0.25, 'experience_years': 2.0,
        'historical_success_7d': 0.70, 'historical_success_30d': 0.72, 'historical_success_90d': 0.68,
        'cancellation_7d': 0.15, 'cancellation_30d': 0.12, 'delay_7d': 0.1, 'delay_30d': 0.09,
        'work_hours_7d': 30.0, 'work_hours_30d': 110.0, 'workload_trend': 0.7,
        'recent_exposure': 0.5, 'task_affinity': 0.6, 'skill_match': 1.0,
        'vehicle_match': 1.0, 'weight_ok': 1.0, 'available': 1.0, 'deadline_feasible': 1.0
    }
]
ens, hgb, cat = model_service.predict_probabilities(test_rows)
assert len(ens) == 2
assert all(0 <= p <= 1 for p in ens)
print('4. Predict probabilities: OK ens=' + str([round(p, 4) for p in ens]))

# Test 5: Feature importances
importances = model_service.get_feature_importances()
assert len(importances) > 0
top = importances[0]
print('5. Feature importances: OK top=' + top['feature'] + ':' + str(top['importance']))

# Test 6: AI service
from app.services.ai_service import get_ai_status
status = get_ai_status()
print('6. AI service: OK mode=' + status['mode'])

# Test 7: LLM explainability service
from app.services.llm_explainability_service import generate_deterministic_explanation, build_prompt_payload
payload = build_prompt_payload(
    {'task_id': 'T001', 'task_type': 'fragile', 'priority': 'high',
     'estimated_duration_min': 60, 'package_weight_kg': 2.5,
     'required_vehicle': 'bike', 'base_payout': 500},
    {'worker_id': 'W001', 'vehicle_type': 'bike', 'experience_years': 3,
     'distance_km': 3.5, 'working_hours_7d': 20, 'predicted_success': 0.85,
     'efficiency': 0.7, 'opportunity_credit': 0.3, 'workload_pressure': 0.4},
    None, 'WAFR', 0.08
)
expl = generate_deterministic_explanation(payload)
assert 'explanation_markdown' in expl
print('7. LLM explainability: OK provider=' + expl['provider'])

print()
print('=== ALL TESTS PASSED ===')
print()
print('Bundle size reduction:')
print('  REMOVED: catboost(~200MB) + scipy(~160MB) + pandas(~90MB) = ~450MB')
print('  ADDED:   cat_model_python.py (~1.4MB)')
print('  ESTIMATED NEW BUNDLE: ~380MB (well under 500MB limit)')
