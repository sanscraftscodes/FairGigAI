import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_demo_presentation_doc():
    doc = Document()

    # Margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.9)
        sec.bottom_margin = Inches(0.9)
        sec.left_margin = Inches(0.9)
        sec.right_margin = Inches(0.9)

    # Styles
    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(0x29, 0x26, 0x3D)

    # Helper: Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_t = p_title.add_run("FAIRGIG AI — COMPLETE DEMO FLOW & PRESENTATION SCRIPT")
    r_t.font.size = Pt(22)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9) # Deep Lavender/Violet

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(14)
    r_s = p_sub.add_run("Step-by-Step Presentation Script, Concept Explanations, Mathematical Breakdowns & Viva Defense\nCourse: Prompt Engineering & Advanced AI Systems | UN SDG 8 Aligned")
    r_s.font.size = Pt(12)
    r_s.font.italic = True
    r_s.font.color.rgb = RGBColor(0x77, 0x74, 0x8C)

    # Callout Box: How to use this document
    box_tbl = doc.add_table(rows=1, cols=1)
    box_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = box_tbl.rows[0].cells[0]
    c.width = Inches(6.7)
    set_cell_background(c, "F3F0FF")
    p_box = c.paragraphs[0]
    p_box.paragraph_format.space_before = Pt(4)
    p_box.paragraph_format.space_after = Pt(4)
    r_box_h = p_box.add_run("HOW TO USE THIS SCRIPT TOMORROW:\n")
    r_box_h.font.bold = True
    r_box_h.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)
    r_box_b = p_box.add_run(
        "This guide is arranged in the exact order you should click and speak on screen. "
        "Whenever you see [WHAT TO SAY TO MA'AM], you can speak those exact words. "
        "All difficult concepts (Zero-Shot Prompting, Offline Fallback, Lambda, Jain's Fairness, Gini, Threshold 0.155) "
        "are broken down in simple, conversational English so you never get stuck."
    )
    r_box_b.font.size = Pt(10.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # =========================================================================
    # PART 1: 2-MINUTE OPENING ELEVATOR PITCH
    # =========================================================================
    h1 = doc.add_heading("PART 1: 2-Minute Opening Pitch (Start with This!)", level=1)
    h1.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    doc.add_paragraph(
        "[WHAT TO SAY TO MA'AM]:\n"
        "\"Good morning / afternoon Ma'am. Today I am presenting FairGig AI — A Multi-Agent AI System for Fair and "
        "Explainable Gig Task Allocation, aligned with UN Sustainable Development Goal 8: Decent Work and Economic Growth.\n\n"
        "The problem we are solving is in modern gig platforms like Swiggy, Zomato, Uber, and Dunzo. Today, these platforms "
        "use purely greedy algorithms that only look at who is closest or who has the highest rating. "
        "This causes two major issues:\n"
        "1. Worker Starvation: New couriers get zero orders because the algorithm always prefers old star couriers.\n"
        "2. Worker Burnout: Those same star couriers are overworked with 50+ hours a week, causing fatigue and road accidents.\n"
        "3. Black-Box Opacity: Workers never know why a task was given to someone else.\n\n"
        "Our system, FairGig AI, solves this using 3 pillars:\n"
        "• A Machine Learning Ensemble (HistGradientBoosting + CatBoost) with 0.9561 ROC-AUC that predicts delivery success.\n"
        "• A Workload-Aware Fair Ranking (WAFR) formula with a tunable fairness knob called Lambda (λ).\n"
        "• A 6-Agent Architecture with backend-managed Gemini explanations and a deterministic offline fallback.\""
    )

    # =========================================================================
    # PART 2: KEY THEORETICAL CONCEPTS IN SIMPLE WORDS
    # =========================================================================
    h2 = doc.add_heading("PART 2: Key Concepts in Simple Words (Memorize These!)", level=1)
    h2.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    concepts = [
        ("1. How are explanations generated?",
         "The backend sends the allocation's actual task, worker, model-score, and fairness values to Gemini and asks for a concise, structured explanation. "
         "Prompts prohibit unsupported facts and private chain-of-thought. A deterministic backend fallback is used if Gemini is unavailable."),

        ("2. What is Zero-Shot Prompting / Learning?",
         "Zero-shot prompting means giving the model a task with clear role conditioning and instructions without needing to "
         "re-train or fine-tune the LLM weights on gig dataset samples. The prompt itself contains the rules, system persona, "
         "and data schema, and the LLM generalizes zero-shot to any new delivery task immediately."),

        ("3. What is the Fallback Option and why do we have it?",
         "In real-world SaaS and during university vivas, external cloud APIs can fail: internet drops, API quota runs out, "
         "or Google deprecates a model name (like gemini-1.5-flash). "
         "FairGig AI implements an automatic fallback: if Gemini is not configured or a request fails, "
         "the backend generates a deterministic explanation from the supplied allocation values. "
         "Allocation, fairness evaluation, and ML inference do not depend on Gemini."),

        ("4. What is the WAFR Module (Workload-Aware Fair Ranking)?",
         "WAFR is our core mathematical contribution. The formula is:\n"
         "   WAFR Score = 0.70 × P(success) + 0.30 × Efficiency + λ × Opportunity Credit - λ × Workload Pressure\n"
         "• 0.70 × P(success): 70% weight on our ML model's predicted probability that the task will be delivered successfully.\n"
         "• 0.30 × Efficiency: 30% weight on travel distance and deadline slack (closer couriers get higher efficiency).\n"
         "• + λ × Opportunity Credit: Extra bonus given to workers who have received very few tasks recently (starvation relief).\n"
         "• - λ × Workload Pressure: Penalty subtracted from workers who have worked close to or over 40 hours this week (burnout prevention)."),

        ("5. Why are we using Lambda (λ) and what does it signify?",
         "In simple words, Lambda (λ) is the 'Fairness Knob' or 'Equity Dial'.\n"
         "• If Lambda = 0.00: The system is in purely greedy mode. It completely ignores worker fatigue and gives 0 fairness bonus. "
         "It only cares about ML probability and shortest distance.\n"
         "• If Lambda = 0.08 (Our Recommended Baseline): It gives an 8% opportunity boost to starved couriers and an 8% penalty "
         "to overworked couriers. Our research shows this improves fairness by 45% while travel distance increases by less than 2%!\n"
         "• If Lambda = 0.40 (High Equity Mode): Fairness has high priority (40% weight). The platform aggressively distributes tasks "
         "to idle workers, even if they are slightly farther away."),

        ("6. Comparing the 3 Allocation Policies:",
         "Our platform allows comparing 3 policies:\n"
         "1. WAFR (Our Model): Balances ML success, operational speed, anti-starvation credits, and anti-burnout penalties.\n"
         "2. Nearest Eligible: Blindly assigns the closest courier. Fails when the nearest person has a bicycle but the package is 20 kg, "
         "or when the courier is already exhausted after 45 hours of work.\n"
         "3. ML-Only: Blindly picks the courier with highest predicted success rate. Leads to monopolies where top 5% of couriers take 80% of tasks."),

        ("7. What is Jain's Fairness Index (often misheard as 'jail')?",
         "It is named after Professor Raj Jain (invented in 1984 for computer networking). Formula:\n"
         "   J(x) = (Σ x_i)^2 / [ n × Σ (x_i)^2 ]\n"
         "It measures how equally resources (tasks) are shared among n workers.\n"
         "• Score = 1.0 means PERFECT EQUALITY (every courier gets the exact same number of tasks).\n"
         "• Score = 1/n means WORST MONOPOLY (one courier gets all tasks, everyone else gets 0).\n"
         "• In FairGig AI, WAFR achieves Jain's Index of 0.882, whereas greedy dispatch is only 0.410!"),

        ("8. What is Gini Exposure / Gini Coefficient?",
         "Gini Coefficient is the standard economic metric for inequality (from 0 to 1).\n"
         "• 0.0 means perfect equality in task distribution.\n"
         "• 1.0 means extreme inequality.\n"
         "FairGig AI reduces the Gini coefficient from 0.64 (greedy monopoly) down to 0.22 (fair distribution).")
    ]

    for title, desc in concepts:
        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_before = Pt(6)
        p_c.paragraph_format.space_after = Pt(4)
        r_ct = p_c.add_run(title)
        r_ct.font.bold = True
        r_ct.font.color.rgb = RGBColor(0x29, 0x26, 0x3D)

        p_cd = doc.add_paragraph()
        p_cd.paragraph_format.space_after = Pt(6)
        p_cd.add_run(desc)

    # =========================================================================
    # PART 3: SCREEN-BY-SCREEN LIVE DEMO FLOW
    # =========================================================================
    h3 = doc.add_heading("PART 3: Live Demo Flow (Follow this Screen by Screen!)", level=1)
    h3.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    screens = [
        ("SCREEN 1: Dashboard (/dashboard)",
         "What to show Ma'am:\n"
         "• 4 Top KPI Cards:\n"
         "   - Total Catalog Tasks: 3,000 tasks loaded in SQLite.\n"
         "   - Active Couriers: 1,000 registered workers across bikes, scooters, cars, and vans.\n"
         "   - Jain's Fairness Index: 0.882 (proves equitable distribution).\n"
         "   - Average Predicted Success: 84.7%.\n"
         "• Hourly Task Demand Chart: Shows incoming delivery volume across 24 hours.\n"
         "• Live Allocation Stream: Feed showing recently allocated tasks and courier IDs.\n\n"
         "[WHAT TO SAY TO MA'AM]:\n"
         "\"Here is our central operations dashboard. It gives platform administrators an instant bird's-eye view "
         "of fleet readiness, active couriers, and our platform-wide fairness score of 0.882.\""),

        ("SCREEN 2: The Core Demo — Task Allocation Wizard (/allocate)",
         "This is the heart of your demo! Walk through each of the 5 steps:\n\n"
         "• STEP 1: Select Task\n"
         "   - Pick task T00000 or any task from the dropdown.\n"
         "   - Show Ma'am the Task Profile card: package weight (e.g. 5 kg), required vehicle (car/bike), payout (₹25), and deadline.\n"
         "   - Click 'Continue to Worker Evaluation'.\n\n"
         "• STEP 2: Candidate Eligibility & Ineligible Workers\n"
         "   - Show the 3 summary cards: Total Examined (100 candidates), Eligible (e.g. 18 workers), Ineligible (e.g. 82 workers).\n"
         "   - [WHY ARE SOME WORKERS INELIGIBLE? Explain to Ma'am]:\n"
         "     1. Distance Constraint: Courier is farther than 10 km from pickup point.\n"
         "     2. Vehicle Mismatch: Task needs a car or van because it's 15 kg fragile cargo, but courier has a bicycle.\n"
         "     3. Missing Skill: Task requires 'fragile' or 'medical handling' certification.\n"
         "     4. Availability: Courier status is 'busy' or 'offline'.\n"
         "   - Point out: 'FairGig AI guarantees that zero ineligible workers are ever assigned.' Click 'Run ML Predictions'.\n\n"
         "• STEP 3: ML Predictions & Likelihood Scoring\n"
         "   - Show the Bar Chart comparing predicted success probabilities across eligible couriers.\n"
         "   - [WHY IS SUCCESS RATE HIGH OR LOW? Explain to Ma'am]:\n"
         "     * High Success Rate (85% - 95%): Short travel distance, generous deadline slack (60 mins for 2 km), courier has 4+ years experience and 98% historical completion.\n"
         "     * Low Success Rate (50% - 65%): Tight deadline (15 mins for 8 km), heavy package in peak traffic, newer courier.\n"
         "     * The Colab Threshold (0.155): Explain that in gig work, failed deliveries are rare (only 2.27% baseline failure rate). "
         "A naive 0.50 cutoff would miss risky orders. 0.155 is the optimal calibrated threshold maximizing F1-score!\n"
         "   - Click 'Evaluate Fairness'.\n\n"
         "• STEP 4: Fairness Evaluation & Lambda (λ) Tuning\n"
         "   - Point to the Lambda Slider (λ = 0.08 by default).\n"
         "   - Move the slider to 0.00 and explain: 'At 0.00, opportunity credit and workload penalty are 0%.'\n"
         "   - Move it to 0.08: 'Here, we give an 8% boost for starved workers and 8% penalty for tired workers.'\n"
         "   - Click 'Calculate Final Allocation (Step 5)'. (Or click bubble 5 in the top bar!)\n\n"
         "• STEP 5: Final Allocation & Explainable AI (XAI) (THE BIG MOMENT!)\n"
         "   - Show the Winner Banner: Displays Selected Worker (e.g. W0424), Predicted Success (e.g. 58.0% or 89%), and WAFR Score.\n"
         "   - Show the 4 Math Breakdown Terms:\n"
         "     + ML Success Term: 0.70 × P(succ)\n"
         "     + Efficiency Term: 0.30 × Efficiency\n"
         "     + Opportunity Credit: + λ × Credit\n"
         "     - Workload Penalty: - λ × Pressure\n"
         "   - Now show the EXPLAINABLE AI (XAI) Panel directly below:\n"
         "     1. Click 'Rationale' tab: Read the executive summary aloud.\n"
         "     2. Click 'Math Breakdown' tab: Shows the exact calculated score.\n"
         "     3. Click 'Runner-Up Delta' tab: Shows why Worker #1 beat Worker #2 (e.g. '+0.04 score advantage, Worker #2 already worked 38 hours').\n"
         "     4. Click 'SDG 8 Audit' tab: Shows compliance with UN Decent Work.\n"
         "   - Click the 'Prompt Engineering Trace & Hyperparameters' button at the bottom:\n"
         "     * A black terminal drawer expands!\n"
         "     * Show Ma'am the exact SYSTEM PROMPT, the INJECTED USER PROMPT, and TEMPERATURE = 0.2.\n"
         "     * Explain: 'This demonstrates our prompt engineering curriculum: role prompting, few-shot reasoning constraints, and temperature 0.2 to prevent hallucination.'\n"
         "   - Click 'Confirm Assignment': Saves the record to SQLite and assigns the courier!"),

        ("SCREEN 3: Multi-Agent Orchestrator (/agents)",
         "What to show Ma'am:\n"
         "• Click 'Run Multi-Agent Allocation Workflow'.\n"
         "• Watch all 6 agents execute in sequence with live execution duration (ms):\n"
         "   1. Task Analysis Agent (Stage 1): Parses task requirements.\n"
         "   2. Worker Suitability Agent (Stage 2): Filters hard constraints.\n"
         "   3. Fairness Evaluation Agent (Stage 3): Computes opportunity & workload metrics.\n"
         "   4. Allocation Decision Agent (Stage 4): Evaluates WAFR composite ranking.\n"
         "   5. Audit & Safety Agent (Stage 5): Validates zero-violation safety checks.\n"
         "   6. Explainability Agent (Stage 6): Generates a Gemini explanation or deterministic offline fallback."),

        ("SCREEN 4: Fairness Analytics (/fairness)",
         "What to show Ma'am:\n"
         "• The Pareto Frontier Graph: Plots Allocation Efficiency on Y-axis vs Jain's Fairness Index on X-axis.\n"
         "• Point out the 'Sweet Spot' at λ = 0.08: 'Here, Jain's Index jumps from 0.41 to 0.88, while efficiency only drops from 95% to 93%.'\n"
         "• Click 'Run Live λ Sweep': Evaluates 20 distinct parameter points in real-time.\n"
         "• Show the Gini Coefficient: Reduced from 0.64 down to 0.22."),

        ("SCREEN 5: Model Insights & Machine Learning Metrics (/model-insights)",
         "What to show Ma'am (The exact values from your Google Colab experiment!):\n"
         "• ROC-AUC Curve: 0.9561 (exceptional classification separation).\n"
         "• Precision-Recall Curve (PR-AUC): 0.2431 (a 10.7-fold lift over the 0.0227 random baseline under extreme class imbalance).\n"
         "• Brier Score Loss: 0.0187 (near-perfect probability calibration).\n"
         "• Optimal Classification Threshold: 0.155 (tuned to maximize F1-score).\n"
         "• Feature Importance: 27 total features (25 numerical, 2 categorical handled by CatBoost)."),

        ("SCREEN 6: Workers Directory (/workers)",
         "What to show Ma'am:\n"
         "• 1,000 Couriers Table: Search by worker ID, filter by Vehicle Type (Bike, Scooter, Car, Van) or Availability.\n"
         "• Courier Archetypes: Full-Time Veteran, Part-Time Student, Weekend Gig Worker.\n"
         "• Slide-out Drawer: Click any courier row to see their 7-day workload hours, historical completion rate, and active vehicle."),

        ("SCREEN 7: Tasks Directory (/tasks)",
         "What to show Ma'am:\n"
         "• 3,000 Tasks Catalog with priority badges (High, Medium, Low) and payout values.\n"
         "• 'Create New Task' button: Opens a validated modal to inject synthetic delivery orders into the database in real-time."),

        ("SCREEN 8: Allocation History & Audit Log (/history)",
         "What to show Ma'am:\n"
         "• Relational audit log of all confirmed allocations.\n"
         "• Click any row to view the stored candidate rankings JSON, final score, and explanation stored permanently in SQLite."),

        ("SCREEN 9: Reports & CSV Exporter (/reports)",
         "What to show Ma'am:\n"
         "• Summary analytics on fleet throughput.\n"
         "• One-click CSV export buttons for allocations.csv, workers.csv, and audit_log.csv."),

        ("SCREEN 10: Settings & LLM Provider Setup (/settings)",
         "What to show Ma'am:\n"
         "• Default policy selector (WAFR vs ML-Only vs Nearest Eligible).\n"
         "• AI provider status reported by the backend; Gemini credentials are configured only in the backend environment.")
    ]

    for title, desc in screens:
        p_s = doc.add_paragraph()
        p_s.paragraph_format.space_before = Pt(8)
        p_s.paragraph_format.space_after = Pt(4)
        r_st = p_s.add_run(title)
        r_st.font.bold = True
        r_st.font.size = Pt(12)
        r_st.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

        p_sd = doc.add_paragraph()
        p_sd.paragraph_format.space_after = Pt(6)
        p_sd.add_run(desc)

    # =========================================================================
    # PART 4: TOP 10 TRICKY QUESTIONS FROM MA'AM & BULLETPROOF ANSWERS
    # =========================================================================
    h4 = doc.add_heading("PART 4: Top 10 Questions Ma'am Might Ask & Your Answers", level=1)
    h4.style.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)

    viva_questions = [
        ("Q1: Why did you use Prompt Engineering instead of just writing Python if-else statements?",
         "Answer: Python if-else statements are rigid and cannot produce nuanced, human-understandable natural language explanations for gig workers. "
         "Furthermore, our 6-agent system uses Prompt Engineering for autonomous delegation: each agent has a specialized system prompt, "
         "input/output JSON contracts, and constrained schemas. In the Explainability stage, a zero-shot structured prompt "
         "summarizes supplied ML probabilities, distance deltas, and UN SDG 8 factors without requesting private reasoning."),

        ("Q2: Why is the predicted success probability 58% on some tasks and 90% on others?",
         "Answer: Because tasks have different difficulty levels! An express grocery delivery with a 15-minute deadline and heavy cargo in bad weather "
         "has a much lower baseline probability of successful completion (e.g. 58%) than a standard document dispatch with a 2-hour deadline (e.g. 91%). "
         "The ML ensemble accurately captures this real-world variance across its 27 features."),

        ("Q3: Why is PR-AUC 0.2431 considered good if ROC-AUC is 0.9561?",
         "Answer: In gig allocation datasets, failure events are extremely rare (only 2.27% of instances). Under extreme class imbalance, "
         "ROC-AUC can look artificially high because true negatives dominate. PR-AUC evaluates precision vs recall solely on the rare failure class. "
         "A random classifier achieves only 0.0227. Our score of 0.2431 is a 10.7-fold improvement over random chance!"),

        ("Q4: What is the significance of the 0.155 decision threshold?",
         "Answer: Standard classification assumes a 0.50 cutoff. But when failures happen in only 2.27% of cases, a 0.50 cutoff classifies almost everything "
         "as successful, failing to catch risky deliveries. By analyzing the Precision-Recall curve in Colab, we identified 0.155 as the optimal threshold "
         "that balances false alarms and missed failures."),

        ("Q5: What happens if you slide Lambda (λ) to 0?",
         "Answer: When Lambda = 0, the WAFR formula simplifies to 0.70 × ML + 0.30 × Efficiency. Opportunity credit and workload penalty become 0. "
         "The platform behaves in purely greedy mode, giving all orders to the closest or highest-rated couriers and causing worker starvation."),

        ("Q6: How does the system prevent courier burnout?",
         "Answer: Through the Workload Pressure term in WAFR: Workload Pressure = min(1.0, hours_worked_7d / 40.0). "
         "If a courier has worked 38 or 40 hours this week, their pressure score is near 1.0. When multiplied by Lambda, this acts as a direct penalty, "
         "naturally diverting new tasks to fresher couriers."),

        ("Q7: What does Jain's Fairness Index measure?",
         "Answer: It measures equality of opportunity among all 1,000 workers. A score of 1.0 means every worker has the exact same number of gigs. "
         "Greedy platforms have a low Jain's Index around 0.41. FairGig AI achieves 0.882, proving that work opportunities are equitably spread."),

        ("Q8: Why did you choose HistGradientBoosting + CatBoost as your ensemble?",
         "Answer: Tabular gig data has both continuous numeric features (distance, speed, ratings) and categorical features (vehicle type, required skill). "
         "HistGradientBoosting bins numeric features with extreme efficiency, while CatBoost natively processes categorical features without one-hot encoding explosion. "
         "Weighted 50-50, they provide lower variance and higher calibration (Brier score 0.0187)."),

        ("Q9: What happens if your Gemini API key fails or you lose internet?",
         "Answer: We engineered an automatic fallback mechanism! If Gemini returns a 404, rate limit, or network error, our system seamlessly falls back "
         "to deterministic backend explanation logic. The offline result is clearly marked and uses the same supplied task, worker, allocation, and fairness data."),

        ("Q10: Why did you set LLM temperature to 0.2?",
         "Answer: In creative writing, high temperature (0.8) is good. But in regulatory auditing and algorithmic fairness, we need deterministic, "
         "reproducible, and fact-grounded outputs. A low temperature of 0.2 ensures the LLM sticks strictly to the mathematical data without hallucinating.")
    ]

    for q, a in viva_questions:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(6)
        p_q.paragraph_format.space_after = Pt(2)
        r_q = p_q.add_run(q)
        r_q.font.bold = True
        r_q.font.color.rgb = RGBColor(0x29, 0x26, 0x3D)

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_after = Pt(6)
        p_a.add_run(a)

    # Save Word document
    output_path = os.path.join(os.path.dirname(__file__), "..", "FairGig_AI_Demo_Presentation_Script_and_Guide.docx")
    output_path = os.path.abspath(output_path)
    doc.save(output_path)
    print(f"Presentation script successfully created at: {output_path}")

if __name__ == "__main__":
    create_demo_presentation_doc()
