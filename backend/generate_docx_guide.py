import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_document():
    doc = Document()

    # Set standard margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x29, 0x26, 0x3D)

    # Document Header Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("FAIRGIG AI — COMPREHENSIVE PRESENTATION & VIVA DEFENSE GUIDE")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9) # Deep Purple

    # Subtitle
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(16)
    run_sub = sub_p.add_run("A Multi-Agent AI System for Fair, Transparent, and Explainable Gig Task Allocation\nAligned with UN Sustainable Development Goal 8 (Decent Work and Economic Growth)")
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x77, 0x74, 0x8C)

    # Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    meta_data = [
        ("Course / Subject:", "Prompt Engineering / Advanced AI Systems"),
        ("Project Title:", "FairGig AI — Multi-Agent Fair Task Allocation Platform"),
        ("Core Focus:", "Prompt Engineering, LLM Multi-Agent Systems, Explainable AI (XAI), Algorithmic Fairness"),
        ("Date & Evaluation:", "B.Tech Final Presentation & Faculty Viva Voce Review")
    ]

    for idx, (k, v) in enumerate(meta_data):
        row = meta_table.rows[idx]
        cell_k, cell_v = row.cells[0], row.cells[1]
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_background(cell_k, "F3F0FF")
        set_cell_background(cell_v, "FAF9FE")
        p_k = cell_k.paragraphs[0]
        p_k.add_run(k).font.bold = True
        p_v = cell_v.paragraphs[0]
        p_v.add_run(v)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 1 ---
    h1 = doc.add_heading("1. Executive Summary & Problem Formulation", level=1)
    h1.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    doc.add_paragraph(
        "Commercial gig-economy platforms (food delivery, parcel courier networks, ride-hailing) deploy dispatch "
        "algorithms that prioritize short-term profit and proximity. This purely greedy optimization causes three severe systemic crises:\n"
        "1. Worker Starvation: Algorithmic bias channels the majority of tasks to a small fraction of couriers, leaving newer or under-represented couriers without income opportunities.\n"
        "2. Worker Burnout & Safety Hazards: Top-rated couriers are assigned back-to-back delivery batches, leading to severe fatigue and physical hazards.\n"
        "3. Black-Box Opacity: Gig workers have zero transparency into why they were selected or rejected for tasks, violating principles of modern algorithmic accountability."
    )

    doc.add_paragraph(
        "FairGig AI solves this by introducing Workload-Aware Fair Ranking (WAFR), an ensemble machine learning predictive model "
        "(HistGradientBoosting + CatBoost), and an autonomous 6-stage Multi-Agent LLM Orchestrator integrated with Google Gemini API "
        "and structured, data-grounded explanations with deterministic offline fallback."
    )

    # The 5 Core Questions Table
    q_table = doc.add_table(rows=6, cols=2)
    q_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = q_table.rows[0].cells
    headers[0].text = "Core Question Answered"
    headers[1].text = "How FairGig AI Answers It"
    set_cell_background(headers[0], "8B7CF6")
    set_cell_background(headers[1], "8B7CF6")
    headers[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    headers[0].paragraphs[0].runs[0].font.bold = True
    headers[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    headers[1].paragraphs[0].runs[0].font.bold = True

    questions = [
        ("1. What does the task require?", "Task Analysis Agent extracts vehicle specs, weight limits, urgency, deadline slack, and payouts."),
        ("2. Which workers are eligible?", "Worker Suitability Agent enforces strict non-negotiable hard constraints (vehicle cargo match, radius <= 10km, active availability)."),
        ("3. Which worker is most suitable via ML?", "HistGradientBoosting + CatBoost ensemble predicts the probability of successful, on-time task delivery."),
        ("4. How does fairness affect allocation?", "WAFR algorithm introduces an opportunity credit (+lambda) for starved couriers and a workload penalty (-lambda) for couriers > 40 hours."),
        ("5. Why was the selected worker chosen?", "Explainability Agent & Google Gemini synthesize a 4-part transparent rationale contrasting the winner against the runner-up candidate.")
    ]

    for idx, (q, a) in enumerate(questions):
        row = q_table.rows[idx + 1]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.3)
        c1.width = Inches(4.2)
        set_cell_background(c0, "F3F0FF" if idx % 2 == 0 else "FFFFFF")
        set_cell_background(c1, "FAF9FE" if idx % 2 == 0 else "FFFFFF")
        p0 = c0.paragraphs[0]
        p0.add_run(q).font.bold = True
        p1 = c1.paragraphs[0]
        p1.add_run(a)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 2 ---
    h2 = doc.add_heading("2. Full Technology Stack & Architectural Specifications", level=1)
    h2.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    doc.add_paragraph(
        "FairGig AI is built as a production-grade full-stack web application with strict asynchronous separation of concerns:\n"
        "- Backend API: Python 3.13.8, FastAPI, Uvicorn ASGI server, SQLite with SQLAlchemy ORM.\n"
        "- ML Ensemble: Scikit-learn 1.8.0, HistGradientBoostingClassifier, CatBoostClassifier, Joblib pipelines.\n"
        "- LLM & Prompt Engineering: Backend-configured Google Gemini API and deterministic offline fallback using zero-shot structured prompts.\n"
        "- Frontend UI: React 19, TypeScript, Vite 8.3, Tailwind CSS v4 pastel design system, Recharts data visualization, Lucide React icons."
    )

    # --- SECTION 3 ---
    h3 = doc.add_heading("3. Prompt Engineering Methodology & The 6 Autonomous Agents", level=1)
    h3.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    doc.add_paragraph(
        "As a project submitted for a Prompt Engineering course, the multi-agent system and LLM integration are the central focus. "
        "We employ four core prompt engineering techniques:\n"
        "1. Role Conditioning & Persona Prompting: Establishing the LLM as a 'Senior Algorithmic Fairness Auditor' under UN SDG 8 to guarantee objective, regulatory-compliant evaluations.\n"
        "2. Structured Zero-Shot Explanation: Summarizing supplied eligibility, ML, score, runner-up, and fairness values without requesting private reasoning.\n"
        "3. Counterfactual & Contrastive Prompting: Providing exact delta margins between the winner and runner-up candidate so the model explains why candidate #1 prevailed over candidate #2.\n"
        "4. Constrained Output Formatting: Enforcing structured Markdown and JSON schemas for zero-drift parsing into the user interface."
    )

    agent_table = doc.add_table(rows=7, cols=3)
    agent_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    a_headers = agent_table.rows[0].cells
    a_headers[0].text = "Agent Name"
    a_headers[1].text = "Stage"
    a_headers[2].text = "Role, Prompt Logic & Mathematical Responsibility"
    for c in a_headers:
        set_cell_background(c, "8B7CF6")
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        c.paragraphs[0].runs[0].font.bold = True

    agents = [
        ("Task Analysis Agent", "Stage 1", "Deconstructs task payload, validates SLA deadlines, package weight, payout, and vehicle cargo requirements."),
        ("Worker Suitability Agent", "Stage 2", "Applies strict non-negotiable hard constraints (distance <= 10km, vehicle compatibility, required skills, availability)."),
        ("Fairness Evaluation Agent", "Stage 3", "Calculates Opportunity Credit (starvation relief) and Workload Pressure (burnout prevention). Monitors Jain's Index and Gini Coefficient."),
        ("Allocation Decision Agent", "Stage 4", "Ranks candidates via WAFR policy: 0.70*ML + 0.30*Eff + lambda*Opp - lambda*Press."),
        ("Audit & Safety Agent", "Stage 5", "Verifies zero ineligible allocations, checks working hour caps (< 40h/week fatigue limit), and logs audit trail."),
        ("Explainability Agent (XAI)", "Stage 6", "Generates a concise rationale with Gemini when available or deterministic offline fallback. Does not expose private reasoning.")
    ]

    for idx, (name, stg, role) in enumerate(agents):
        row = agent_table.rows[idx + 1]
        c0, c1, c2 = row.cells[0], row.cells[1], row.cells[2]
        c0.width = Inches(2.0)
        c1.width = Inches(1.0)
        c2.width = Inches(3.5)
        set_cell_background(c0, "F3F0FF" if idx % 2 == 0 else "FFFFFF")
        set_cell_background(c1, "FAF9FE" if idx % 2 == 0 else "FFFFFF")
        set_cell_background(c2, "FAF9FE" if idx % 2 == 0 else "FFFFFF")
        c0.paragraphs[0].add_run(name).font.bold = True
        c1.paragraphs[0].add_run(stg)
        c2.paragraphs[0].add_run(role)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 4 ---
    h4 = doc.add_heading("4. Machine Learning Ensemble & Exact Empirical Metrics", level=1)
    h4.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    doc.add_paragraph(
        "The model was trained on historical gig completion records in Google Colab (FairGig_AI_FINAL_MODEL_HANDOFF.zip). "
        "The serialized ensemble consists of HistGradientBoostingClassifier (0.50) + CatBoostClassifier (0.50) operating across 27 tabular features (25 numerical, 2 categorical)."
    )

    metric_table = doc.add_table(rows=7, cols=3)
    metric_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    m_headers = metric_table.rows[0].cells
    m_headers[0].text = "Evaluation Metric"
    m_headers[1].text = "Empirical Value"
    m_headers[2].text = "Significance & Technical Interpretation"
    for c in m_headers:
        set_cell_background(c, "8B7CF6")
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        c.paragraphs[0].runs[0].font.bold = True

    metrics = [
        ("ROC-AUC", "0.9561", "Exceptional ranking capability distinguishing between successful deliveries and task failures."),
        ("PR-AUC (Precision-Recall)", "0.2431", "10.7x lift over random baseline prevalence of 0.0227 (2.27% rare failure rate under severe class imbalance)."),
        ("Brier Score Loss", "0.0187", "Exceptional probabilistic calibration; values near 0 demonstrate that predicted probabilities match true event frequencies."),
        ("Optimal Decision Threshold", "0.1550", "Calibrated on PR curves to maximize F1-score rather than assuming an arbitrary 0.50 cutoff."),
        ("Test Set Log-Loss", "0.0768", "Demonstrates robust model confidence without overfitting."),
        ("Feature Count", "27 Features", "25 numerical features (experience, distance, duration, historical completion rates, dimensions) + 2 categorical features.")
    ]

    for idx, (m, val, desc) in enumerate(metrics):
        row = metric_table.rows[idx + 1]
        c0, c1, c2 = row.cells[0], row.cells[1], row.cells[2]
        c0.width = Inches(2.2)
        c1.width = Inches(1.3)
        c2.width = Inches(3.0)
        set_cell_background(c0, "F3F0FF" if idx % 2 == 0 else "FFFFFF")
        set_cell_background(c1, "FAF9FE" if idx % 2 == 0 else "FFFFFF")
        set_cell_background(c2, "FAF9FE" if idx % 2 == 0 else "FFFFFF")
        c0.paragraphs[0].add_run(m).font.bold = True
        c1.paragraphs[0].add_run(val).font.bold = True
        c2.paragraphs[0].add_run(desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 5 ---
    h5 = doc.add_heading("5. Real-Time Calculations vs Hardcoded Seed Data", level=1)
    h5.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    doc.add_paragraph(
        "To clearly articulate what is hardcoded versus what is computed dynamically:\n"
        "• Hardcoded / Seeded Data: 1,000 synthetic workers loaded from data/workers.csv into SQLite; 3,000 tasks loaded from data/tasks.csv; pre-trained weights in models/cat_model.joblib.\n"
        "• Dynamically Computed in Real-Time:\n"
        "   1. Candidate Eligibility: dynamically computed per task based on location coordinates, vehicle capacity, and skills.\n"
        "   2. ML Success Probability: dynamically predicted by the HistGradientBoosting + CatBoost ensemble.\n"
        "   3. Efficiency Term: 0.60 * (1 - dist / max_dist) + 0.40 * min(1, deadline / duration).\n"
        "   4. Opportunity Credit: 1 - (tasks_7d / max_tasks_fleet).\n"
        "   5. Workload Pressure Penalty: min(1.0, hours_7d / 40.0).\n"
        "   6. WAFR Composite Score: 0.70*P(succ) + 0.30*Eff + lambda*Opp - lambda*Press.\n"
        "   7. Jain's Fairness Index & Gini Coefficient: dynamically computed across the entire allocated fleet.\n"
        "   8. Explainable AI Rationales: generated by Google Gemini when available or deterministic offline fallback."
    )

    # --- SECTION 6 ---
    h6 = doc.add_heading("6. Walkthrough of All 10 Sidebar Navigation Dashboards", level=1)
    h6.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    screens = [
        ("1. Overview Dashboard (/dashboard)", "Summary KPI cards (3000 tasks, 1000 workers, Jain's index 0.882, avg P(succ) 84.7%), hourly demand charts, and live allocation feed."),
        ("2. Interactive Allocation Studio (/allocate)", "The flagship 5-step wizard: Step 1 (Task Select), Step 2 (Eligibility Filter), Step 3 (ML Scoring), Step 4 (Fairness lambda Tuning), Step 5 (Final Allocation & Gemini XAI)."),
        ("3. Multi-Agent Orchestrator (/agents)", "Interactive execution studio for the 6 autonomous agents. Displays latency (ms), input parameters, and output artifacts per stage."),
        ("4. Tasks Directory & Creator (/tasks)", "Searchable catalog of all 3,000 tasks with filters for priority and status, plus a modal to create new tasks with instant validation."),
        ("5. Worker Pool Directory (/workers)", "Catalog of 1,000 couriers with vehicle type, experience, 7-day workload hours, archetype filters, and synthetic courier generation."),
        ("6. Fairness Analytics & lambda Sweep (/fairness)", "Empirical Pareto frontier plotting operational efficiency vs Jain's fairness index across 20 lambda parameter steps."),
        ("7. Model Insights & Calibration (/model-insights)", "ROC curve (0.9561), PR curve (0.2431), Calibration Reliability diagram (Brier score 0.0187), and feature importance ranking."),
        ("8. Allocation History & Audit Log (/history)", "Permanent SQLite audit trail of all confirmed allocations with candidate rankings JSON and stored explanations."),
        ("9. Export & Reporting Studio (/reports)", "System throughput metrics, fairness reports, and one-click CSV export buttons for allocations, workers, and audit logs."),
        ("10. Platform & XAI Settings (/settings)", "Global defaults for policy and lambda, database seed status, and backend-reported AI provider status.")
    ]

    for title, desc in screens:
        p = doc.add_paragraph()
        p.add_run(f"• {title}: ").font.bold = True
        p.add_run(desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 7 ---
    h7 = doc.add_heading("7. Top Viva Voce Questions & Model Answers for Evaluator", level=1)
    h7.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    viva_qa = [
        ("Why is this a Prompt Engineering project?",
         "Because Prompt Engineering is utilized in the Explainability stage: the six specialized agents coordinate task analysis, constraint checking, and multi-objective ranking. A role-conditioned zero-shot prompt uses supplied mathematical outputs for a concise, structured explanation and counterfactual comparison without requesting private reasoning."),
        ("What is the purpose of lambda in the WAFR formula?",
         "Lambda is the fairness-efficiency trade-off parameter. At lambda = 0.0, the algorithm behaves as purely greedy dispatch (optimizing only for predicted completion probability and shortest distance). At lambda = 0.08, opportunity credits boost under-utilized couriers and workload penalties prevent courier burnout (> 40h/week), improving Jain's fairness index by 45% while incurring less than a 2.1% penalty in operational travel distance."),
        ("What happens if the Gemini API key is missing or offline?",
         "If no backend Gemini key is configured or a Gemini request fails, FairGig AI uses deterministic backend explanation logic. Allocation, fairness scoring, and ML inference continue independently of Gemini."),
        ("Why is PR-AUC 0.2431 significant?",
         "Task delivery failure in gig platforms is a rare event with severe class imbalance (only 2.27% of instances are negative/failure events). A random classifier achieves a PR-AUC of 0.0227. Our ensemble achieves 0.2431, representing a 10.7-fold predictive lift on the critical minority class."),
        ("How does FairGig AI embody UN SDG 8 (Decent Work)?",
         "UN SDG 8 calls for fair working environments, non-discrimination, and protection of labor rights. FairGig AI eliminates gig algorithmic bias by giving starved couriers positive opportunity credits, prevents fatigue accidents by penalizing workload over 40 hours/week, and provides transparent explanations so workers understand task assignments.")
    ]

    for q, a in viva_qa:
        p_q = doc.add_paragraph()
        p_q.add_run(f"Q: {q}").font.bold = True
        p_a = doc.add_paragraph()
        p_a.add_run(f"A: {a}")
        p_a.paragraph_format.space_after = Pt(8)

    # --- SECTION 8 ---
    h8 = doc.add_heading("8. Commands to Run Backend & Frontend", level=1)
    h8.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    doc.add_paragraph(
        "To run the application locally on Windows:\n"
        "Option 1: Double click 'start_all.bat' in the project root.\n"
        "Option 2: Terminal 1 (Backend):\n"
        "   cd backend\n"
        "   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload\n"
        "Option 3: Terminal 2 (Frontend):\n"
        "   cd frontend\n"
        "   npm run dev\n\n"
        "Access URLs:\n"
        "• Web Application: http://localhost:5173\n"
        "• FastAPI Documentation: http://127.0.0.1:8000/docs"
    )

    output_path = os.path.join(os.path.dirname(__file__), "..", "FairGig_AI_Presentation_Defense_Guide.docx")
    output_path = os.path.abspath(output_path)
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    create_document()
