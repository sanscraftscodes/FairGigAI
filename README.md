# FairGig AI — Multi-Agent AI System for Fair and Explainable Gig Task Allocation

**Aligned with United Nations Sustainable Development Goal 8: Decent Work and Economic Growth**

FairGig AI is a full-stack, research-backed multi-agent task allocation system designed to balance task feasibility, worker suitability, trained machine-learning success likelihood, operational efficiency, and algorithmic fairness.

---

## 🌟 Key Highlights

- **Multi-Agent Orchestration Pipeline:**
  1. **Task Analysis Agent:** Validates completeness, identifies spatial/temporal constraints, and scores data quality.
  2. **Worker Profile & Suitability Agent:** Enforces hard eligibility constraints (vehicle, skills, package capacity, availability, travel deadline) and logs exact rejection reasons.
  3. **ML Success Prediction Service:** Uses validation-selected dual ensemble (`HistGradientBoosting` 50% + `CatBoost` 50%) across 27 features to predict task completion probability.
  4. **Fairness Evaluation Agent:** Computes worker recent exposure, opportunity credit, and 7-day workload pressure.
  5. **Allocation Agent:** Executes Workload-Aware Fair Ranking (WAFR) multi-objective optimization:
     $$\text{WAFR} = 0.70 \cdot P(\text{success}) + 0.30 \cdot \text{Efficiency} + \lambda \cdot \text{Opportunity\_Credit} - \lambda \cdot \text{Workload\_Pressure}$$
  6. **Explainability Agent:** Synthesizes human-readable justifications, score decompositions, and counterfactual comparisons against runner-up candidates.

- **Visual Design System:** Modern SaaS dashboard using a soft pastel color palette (`#8B7CF6`, `#F3F0FF`, `#F8DDE8`, `#D9F3E4`, `#DCEBFA`, `#FFE7D2`), clean typography, Lucide icons, responsive tables, and interactive Recharts visualizations.

- **Dual-Model Inference Parity:** Verified numerical match ($0.00005$) against held-out Colab experiment records without retraining or fabricating predictions.

---

## 📁 Repository Structure

```text
FairGig-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application and lifespan seed
│   │   ├── config.py                # System paths and hyperparameter defaults
│   │   ├── db/
│   │   │   ├── database.py          # SQLAlchemy SQLite/Postgres connection
│   │   │   ├── models.py            # Task, Worker, Allocation, and AgentLog models
│   │   │   └── seed.py              # Ingests CSVs and seeds demonstration allocations
│   │   ├── schemas/                 # Pydantic schemas for requests/responses
│   │   ├── services/
│   │   │   ├── eligibility.py       # Hard feasibility constraint rules & reasons
│   │   │   ├── feature_builder.py   # 27-feature engineering pipeline
│   │   │   ├── model_service.py     # HGB + CatBoost ensemble loader & predictor
│   │   │   ├── fairness_service.py  # WAFR, Jain fairness, and Gini calculations
│   │   │   └── allocation_service.py# Candidate evaluation, ranking & policy comparison
│   │   ├── agents/                  # 5 distinct agent implementations
│   │   │   ├── task_analysis.py
│   │   │   ├── worker_suitability.py
│   │   │   ├── fairness_evaluation.py
│   │   │   ├── allocation_agent.py
│   │   │   └── explainability.py
│   │   └── api/                     # REST endpoints (tasks, workers, allocation, etc.)
│   └── tests/
├── requirements.txt                 # Pinned Python runtime dependencies
├── pyproject.toml                    # Vercel Python entrypoint/runtime
├── vercel.json                       # Single-project Vercel build configuration
├── .env.example                      # Server-only environment variable template
├── DEPLOYMENT.md                     # GitHub, Supabase, and Vercel setup
├── frontend/
│   ├── src/
│   │   ├── api/client.ts            # Type-safe API client
│   │   ├── components/              # Sidebar, Header, KPICard, HelpModal
│   │   ├── pages/                   # 10 full functional routes
│   │   │   ├── DashboardPage.tsx    # KPIs, charts, policy comparisons, activity
│   │   │   ├── TasksPage.tsx        # Catalog, filters, drawer, create task modal
│   │   │   ├── AllocatePage.tsx     # 5-step guided allocation stepper
│   │   │   ├── AgentsPage.tsx       # Multi-agent visual workflow execution
│   │   │   ├── WorkersPage.tsx      # Directory, profiles, synthetic demo worker
│   │   │   ├── FairnessPage.tsx     # Exposure, workload, and lambda sweep curve
│   │   │   ├── ModelInsightsPage.tsx# Model weights, calibration curve, feature importances
│   │   │   ├── HistoryPage.tsx      # Audit trail, candidate rankings, CSV export
│   │   │   ├── ReportsPage.tsx      # CSV downloads
│   │   │   └── SettingsPage.tsx     # Parameter configuration
│   │   ├── App.tsx                  # Main router shell
│   │   └── index.css                # Pastel design system styles
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── tasks.csv                    # 3,000 tasks
│   └── workers.csv                  # 1,000 workers
├── models/
│   ├── all_trained_models.joblib    # Bundle with HistGradientBoosting
│   ├── cat_model.joblib             # Standalone CatBoost classifier
│   └── ensemble_configuration.json  # Weights [0.5, 0.0, 0.0, 0.5], threshold 0.155
├── documentation/
│   ├── PROJECT_MANIFEST.json
│   ├── feature_configuration.json
│   └── FINAL_NOTEBOOK_EXECUTION_HISTORY.py
└── predictions/
    ├── ensemble_test.csv            # 60,000 test predictions
    └── y_test.csv                   # Ground-truth outcomes
```

---

## 🚀 Setup & Launch Instructions (Windows)

### Prerequisites
- **Python 3.10+** (tested with Python 3.13)
- **Node.js 18+** & **npm** (tested with Node v22.20.0)

---

### Step 1: Backend Setup & Launch

Open a PowerShell terminal at the project root:

```powershell
# Install Python requirements
python -m pip install -r requirements.txt

# Navigate into backend directory
cd backend

# Seed the local SQLite database from data/workers.csv & data/tasks.csv
python -m app.db.seed

# Start the FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend server will start at `http://127.0.0.1:8000`.
- Health check: `http://127.0.0.1:8000/api/health`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

---

### Step 2: Frontend Setup & Launch

Open a second PowerShell terminal at the project root:

```powershell
# Navigate into frontend directory
cd frontend

# Install npm dependencies (first time only)
npm install

# Start Vite development server
npm run dev
```

The application interface will be live at:
👉 **`http://localhost:5173`**

---

## 📊 Key Evaluation Reference Metrics

From the held-out research experiment:
- **ROC-AUC:** $\approx 0.9561$ (discrimination over all candidate pairs)
- **PR-AUC:** $\approx 0.2431$ (against random baseline of $\approx 0.0227$, given $2.27\%$ positive prevalence)
- **Brier Score:** $\approx 0.0187$
- **Counterfactual +3h Workload Switch Rate:** $\approx 0.044$
- **Ensemble Weights:** 50% `HistGradientBoosting` + 50% `CatBoost`
- **Optimal Decision Threshold:** $0.155$

---

## ☁️ Production Deployment

The complete React application and FastAPI API are served from one Vercel
project and one domain. Vercel's Python function uses Supabase Postgres for
persistent application data. See [DEPLOYMENT.md](./DEPLOYMENT.md) for setup,
environment variables, limits, and verification steps.
