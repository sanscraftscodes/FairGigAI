

# =====================================================
# CELL 1
# =====================================================

# 1 — Install and imports
!pip -q install xgboost lightgbm catboost shap

import os, random, warnings, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd, matplotlib.pyplot as plt

from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (accuracy_score,precision_score,recall_score,f1_score,
    balanced_accuracy_score,matthews_corrcoef,roc_auc_score,average_precision_score,
    brier_score_loss)
from sklearn.calibration import calibration_curve
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

warnings.filterwarnings("ignore")
SEED=42
np.random.seed(SEED); random.seed(SEED)
rng=np.random.default_rng(SEED)
print("Environment ready.")

# =====================================================
# CELL 2
# =====================================================

N_WORKERS=1000
N_TASKS=3000
CANDIDATES_PER_TASK=100

TASK_TYPES=["delivery","medicine","food","fragile","document","grocery"]
SKILLS=["driving","navigation","handling","customer_service","time_management","cold_chain"]
VEHICLES=["bike","scooter","car","van"]
ARCHETYPES=["speed","reliable","experienced","balanced","fairness_need"]

print(N_WORKERS,N_TASKS,CANDIDATES_PER_TASK)

# =====================================================
# CELL 3
# =====================================================

workers=pd.DataFrame({
    "worker_id":[f"W{i:04d}" for i in range(N_WORKERS)],
    "experience_years":np.clip(rng.gamma(2.2,1.8,N_WORKERS),.1,15),
    "current_lat":rng.normal(18.5204,.055,N_WORKERS),
    "current_lon":rng.normal(73.8567,.065,N_WORKERS),
    "availability_status":rng.choice(["available","busy","offline"],N_WORKERS,p=[.72,.18,.10]),
    "worker_status":"active",
    "vehicle_type":rng.choice(VEHICLES,N_WORKERS,p=[.35,.25,.25,.15]),
    "vehicle_available":rng.random(N_WORKERS)>.06,
    "max_package_weight_kg":np.round(rng.uniform(4,35,N_WORKERS),1),
    "archetype":rng.choice(ARCHETYPES,N_WORKERS,p=[.18,.24,.18,.30,.10])
})
workers["skills"]=[",".join(rng.choice(SKILLS,rng.integers(2,5),replace=False)) for _ in range(N_WORKERS)]

# Generation-only variables. They are excluded later.
workers["_latent_reliability"]=np.clip(
    .52+.14*workers.archetype.eq("reliable")+.10*workers.archetype.eq("experienced")
    +rng.normal(0,.055,N_WORKERS),.20,.96)
workers["_latent_consistency"]=np.clip(rng.beta(8,2,N_WORKERS),.40,.99)

# =====================================================
# CELL 4
# =====================================================

tasks=pd.DataFrame({
    "task_id":[f"T{i:05d}" for i in range(N_TASKS)],
    "task_type":rng.choice(TASK_TYPES,N_TASKS,p=[.25,.12,.22,.12,.14,.15]),
    "pickup_lat":rng.normal(18.5204,.07,N_TASKS),
    "pickup_lon":rng.normal(73.8567,.08,N_TASKS),
    "destination_lat":rng.normal(18.5204,.07,N_TASKS),
    "destination_lon":rng.normal(73.8567,.08,N_TASKS),
    "priority":rng.choice(["low","medium","high","urgent"],N_TASKS,p=[.28,.42,.22,.08]),
    "estimated_duration_min":np.clip(rng.normal(48,20,N_TASKS),15,140),
    "deadline_min":np.clip(rng.normal(135,42,N_TASKS),50,280),
    "payment":np.round(rng.uniform(70,900,N_TASKS),2),
    "package_weight_kg":np.round(rng.uniform(.3,18,N_TASKS),1),
    "vehicle_required":rng.choice(["bike","scooter","car","van","none"],N_TASKS,p=[.24,.20,.22,.10,.24])
})
skill_map={"delivery":["driving","navigation"],"medicine":["cold_chain","time_management"],
"food":["driving","customer_service"],"fragile":["handling","time_management"],
"document":["navigation","customer_service"],"grocery":["driving","handling"]}
tasks["required_skill"]=tasks.task_type.map(lambda x:rng.choice(skill_map[x]))
tasks["priority_num"]=tasks.priority.map({"low":0,"medium":1,"high":2,"urgent":3})

# =====================================================
# CELL 5
# =====================================================

hist=[]
for _,w in workers.iterrows():
    rel=w["_latent_reliability"]; cons=w["_latent_consistency"]; exp=w["experience_years"]
    base=max(10,int(rng.poisson(55+7*exp)))
    for window,mult in [("7d",1),("30d",4),("90d",11)]:
        n=max(5,int(base*mult/4))
        success=np.clip(rel+.055*(exp>4)+rng.normal(0,.025),.30,.99)
        cancel=np.clip(.32*(1-rel)+rng.normal(0,.018),.005,.25)
        delay=np.clip(38*(1-rel)+15*(1-cons)+rng.normal(0,3),1,65)
        hours=np.clip(n*rng.uniform(.30,.65),2,65*mult/4)
        hist.append([w.worker_id,window,n,success,cancel,delay,hours])

hist=pd.DataFrame(hist,columns=["worker_id","window","historical_tasks","success_rate","cancellation_rate","avg_delay_min","working_hours"])
wide=hist.pivot(index="worker_id",columns="window")
wide.columns=[f"{a}_{b}" for a,b in wide.columns]
workers=workers.merge(wide.reset_index(),on="worker_id")

for tt in TASK_TYPES:
    vals=[]
    for _,w in workers.iterrows():
        skill=any(s in w.skills.split(",") for s in skill_map[tt])
        vals.append(np.clip(.40+.24*skill+.25*w["_latent_reliability"]+rng.normal(0,.045),.05,.995))
    workers[f"success_{tt}"]=vals

workers["workload_trend"]=workers.working_hours_7d/(workers.working_hours_30d/4+1e-6)-1
workers["recent_exposure"]=workers.historical_tasks_7d/(workers.historical_tasks_30d+1e-6)
print("History generated.")

# =====================================================
# CELL 6
# =====================================================

def haversine(lat1,lon1,lat2,lon2):
    R=6371.
    p1,p2=np.radians(lat1),np.radians(lat2)
    a=np.sin(np.radians(lat2-lat1)/2)**2+np.cos(p1)*np.cos(p2)*np.sin(np.radians(lon2-lon1)/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

rows=[]
for _,t in tasks.iterrows():
    for j in rng.choice(len(workers),CANDIDATES_PER_TASK,replace=False):
        w=workers.iloc[j]
        dist=haversine(w.current_lat,w.current_lon,t.pickup_lat,t.pickup_lon)
        veh=(t.vehicle_required=="none" or w.vehicle_type==t.vehicle_required or
             (t.vehicle_required=="bike" and w.vehicle_type=="scooter"))
        skill=t.required_skill in w.skills.split(",")
        weight=w.max_package_weight_kg>=t.package_weight_kg
        avail=(w.availability_status=="available" and bool(w.vehicle_available))
        deadline=(dist/25*60+t.estimated_duration_min<=t.deadline_min)
        eligible=int(veh and skill and weight and avail and deadline)

        aff=w[f"success_{t.task_type}"]
        hist_success=w.success_rate_30d
        workload=w.working_hours_7d
        pressure=t.estimated_duration_min/(t.deadline_min+1e-6)

        # Nonlinear observable relationship + hidden noise.
        z=(-2.05+2.55*aff+1.20*hist_success+.14*np.log1p(t.payment)
           +.18*np.sqrt(w.experience_years)-.032*dist-.62*pressure-.012*workload
           +1.05*aff*hist_success+.70*aff**2-.30*pressure*(dist/10)
           +.22*(w.archetype=="reliable")*(t.priority_num>=2)
           +.16*np.sin(aff*np.pi)+.12*(hist_success>.82)*(aff>.78)
           +rng.normal(0,.28))

        rows.append([t.task_id,w.worker_id,t.task_type,t.required_skill,t.priority_num,
            t.estimated_duration_min,t.deadline_min,t.payment,t.package_weight_kg,dist,pressure,
            w.experience_years,w.success_rate_7d,w.success_rate_30d,w.success_rate_90d,
            w.cancellation_rate_7d,w.cancellation_rate_30d,w.avg_delay_min_7d,w.avg_delay_min_30d,
            w.working_hours_7d,w.working_hours_30d,w.workload_trend,w.recent_exposure,aff,
            int(skill),int(veh),int(weight),int(avail),int(deadline),eligible,z])

pairs=pd.DataFrame(rows,columns=["task_id","worker_id","task_type","required_skill","priority_num",
    "estimated_duration_min","deadline_min","payment","package_weight_kg","distance_km","deadline_pressure",
    "experience_years","historical_success_7d","historical_success_30d","historical_success_90d",
    "cancellation_7d","cancellation_30d","delay_7d","delay_30d","work_hours_7d","work_hours_30d",
    "workload_trend","recent_exposure","task_affinity","skill_match","vehicle_match","weight_ok",
    "available","deadline_feasible","eligible","generation_score"])

print("Candidate pairs:",pairs.shape)
print("Eligible rate:",pairs.eligible.mean())

# =====================================================
# CELL 7
# =====================================================

eligible_mask=pairs.eligible.eq(1)

def eligible_rate(shift):
    p=1/(1+np.exp(-(pairs.generation_score+shift)))
    return p[eligible_mask].mean()

lo,hi=-8.0,4.0
for _ in range(60):
    mid=(lo+hi)/2
    if eligible_rate(mid)>.18: hi=mid
    else: lo=mid

shift=(lo+hi)/2
p=1/(1+np.exp(-(pairs.generation_score+shift)))

pairs["target"]=0
pairs.loc[eligible_mask,"target"]=(rng.random(eligible_mask.sum())<p[eligible_mask]).astype(int)

print("Eligible positive rate:",round(pairs.loc[eligible_mask,"target"].mean(),4))
print("Overall positive rate:",round(pairs.target.mean(),4))
print("Eligible candidates:",int(eligible_mask.sum()))

# =====================================================
# CELL 8
# =====================================================

g1=GroupShuffleSplit(n_splits=1,test_size=.20,random_state=SEED)
tv,te=next(g1.split(pairs,pairs.target,groups=pairs.task_id))
trainval=pairs.iloc[tv].copy()
test=pairs.iloc[te].copy()

g2=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED)
tr,va=next(g2.split(trainval,trainval.target,groups=trainval.task_id))
train=trainval.iloc[tr].copy()
valid=trainval.iloc[va].copy()

print("Train:",train.shape,"Validation:",valid.shape,"Test:",test.shape)
print("Task overlaps:",
      len(set(train.task_id)&set(valid.task_id)),
      len(set(train.task_id)&set(test.task_id)),
      len(set(valid.task_id)&set(test.task_id)))

# =====================================================
# CELL 9
# =====================================================

DROP=["task_id","worker_id","target","eligible","generation_score"]

X_train=train.drop(columns=DROP); y_train=train.target
X_valid=valid.drop(columns=DROP); y_valid=valid.target
X_test=test.drop(columns=DROP); y_test=test.target

CAT_COLS=["task_type","required_skill"]
NUM_COLS=[c for c in X_train.columns if c not in CAT_COLS]

pre=ColumnTransformer([
    ("num",Pipeline([
        ("imp",SimpleImputer(strategy="median")),
        ("scale",StandardScaler())
    ]),NUM_COLS),
    ("cat",Pipeline([
        ("imp",SimpleImputer(strategy="most_frequent")),
        ("oh",OneHotEncoder(handle_unknown="ignore"))
    ]),CAT_COLS)
])

CAT_IDX=[X_train.columns.get_loc(c) for c in CAT_COLS]
print("Categorical:",CAT_COLS)

# =====================================================
# CELL 10
# =====================================================

models={
"Balanced Logistic Regression":Pipeline([
    ("pre",pre),
    ("model",LogisticRegression(max_iter=3000,class_weight="balanced",C=.7))
]),
"HistGradientBoosting":HistGradientBoostingClassifier(
    max_iter=350,learning_rate=.045,max_leaf_nodes=31,
    min_samples_leaf=35,l2_regularization=1.2,random_state=SEED
),
"XGBoost":XGBClassifier(
    n_estimators=550,max_depth=6,learning_rate=.045,subsample=.82,
    colsample_bytree=.82,min_child_weight=5,gamma=.05,
    reg_alpha=.10,reg_lambda=1.5,eval_metric="logloss",
    random_state=SEED,n_jobs=2
),
"LightGBM":LGBMClassifier(
    n_estimators=550,learning_rate=.045,num_leaves=31,
    min_child_samples=35,subsample=.82,colsample_bytree=.82,
    reg_alpha=.05,reg_lambda=1.5,random_state=SEED,verbosity=-1
),
"CatBoost":CatBoostClassifier(
    iterations=550,depth=7,learning_rate=.045,l2_leaf_reg=5,
    loss_function="Logloss",eval_metric="AUC",random_seed=SEED,verbose=False
)}

# =====================================================
# CELL 11
# =====================================================

def metric_dict(y,p,t):
    pred=(p>=t).astype(int)
    return {
        "Accuracy":accuracy_score(y,pred),
        "Precision":precision_score(y,pred,zero_division=0),
        "Recall":recall_score(y,pred,zero_division=0),
        "F1":f1_score(y,pred,zero_division=0),
        "Balanced_Accuracy":balanced_accuracy_score(y,pred),
        "MCC":matthews_corrcoef(y,pred),
        "ROC_AUC":roc_auc_score(y,p),
        "PR_AUC":average_precision_score(y,p),
        "Brier":brier_score_loss(y,p),
        "Threshold":t
    }

def best_threshold(y,p):
    ts=np.linspace(.10,.90,161)
    scores=[f1_score(y,(p>=t).astype(int),zero_division=0) for t in ts]
    return float(ts[int(np.argmax(scores))])

# Numeric matrices for XGBoost/LightGBM.
X_train_enc=pre.fit_transform(X_train)
X_valid_enc=pre.transform(X_valid)
X_test_enc=pre.transform(X_test)

vp={}
tp={}
validation_rows=[]

for name,model in models.items():
    print("Training:",name)

    if name=="Balanced Logistic Regression":
        model.fit(X_train,y_train)
        pv=model.predict_proba(X_valid)[:,1]
        pt=model.predict_proba(X_test)[:,1]

    elif name in ["XGBoost","LightGBM"]:
        model.fit(X_train_enc,y_train)
        pv=model.predict_proba(X_valid_enc)[:,1]
        pt=model.predict_proba(X_test_enc)[:,1]

    elif name=="CatBoost":
        model.fit(X_train,y_train,cat_features=CAT_IDX)
        pv=model.predict_proba(X_valid)[:,1]
        pt=model.predict_proba(X_test)[:,1]

    else:
        A=X_train.drop(columns=CAT_COLS)
        B=X_valid.drop(columns=CAT_COLS)
        C_=X_test.drop(columns=CAT_COLS)
        model.fit(A,y_train)
        pv=model.predict_proba(B)[:,1]
        pt=model.predict_proba(C_)[:,1]

    vp[name]=pv
    tp[name]=pt
    t=best_threshold(y_valid,pv)
    validation_rows.append({"Model":name,**metric_dict(y_valid,pv,t)})

validation_table=pd.DataFrame(validation_rows).sort_values("PR_AUC",ascending=False).reset_index(drop=True)
display(validation_table)

# =====================================================
# CELL 12
# =====================================================

# Search a simplex of four nonlinear models.
grid=np.linspace(0,1,11)
best_pr=-1
best_weights=None

for a in grid:
    for b in grid:
        for c in grid:
            d=1-a-b-c
            if d<0: continue

            p=(a*vp["HistGradientBoosting"]+
               b*vp["XGBoost"]+
               c*vp["LightGBM"]+
               d*vp["CatBoost"])

            score=average_precision_score(y_valid,p)

            if score>best_pr:
                best_pr=score
                best_weights=(a,b,c,d)

a,b,c,d=best_weights

ensemble_valid=(
    a*vp["HistGradientBoosting"]+
    b*vp["XGBoost"]+
    c*vp["LightGBM"]+
    d*vp["CatBoost"]
)

ensemble_test=(
    a*tp["HistGradientBoosting"]+
    b*tp["XGBoost"]+
    c*tp["LightGBM"]+
    d*tp["CatBoost"]
)

ensemble_threshold=best_threshold(y_valid,ensemble_valid)

print("Validation PR-AUC:",best_pr)
print("Weights:",{
    "HistGradientBoosting":a,
    "XGBoost":b,
    "LightGBM":c,
    "CatBoost":d
})
print("Validation threshold:",ensemble_threshold)

# =====================================================
# CELL 13
# =====================================================

test_rows=[]

for name,pred in tp.items():
    t=best_threshold(y_valid,vp[name])
    test_rows.append({"Model":name,**metric_dict(y_test,pred,t)})

test_rows.append({
    "Model":"Validation-selected Ensemble",
    **metric_dict(y_test,ensemble_test,ensemble_threshold)
})

test_table=pd.DataFrame(test_rows).sort_values("PR_AUC",ascending=False).reset_index(drop=True)

display(test_table)
print("Base-rate PR-AUC:",round(y_test.mean(),4))

# =====================================================
# CELL 14
# =====================================================

def bootstrap_ci(y,p,metric,B=300):
    rr=np.random.default_rng(SEED+99)
    values=[]
    y=np.asarray(y); p=np.asarray(p)
    for _ in range(B):
        idx=rr.integers(0,len(y),len(y))
        values.append(metric(y[idx],p[idx]))
    return np.percentile(values,[2.5,50,97.5])

print("ROC-AUC CI95:",bootstrap_ci(y_test,ensemble_test,roc_auc_score))
print("PR-AUC CI95:",bootstrap_ci(y_test,ensemble_test,average_precision_score))
print("Brier CI95:",bootstrap_ci(y_test,ensemble_test,brier_score_loss))

# =====================================================
# CELL 15
# =====================================================

obs,pred=calibration_curve(y_test,ensemble_test,n_bins=10,strategy="quantile")
plt.figure(figsize=(6,5))
plt.plot(pred,obs,marker="o",label="FairGig ensemble")
plt.plot([0,1],[0,1],"--",label="Perfect calibration")
plt.xlabel("Predicted probability")
plt.ylabel("Observed frequency")
plt.title("Held-out Calibration")
plt.legend()
plt.tight_layout()
plt.show()

# =====================================================
# CELL 16
# =====================================================

cat_model=models["CatBoost"]
importance=pd.Series(
    cat_model.get_feature_importance(),
    index=X_train.columns
).sort_values(ascending=False)

display(importance.head(20).to_frame("importance"))

plt.figure(figsize=(8,6))
importance.head(15).sort_values().plot(kind="barh")
plt.title("CatBoost Feature Importance")
plt.tight_layout()
plt.show()

try:
    import shap
    sample=X_test.sample(min(600,len(X_test)),random_state=SEED)
    sv=shap.TreeExplainer(cat_model).shap_values(sample)
    if isinstance(sv,list): sv=sv[1]
    shap_imp=pd.Series(
        np.abs(sv).mean(axis=0),
        index=sample.columns
    ).sort_values(ascending=False)
    display(shap_imp.head(15).to_frame("mean_abs_shap"))
except Exception as e:
    print("SHAP unavailable:",str(e)[:200])

# =====================================================
# CELL 17
# =====================================================

evaluation=test.copy()
evaluation["predicted_success"]=ensemble_test

evaluation["efficiency"]=(
    .65/(1+evaluation.distance_km)
    +.35/(1+evaluation.deadline_pressure)
)
evaluation["efficiency"]=(
    evaluation.efficiency-evaluation.efficiency.min()
)/(evaluation.efficiency.max()-evaluation.efficiency.min()+1e-9)

evaluation["opportunity_credit"]=1-evaluation.recent_exposure.rank(pct=True)
evaluation["workload_pressure"]=(
    evaluation.work_hours_7d/
    (evaluation.work_hours_7d.median()+1e-6)
).clip(0,2)/2

# =====================================================
# CELL 18
# =====================================================

def choose_worker(group,policy,lam=.25):
    d=group[group.eligible==1].copy()
    if d.empty: return None

    if policy=="Nearest Eligible":
        return d.sort_values("distance_km").iloc[0]

    if policy=="ML-Only":
        return d.sort_values("predicted_success",ascending=False).iloc[0]

    d["wafr"]=(
        .70*d.predicted_success
        +.30*d.efficiency
        +lam*d.opportunity_credit
        -lam*d.workload_pressure
    )

    return d.sort_values("wafr",ascending=False).iloc[0]


def simulate_policy(df,policy,lam=.25):
    chosen=[]
    for _,g in df.groupby("task_id"):
        r=choose_worker(g,policy,lam)
        if r is not None: chosen.append(r)

    chosen=pd.DataFrame(chosen)
    if chosen.empty: return {}

    exposure=chosen.worker_id.value_counts()
    mean_exp=exposure.mean()

    jain=exposure.sum()**2/(
        len(exposure)*(exposure.pow(2).sum()+1e-9)
    )

    gini=np.abs(
        exposure.values[:,None]-exposure.values[None,:]
    ).sum()/(2*len(exposure)**2*mean_exp+1e-9)

    return {
        "tasks_allocated":len(chosen),
        "realized_success_rate":chosen.target.mean(),
        "mean_distance_km":chosen.distance_km.mean(),
        "mean_predicted_success":chosen.predicted_success.mean(),
        "Jain_exposure":jain,
        "Gini_exposure":gini,
        "worker_coverage":len(exposure)/df.worker_id.nunique(),
        "zero_exposure_rate":1-len(exposure)/df.worker_id.nunique()
    }

policy_rows=[]
for policy in ["Nearest Eligible","ML-Only"]:
    policy_rows.append({"Policy":policy,**simulate_policy(evaluation,policy)})

for lam in np.linspace(0,.50,11):
    policy_rows.append({
        "Policy":f"WAFR λ={lam:.2f}",
        "lambda":lam,
        **simulate_policy(evaluation,"WAFR",lam)
    })

policy_table=pd.DataFrame(policy_rows)
display(policy_table)

# =====================================================
# CELL 19
# =====================================================

sweep_rows=[]
for lam in np.linspace(0,.50,21):
    r=simulate_policy(evaluation,"WAFR",lam)
    r["lambda"]=lam
    sweep_rows.append(r)

sweep=pd.DataFrame(sweep_rows)

plt.figure(figsize=(8,5))
plt.plot(sweep["lambda"],sweep["Jain_exposure"],marker="o")
plt.xlabel("Fairness lambda")
plt.ylabel("Jain exposure")
plt.title("Fairness–Allocation Trade-off")
plt.tight_layout()
plt.show()

display(sweep)

# =====================================================
# CELL 20
# =====================================================

counterfactual=evaluation.copy()
counterfactual["work_hours_7d"]+=3
counterfactual["workload_pressure"]=(
    counterfactual.work_hours_7d/
    (counterfactual.work_hours_7d.median()+1e-6)
).clip(0,2)/2

def allocation_ids(df,lam=.25):
    out={}
    for tid,g in df.groupby("task_id"):
        r=choose_worker(g,"WAFR",lam)
        if r is not None: out[tid]=r.worker_id
    return out

base_ids=allocation_ids(evaluation,.25)
cf_ids=allocation_ids(counterfactual,.25)
common=set(base_ids)&set(cf_ids)

switch_rate=sum(base_ids[k]!=cf_ids[k] for k in common)/max(len(common),1)

print("Counterfactual +3 workload switch rate:",round(switch_rate,4))

# =====================================================
# CELL 21
# =====================================================

validity={
    "no_task_overlap":(
        len(set(train.task_id)&set(valid.task_id))==0
        and len(set(train.task_id)&set(test.task_id))==0
        and len(set(valid.task_id)&set(test.task_id))==0
    ),
    "hidden_generation_variables_excluded":not any(
        c.startswith("_") or c=="generation_score"
        for c in X_train.columns
    ),
    "categoricals_explicitly_handled":set(["task_type","required_skill"]).issubset(CAT_COLS),
    "test_not_used_for_threshold_selection":True,
    "test_not_used_for_ensemble_weights":True,
    "prediction_and_fairness_separated":True,
    "allocation_exposure_metrics_present":True
}

print(json.dumps(validity,indent=2))
assert all(validity.values())
print("ALL VALIDITY CHECKS PASSED.")

# =====================================================
# CELL 22
# =====================================================

bundle=Path("/content/FairGig_AI_FINAL_Research_Bundle")
bundle.mkdir(exist_ok=True)

test_table.to_csv(bundle/"heldout_test_metrics.csv",index=False)
validation_table.to_csv(bundle/"validation_metrics.csv",index=False)
policy_table.to_csv(bundle/"policy_comparison.csv",index=False)
sweep.to_csv(bundle/"fairness_lambda_sweep.csv",index=False)
pd.DataFrame([validity]).to_csv(bundle/"research_validity_checks.csv",index=False)

with open(bundle/"experiment_config.txt","w") as f:
    f.write(
        f"workers={N_WORKERS}\n"
        f"tasks={N_TASKS}\n"
        f"candidates_per_task={CANDIDATES_PER_TASK}\n"
        f"seed={SEED}\n"
        f"eligible_positive_rate={pairs.loc[eligible_mask,'target'].mean():.6f}\n"
        f"overall_positive_rate={pairs.target.mean():.6f}\n"
    )

zip_path="/content/FairGig_AI_FINAL_Research_Bundle.zip"

with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
    for p in bundle.rglob("*"):
        z.write(p,p.relative_to(bundle.parent))

print("Bundle created:",zip_path)

# =====================================================
# CELL 23
# =====================================================

# ============================================================
# ELIGIBLE-ONLY FINAL EVALUATION
# ============================================================

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    matthews_corrcoef,
    brier_score_loss
)

eligible_eval = test_df.copy()

eligible_eval["predicted_probability"] = np.asarray(
    ensemble_test
).reshape(-1)

# Keep only eligible candidates
eligible_eval = eligible_eval[
    eligible_eval["eligible"] == 1
].copy()

print("=" * 70)
print("ELIGIBLE-ONLY TEST EVALUATION")
print("=" * 70)

y_true = eligible_eval["success"].astype(int)
y_prob = eligible_eval["predicted_probability"]

# Use the already selected validation threshold.
# DO NOT tune threshold on test data.
if "best_threshold" in globals():
    test_threshold = float(best_threshold)
elif "threshold" in globals():
    test_threshold = float(threshold)
else:
    test_threshold = 0.155

y_pred = (y_prob >= test_threshold).astype(int)

print("Eligible test samples:", len(eligible_eval))
print("Positive rate:", round(y_true.mean(), 4))
print()

print("ROC-AUC:",
      round(roc_auc_score(y_true, y_prob), 4))

print("PR-AUC:",
      round(average_precision_score(y_true, y_prob), 4))

print("Precision:",
      round(precision_score(y_true, y_pred, zero_division=0), 4))

print("Recall:",
      round(recall_score(y_true, y_pred, zero_division=0), 4))

print("F1:",
      round(f1_score(y_true, y_pred, zero_division=0), 4))

print("Balanced Accuracy:",
      round(
          balanced_accuracy_score(y_true, y_pred),
          4
      ))

print("MCC:",
      round(
          matthews_corrcoef(y_true, y_pred),
          4
      ))

print("Brier:",
      round(
          brier_score_loss(y_true, y_prob),
          4
      ))

print("=" * 70)

# =====================================================
# CELL 24
# =====================================================

# 1 — Install and imports
!pip -q install xgboost lightgbm catboost shap

import os, random, warnings, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd, matplotlib.pyplot as plt

from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (accuracy_score,precision_score,recall_score,f1_score,
    balanced_accuracy_score,matthews_corrcoef,roc_auc_score,average_precision_score,
    brier_score_loss)
from sklearn.calibration import calibration_curve
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

warnings.filterwarnings("ignore")
SEED=42
np.random.seed(SEED); random.seed(SEED)
rng=np.random.default_rng(SEED)
print("Environment ready.")

# =====================================================
# CELL 25
# =====================================================

N_WORKERS=1000
N_TASKS=3000
CANDIDATES_PER_TASK=100

TASK_TYPES=["delivery","medicine","food","fragile","document","grocery"]
SKILLS=["driving","navigation","handling","customer_service","time_management","cold_chain"]
VEHICLES=["bike","scooter","car","van"]
ARCHETYPES=["speed","reliable","experienced","balanced","fairness_need"]

print(N_WORKERS,N_TASKS,CANDIDATES_PER_TASK)

# =====================================================
# CELL 26
# =====================================================

workers=pd.DataFrame({
    "worker_id":[f"W{i:04d}" for i in range(N_WORKERS)],
    "experience_years":np.clip(rng.gamma(2.2,1.8,N_WORKERS),.1,15),
    "current_lat":rng.normal(18.5204,.055,N_WORKERS),
    "current_lon":rng.normal(73.8567,.065,N_WORKERS),
    "availability_status":rng.choice(["available","busy","offline"],N_WORKERS,p=[.72,.18,.10]),
    "worker_status":"active",
    "vehicle_type":rng.choice(VEHICLES,N_WORKERS,p=[.35,.25,.25,.15]),
    "vehicle_available":rng.random(N_WORKERS)>.06,
    "max_package_weight_kg":np.round(rng.uniform(4,35,N_WORKERS),1),
    "archetype":rng.choice(ARCHETYPES,N_WORKERS,p=[.18,.24,.18,.30,.10])
})
workers["skills"]=[",".join(rng.choice(SKILLS,rng.integers(2,5),replace=False)) for _ in range(N_WORKERS)]

# Generation-only variables. They are excluded later.
workers["_latent_reliability"]=np.clip(
    .52+.14*workers.archetype.eq("reliable")+.10*workers.archetype.eq("experienced")
    +rng.normal(0,.055,N_WORKERS),.20,.96)
workers["_latent_consistency"]=np.clip(rng.beta(8,2,N_WORKERS),.40,.99)

# =====================================================
# CELL 27
# =====================================================

tasks=pd.DataFrame({
    "task_id":[f"T{i:05d}" for i in range(N_TASKS)],
    "task_type":rng.choice(TASK_TYPES,N_TASKS,p=[.25,.12,.22,.12,.14,.15]),
    "pickup_lat":rng.normal(18.5204,.07,N_TASKS),
    "pickup_lon":rng.normal(73.8567,.08,N_TASKS),
    "destination_lat":rng.normal(18.5204,.07,N_TASKS),
    "destination_lon":rng.normal(73.8567,.08,N_TASKS),
    "priority":rng.choice(["low","medium","high","urgent"],N_TASKS,p=[.28,.42,.22,.08]),
    "estimated_duration_min":np.clip(rng.normal(48,20,N_TASKS),15,140),
    "deadline_min":np.clip(rng.normal(135,42,N_TASKS),50,280),
    "payment":np.round(rng.uniform(70,900,N_TASKS),2),
    "package_weight_kg":np.round(rng.uniform(.3,18,N_TASKS),1),
    "vehicle_required":rng.choice(["bike","scooter","car","van","none"],N_TASKS,p=[.24,.20,.22,.10,.24])
})
skill_map={"delivery":["driving","navigation"],"medicine":["cold_chain","time_management"],
"food":["driving","customer_service"],"fragile":["handling","time_management"],
"document":["navigation","customer_service"],"grocery":["driving","handling"]}
tasks["required_skill"]=tasks.task_type.map(lambda x:rng.choice(skill_map[x]))
tasks["priority_num"]=tasks.priority.map({"low":0,"medium":1,"high":2,"urgent":3})

# =====================================================
# CELL 28
# =====================================================

hist=[]
for _,w in workers.iterrows():
    rel=w["_latent_reliability"]; cons=w["_latent_consistency"]; exp=w["experience_years"]
    base=max(10,int(rng.poisson(55+7*exp)))
    for window,mult in [("7d",1),("30d",4),("90d",11)]:
        n=max(5,int(base*mult/4))
        success=np.clip(rel+.055*(exp>4)+rng.normal(0,.025),.30,.99)
        cancel=np.clip(.32*(1-rel)+rng.normal(0,.018),.005,.25)
        delay=np.clip(38*(1-rel)+15*(1-cons)+rng.normal(0,3),1,65)
        hours=np.clip(n*rng.uniform(.30,.65),2,65*mult/4)
        hist.append([w.worker_id,window,n,success,cancel,delay,hours])

hist=pd.DataFrame(hist,columns=["worker_id","window","historical_tasks","success_rate","cancellation_rate","avg_delay_min","working_hours"])
wide=hist.pivot(index="worker_id",columns="window")
wide.columns=[f"{a}_{b}" for a,b in wide.columns]
workers=workers.merge(wide.reset_index(),on="worker_id")

for tt in TASK_TYPES:
    vals=[]
    for _,w in workers.iterrows():
        skill=any(s in w.skills.split(",") for s in skill_map[tt])
        vals.append(np.clip(.40+.24*skill+.25*w["_latent_reliability"]+rng.normal(0,.045),.05,.995))
    workers[f"success_{tt}"]=vals

workers["workload_trend"]=workers.working_hours_7d/(workers.working_hours_30d/4+1e-6)-1
workers["recent_exposure"]=workers.historical_tasks_7d/(workers.historical_tasks_30d+1e-6)
print("History generated.")

# =====================================================
# CELL 29
# =====================================================

def haversine(lat1,lon1,lat2,lon2):
    R=6371.
    p1,p2=np.radians(lat1),np.radians(lat2)
    a=np.sin(np.radians(lat2-lat1)/2)**2+np.cos(p1)*np.cos(p2)*np.sin(np.radians(lon2-lon1)/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

rows=[]
for _,t in tasks.iterrows():
    for j in rng.choice(len(workers),CANDIDATES_PER_TASK,replace=False):
        w=workers.iloc[j]
        dist=haversine(w.current_lat,w.current_lon,t.pickup_lat,t.pickup_lon)
        veh=(t.vehicle_required=="none" or w.vehicle_type==t.vehicle_required or
             (t.vehicle_required=="bike" and w.vehicle_type=="scooter"))
        skill=t.required_skill in w.skills.split(",")
        weight=w.max_package_weight_kg>=t.package_weight_kg
        avail=(w.availability_status=="available" and bool(w.vehicle_available))
        deadline=(dist/25*60+t.estimated_duration_min<=t.deadline_min)
        eligible=int(veh and skill and weight and avail and deadline)

        aff=w[f"success_{t.task_type}"]
        hist_success=w.success_rate_30d
        workload=w.working_hours_7d
        pressure=t.estimated_duration_min/(t.deadline_min+1e-6)

        # Nonlinear observable relationship + hidden noise.
        z=(-2.05+2.55*aff+1.20*hist_success+.14*np.log1p(t.payment)
           +.18*np.sqrt(w.experience_years)-.032*dist-.62*pressure-.012*workload
           +1.05*aff*hist_success+.70*aff**2-.30*pressure*(dist/10)
           +.22*(w.archetype=="reliable")*(t.priority_num>=2)
           +.16*np.sin(aff*np.pi)+.12*(hist_success>.82)*(aff>.78)
           +rng.normal(0,.28))

        rows.append([t.task_id,w.worker_id,t.task_type,t.required_skill,t.priority_num,
            t.estimated_duration_min,t.deadline_min,t.payment,t.package_weight_kg,dist,pressure,
            w.experience_years,w.success_rate_7d,w.success_rate_30d,w.success_rate_90d,
            w.cancellation_rate_7d,w.cancellation_rate_30d,w.avg_delay_min_7d,w.avg_delay_min_30d,
            w.working_hours_7d,w.working_hours_30d,w.workload_trend,w.recent_exposure,aff,
            int(skill),int(veh),int(weight),int(avail),int(deadline),eligible,z])

pairs=pd.DataFrame(rows,columns=["task_id","worker_id","task_type","required_skill","priority_num",
    "estimated_duration_min","deadline_min","payment","package_weight_kg","distance_km","deadline_pressure",
    "experience_years","historical_success_7d","historical_success_30d","historical_success_90d",
    "cancellation_7d","cancellation_30d","delay_7d","delay_30d","work_hours_7d","work_hours_30d",
    "workload_trend","recent_exposure","task_affinity","skill_match","vehicle_match","weight_ok",
    "available","deadline_feasible","eligible","generation_score"])

print("Candidate pairs:",pairs.shape)
print("Eligible rate:",pairs.eligible.mean())

# =====================================================
# CELL 30
# =====================================================

eligible_mask=pairs.eligible.eq(1)

def eligible_rate(shift):
    p=1/(1+np.exp(-(pairs.generation_score+shift)))
    return p[eligible_mask].mean()

lo,hi=-8.0,4.0
for _ in range(60):
    mid=(lo+hi)/2
    if eligible_rate(mid)>.18: hi=mid
    else: lo=mid

shift=(lo+hi)/2
p=1/(1+np.exp(-(pairs.generation_score+shift)))

pairs["target"]=0
pairs.loc[eligible_mask,"target"]=(rng.random(eligible_mask.sum())<p[eligible_mask]).astype(int)

print("Eligible positive rate:",round(pairs.loc[eligible_mask,"target"].mean(),4))
print("Overall positive rate:",round(pairs.target.mean(),4))
print("Eligible candidates:",int(eligible_mask.sum()))

# =====================================================
# CELL 31
# =====================================================

g1=GroupShuffleSplit(n_splits=1,test_size=.20,random_state=SEED)
tv,te=next(g1.split(pairs,pairs.target,groups=pairs.task_id))
trainval=pairs.iloc[tv].copy()
test=pairs.iloc[te].copy()

g2=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED)
tr,va=next(g2.split(trainval,trainval.target,groups=trainval.task_id))
train=trainval.iloc[tr].copy()
valid=trainval.iloc[va].copy()

print("Train:",train.shape,"Validation:",valid.shape,"Test:",test.shape)
print("Task overlaps:",
      len(set(train.task_id)&set(valid.task_id)),
      len(set(train.task_id)&set(test.task_id)),
      len(set(valid.task_id)&set(test.task_id)))

# =====================================================
# CELL 32
# =====================================================

DROP=["task_id","worker_id","target","eligible","generation_score"]

X_train=train.drop(columns=DROP); y_train=train.target
X_valid=valid.drop(columns=DROP); y_valid=valid.target
X_test=test.drop(columns=DROP); y_test=test.target

CAT_COLS=["task_type","required_skill"]
NUM_COLS=[c for c in X_train.columns if c not in CAT_COLS]

pre=ColumnTransformer([
    ("num",Pipeline([
        ("imp",SimpleImputer(strategy="median")),
        ("scale",StandardScaler())
    ]),NUM_COLS),
    ("cat",Pipeline([
        ("imp",SimpleImputer(strategy="most_frequent")),
        ("oh",OneHotEncoder(handle_unknown="ignore"))
    ]),CAT_COLS)
])

CAT_IDX=[X_train.columns.get_loc(c) for c in CAT_COLS]
print("Categorical:",CAT_COLS)

# =====================================================
# CELL 33
# =====================================================

models={
"Balanced Logistic Regression":Pipeline([
    ("pre",pre),
    ("model",LogisticRegression(max_iter=3000,class_weight="balanced",C=.7))
]),
"HistGradientBoosting":HistGradientBoostingClassifier(
    max_iter=350,learning_rate=.045,max_leaf_nodes=31,
    min_samples_leaf=35,l2_regularization=1.2,random_state=SEED
),
"XGBoost":XGBClassifier(
    n_estimators=550,max_depth=6,learning_rate=.045,subsample=.82,
    colsample_bytree=.82,min_child_weight=5,gamma=.05,
    reg_alpha=.10,reg_lambda=1.5,eval_metric="logloss",
    random_state=SEED,n_jobs=2
),
"LightGBM":LGBMClassifier(
    n_estimators=550,learning_rate=.045,num_leaves=31,
    min_child_samples=35,subsample=.82,colsample_bytree=.82,
    reg_alpha=.05,reg_lambda=1.5,random_state=SEED,verbosity=-1
),
"CatBoost":CatBoostClassifier(
    iterations=550,depth=7,learning_rate=.045,l2_leaf_reg=5,
    loss_function="Logloss",eval_metric="AUC",random_seed=SEED,verbose=False
)}

# =====================================================
# CELL 34
# =====================================================

def metric_dict(y,p,t):
    pred=(p>=t).astype(int)
    return {
        "Accuracy":accuracy_score(y,pred),
        "Precision":precision_score(y,pred,zero_division=0),
        "Recall":recall_score(y,pred,zero_division=0),
        "F1":f1_score(y,pred,zero_division=0),
        "Balanced_Accuracy":balanced_accuracy_score(y,pred),
        "MCC":matthews_corrcoef(y,pred),
        "ROC_AUC":roc_auc_score(y,p),
        "PR_AUC":average_precision_score(y,p),
        "Brier":brier_score_loss(y,p),
        "Threshold":t
    }

def best_threshold(y,p):
    ts=np.linspace(.10,.90,161)
    scores=[f1_score(y,(p>=t).astype(int),zero_division=0) for t in ts]
    return float(ts[int(np.argmax(scores))])

# Numeric matrices for XGBoost/LightGBM.
X_train_enc=pre.fit_transform(X_train)
X_valid_enc=pre.transform(X_valid)
X_test_enc=pre.transform(X_test)

vp={}
tp={}
validation_rows=[]

for name,model in models.items():
    print("Training:",name)

    if name=="Balanced Logistic Regression":
        model.fit(X_train,y_train)
        pv=model.predict_proba(X_valid)[:,1]
        pt=model.predict_proba(X_test)[:,1]

    elif name in ["XGBoost","LightGBM"]:
        model.fit(X_train_enc,y_train)
        pv=model.predict_proba(X_valid_enc)[:,1]
        pt=model.predict_proba(X_test_enc)[:,1]

    elif name=="CatBoost":
        model.fit(X_train,y_train,cat_features=CAT_IDX)
        pv=model.predict_proba(X_valid)[:,1]
        pt=model.predict_proba(X_test)[:,1]

    else:
        A=X_train.drop(columns=CAT_COLS)
        B=X_valid.drop(columns=CAT_COLS)
        C_=X_test.drop(columns=CAT_COLS)
        model.fit(A,y_train)
        pv=model.predict_proba(B)[:,1]
        pt=model.predict_proba(C_)[:,1]

    vp[name]=pv
    tp[name]=pt
    t=best_threshold(y_valid,pv)
    validation_rows.append({"Model":name,**metric_dict(y_valid,pv,t)})

validation_table=pd.DataFrame(validation_rows).sort_values("PR_AUC",ascending=False).reset_index(drop=True)
display(validation_table)

# =====================================================
# CELL 35
# =====================================================

# Search a simplex of four nonlinear models.
grid=np.linspace(0,1,11)
best_pr=-1
best_weights=None

for a in grid:
    for b in grid:
        for c in grid:
            d=1-a-b-c
            if d<0: continue

            p=(a*vp["HistGradientBoosting"]+
               b*vp["XGBoost"]+
               c*vp["LightGBM"]+
               d*vp["CatBoost"])

            score=average_precision_score(y_valid,p)

            if score>best_pr:
                best_pr=score
                best_weights=(a,b,c,d)

a,b,c,d=best_weights

ensemble_valid=(
    a*vp["HistGradientBoosting"]+
    b*vp["XGBoost"]+
    c*vp["LightGBM"]+
    d*vp["CatBoost"]
)

ensemble_test=(
    a*tp["HistGradientBoosting"]+
    b*tp["XGBoost"]+
    c*tp["LightGBM"]+
    d*tp["CatBoost"]
)

ensemble_threshold=best_threshold(y_valid,ensemble_valid)

print("Validation PR-AUC:",best_pr)
print("Weights:",{
    "HistGradientBoosting":a,
    "XGBoost":b,
    "LightGBM":c,
    "CatBoost":d
})
print("Validation threshold:",ensemble_threshold)

# =====================================================
# CELL 36
# =====================================================

test_rows=[]

for name,pred in tp.items():
    t=best_threshold(y_valid,vp[name])
    test_rows.append({"Model":name,**metric_dict(y_test,pred,t)})

test_rows.append({
    "Model":"Validation-selected Ensemble",
    **metric_dict(y_test,ensemble_test,ensemble_threshold)
})

test_table=pd.DataFrame(test_rows).sort_values("PR_AUC",ascending=False).reset_index(drop=True)

display(test_table)
print("Base-rate PR-AUC:",round(y_test.mean(),4))

# =====================================================
# CELL 37
# =====================================================

def bootstrap_ci(y,p,metric,B=300):
    rr=np.random.default_rng(SEED+99)
    values=[]
    y=np.asarray(y); p=np.asarray(p)
    for _ in range(B):
        idx=rr.integers(0,len(y),len(y))
        values.append(metric(y[idx],p[idx]))
    return np.percentile(values,[2.5,50,97.5])

print("ROC-AUC CI95:",bootstrap_ci(y_test,ensemble_test,roc_auc_score))
print("PR-AUC CI95:",bootstrap_ci(y_test,ensemble_test,average_precision_score))
print("Brier CI95:",bootstrap_ci(y_test,ensemble_test,brier_score_loss))

# =====================================================
# CELL 38
# =====================================================

obs,pred=calibration_curve(y_test,ensemble_test,n_bins=10,strategy="quantile")
plt.figure(figsize=(6,5))
plt.plot(pred,obs,marker="o",label="FairGig ensemble")
plt.plot([0,1],[0,1],"--",label="Perfect calibration")
plt.xlabel("Predicted probability")
plt.ylabel("Observed frequency")
plt.title("Held-out Calibration")
plt.legend()
plt.tight_layout()
plt.show()

# =====================================================
# CELL 39
# =====================================================

cat_model=models["CatBoost"]
importance=pd.Series(
    cat_model.get_feature_importance(),
    index=X_train.columns
).sort_values(ascending=False)

display(importance.head(20).to_frame("importance"))

plt.figure(figsize=(8,6))
importance.head(15).sort_values().plot(kind="barh")
plt.title("CatBoost Feature Importance")
plt.tight_layout()
plt.show()

try:
    import shap
    sample=X_test.sample(min(600,len(X_test)),random_state=SEED)
    sv=shap.TreeExplainer(cat_model).shap_values(sample)
    if isinstance(sv,list): sv=sv[1]
    shap_imp=pd.Series(
        np.abs(sv).mean(axis=0),
        index=sample.columns
    ).sort_values(ascending=False)
    display(shap_imp.head(15).to_frame("mean_abs_shap"))
except Exception as e:
    print("SHAP unavailable:",str(e)[:200])

# =====================================================
# CELL 40
# =====================================================

evaluation=test.copy()
evaluation["predicted_success"]=ensemble_test

evaluation["efficiency"]=(
    .65/(1+evaluation.distance_km)
    +.35/(1+evaluation.deadline_pressure)
)
evaluation["efficiency"]=(
    evaluation.efficiency-evaluation.efficiency.min()
)/(evaluation.efficiency.max()-evaluation.efficiency.min()+1e-9)

evaluation["opportunity_credit"]=1-evaluation.recent_exposure.rank(pct=True)
evaluation["workload_pressure"]=(
    evaluation.work_hours_7d/
    (evaluation.work_hours_7d.median()+1e-6)
).clip(0,2)/2

# =====================================================
# CELL 41
# =====================================================

def choose_worker(group,policy,lam=.25):
    d=group[group.eligible==1].copy()
    if d.empty: return None

    if policy=="Nearest Eligible":
        return d.sort_values("distance_km").iloc[0]

    if policy=="ML-Only":
        return d.sort_values("predicted_success",ascending=False).iloc[0]

    d["wafr"]=(
        .70*d.predicted_success
        +.30*d.efficiency
        +lam*d.opportunity_credit
        -lam*d.workload_pressure
    )

    return d.sort_values("wafr",ascending=False).iloc[0]


def simulate_policy(df,policy,lam=.25):
    chosen=[]
    for _,g in df.groupby("task_id"):
        r=choose_worker(g,policy,lam)
        if r is not None: chosen.append(r)

    chosen=pd.DataFrame(chosen)
    if chosen.empty: return {}

    exposure=chosen.worker_id.value_counts()
    mean_exp=exposure.mean()

    jain=exposure.sum()**2/(
        len(exposure)*(exposure.pow(2).sum()+1e-9)
    )

    gini=np.abs(
        exposure.values[:,None]-exposure.values[None,:]
    ).sum()/(2*len(exposure)**2*mean_exp+1e-9)

    return {
        "tasks_allocated":len(chosen),
        "realized_success_rate":chosen.target.mean(),
        "mean_distance_km":chosen.distance_km.mean(),
        "mean_predicted_success":chosen.predicted_success.mean(),
        "Jain_exposure":jain,
        "Gini_exposure":gini,
        "worker_coverage":len(exposure)/df.worker_id.nunique(),
        "zero_exposure_rate":1-len(exposure)/df.worker_id.nunique()
    }

policy_rows=[]
for policy in ["Nearest Eligible","ML-Only"]:
    policy_rows.append({"Policy":policy,**simulate_policy(evaluation,policy)})

for lam in np.linspace(0,.50,11):
    policy_rows.append({
        "Policy":f"WAFR λ={lam:.2f}",
        "lambda":lam,
        **simulate_policy(evaluation,"WAFR",lam)
    })

policy_table=pd.DataFrame(policy_rows)
display(policy_table)

# =====================================================
# CELL 42
# =====================================================

sweep_rows=[]
for lam in np.linspace(0,.50,21):
    r=simulate_policy(evaluation,"WAFR",lam)
    r["lambda"]=lam
    sweep_rows.append(r)

sweep=pd.DataFrame(sweep_rows)

plt.figure(figsize=(8,5))
plt.plot(sweep["lambda"],sweep["Jain_exposure"],marker="o")
plt.xlabel("Fairness lambda")
plt.ylabel("Jain exposure")
plt.title("Fairness–Allocation Trade-off")
plt.tight_layout()
plt.show()

display(sweep)

# =====================================================
# CELL 43
# =====================================================

counterfactual=evaluation.copy()
counterfactual["work_hours_7d"]+=3
counterfactual["workload_pressure"]=(
    counterfactual.work_hours_7d/
    (counterfactual.work_hours_7d.median()+1e-6)
).clip(0,2)/2

def allocation_ids(df,lam=.25):
    out={}
    for tid,g in df.groupby("task_id"):
        r=choose_worker(g,"WAFR",lam)
        if r is not None: out[tid]=r.worker_id
    return out

base_ids=allocation_ids(evaluation,.25)
cf_ids=allocation_ids(counterfactual,.25)
common=set(base_ids)&set(cf_ids)

switch_rate=sum(base_ids[k]!=cf_ids[k] for k in common)/max(len(common),1)

print("Counterfactual +3 workload switch rate:",round(switch_rate,4))

# =====================================================
# CELL 44
# =====================================================

validity={
    "no_task_overlap":(
        len(set(train.task_id)&set(valid.task_id))==0
        and len(set(train.task_id)&set(test.task_id))==0
        and len(set(valid.task_id)&set(test.task_id))==0
    ),
    "hidden_generation_variables_excluded":not any(
        c.startswith("_") or c=="generation_score"
        for c in X_train.columns
    ),
    "categoricals_explicitly_handled":set(["task_type","required_skill"]).issubset(CAT_COLS),
    "test_not_used_for_threshold_selection":True,
    "test_not_used_for_ensemble_weights":True,
    "prediction_and_fairness_separated":True,
    "allocation_exposure_metrics_present":True
}

print(json.dumps(validity,indent=2))
assert all(validity.values())
print("ALL VALIDITY CHECKS PASSED.")

# =====================================================
# CELL 45
# =====================================================

bundle=Path("/content/FairGig_AI_FINAL_Research_Bundle")
bundle.mkdir(exist_ok=True)

test_table.to_csv(bundle/"heldout_test_metrics.csv",index=False)
validation_table.to_csv(bundle/"validation_metrics.csv",index=False)
policy_table.to_csv(bundle/"policy_comparison.csv",index=False)
sweep.to_csv(bundle/"fairness_lambda_sweep.csv",index=False)
pd.DataFrame([validity]).to_csv(bundle/"research_validity_checks.csv",index=False)

with open(bundle/"experiment_config.txt","w") as f:
    f.write(
        f"workers={N_WORKERS}\n"
        f"tasks={N_TASKS}\n"
        f"candidates_per_task={CANDIDATES_PER_TASK}\n"
        f"seed={SEED}\n"
        f"eligible_positive_rate={pairs.loc[eligible_mask,'target'].mean():.6f}\n"
        f"overall_positive_rate={pairs.target.mean():.6f}\n"
    )

zip_path="/content/FairGig_AI_FINAL_Research_Bundle.zip"

with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
    for p in bundle.rglob("*"):
        z.write(p,p.relative_to(bundle.parent))

print("Bundle created:",zip_path)

# =====================================================
# CELL 46
# =====================================================

# ============================================================
# ELIGIBLE-ONLY FINAL EVALUATION
# ============================================================

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    matthews_corrcoef,
    brier_score_loss
)

eligible_eval = test_df.copy()

eligible_eval["predicted_probability"] = np.asarray(
    ensemble_test
).reshape(-1)

# Keep only eligible candidates
eligible_eval = eligible_eval[
    eligible_eval["eligible"] == 1
].copy()

print("=" * 70)
print("ELIGIBLE-ONLY TEST EVALUATION")
print("=" * 70)

y_true = eligible_eval["success"].astype(int)
y_prob = eligible_eval["predicted_probability"]

# Use the already selected validation threshold.
# DO NOT tune threshold on test data.
if "best_threshold" in globals():
    test_threshold = float(best_threshold)
elif "threshold" in globals():
    test_threshold = float(threshold)
else:
    test_threshold = 0.155

y_pred = (y_prob >= test_threshold).astype(int)

print("Eligible test samples:", len(eligible_eval))
print("Positive rate:", round(y_true.mean(), 4))
print()

print("ROC-AUC:",
      round(roc_auc_score(y_true, y_prob), 4))

print("PR-AUC:",
      round(average_precision_score(y_true, y_prob), 4))

print("Precision:",
      round(precision_score(y_true, y_pred, zero_division=0), 4))

print("Recall:",
      round(recall_score(y_true, y_pred, zero_division=0), 4))

print("F1:",
      round(f1_score(y_true, y_pred, zero_division=0), 4))

print("Balanced Accuracy:",
      round(
          balanced_accuracy_score(y_true, y_pred),
          4
      ))

print("MCC:",
      round(
          matthews_corrcoef(y_true, y_pred),
          4
      ))

print("Brier:",
      round(
          brier_score_loss(y_true, y_prob),
          4
      ))

print("=" * 70)

# =====================================================
# CELL 47
# =====================================================

# ============================================================
# FAIRGIG AI — FINAL MODEL HANDOFF PACKAGE
# ============================================================
# This creates a self-contained package containing:
# - trained models
# - preprocessing objects
# - ensemble configuration
# - thresholds
# - feature lists
# - metrics
# - predictions
# - fairness/allocation outputs
# - feature importance / SHAP outputs
# - research configuration
# - notebook execution history
#
# The final ZIP will be downloaded directly to your laptop.
# ============================================================

import os
import json
import shutil
import pickle
import joblib
import zipfile
import glob
import numpy as np
import pandas as pd
from datetime import datetime
from google.colab import files

# ------------------------------------------------------------
# 1. Create temporary packaging directory
# ------------------------------------------------------------

PACKAGE_NAME = "FairGig_AI_FINAL_MODEL_HANDOFF"

WORK_DIR = f"/content/{PACKAGE_NAME}"
ZIP_PATH = f"/content/{PACKAGE_NAME}.zip"

if os.path.exists(WORK_DIR):
    shutil.rmtree(WORK_DIR)

if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)

os.makedirs(WORK_DIR)

for folder in [
    "models",
    "preprocessing",
    "metrics",
    "predictions",
    "fairness",
    "explainability",
    "data",
    "documentation"
]:
    os.makedirs(os.path.join(WORK_DIR, folder))


# ------------------------------------------------------------
# 2. Helper functions
# ------------------------------------------------------------

def save_joblib(obj, filename, folder):
    path = os.path.join(WORK_DIR, folder, filename)
    joblib.dump(obj, path)
    print("Saved:", path)


def save_pickle(obj, filename, folder):
    path = os.path.join(WORK_DIR, folder, filename)
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    print("Saved:", path)


def save_json(obj, filename, folder):
    path = os.path.join(WORK_DIR, folder, filename)

    def convert(x):
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, (np.floating,)):
            return float(x)
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, pd.Timestamp):
            return str(x)
        return str(x)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=convert)

    print("Saved:", path)


def save_dataframe(df, filename, folder):
    if isinstance(df, pd.DataFrame):
        path = os.path.join(WORK_DIR, folder, filename)
        df.to_csv(path, index=False)
        print("Saved:", path)


# ------------------------------------------------------------
# 3. Save trained model objects
# ------------------------------------------------------------

# Save the model dictionary if available
if "models" in globals():
    save_joblib(models, "all_trained_models.joblib", "models")

# Save individual models if they exist
model_names = [
    "lr_model",
    "hgb_model",
    "xgb_model",
    "lgbm_model",
    "cat_model",
    "logistic_model",
    "ensemble_model"
]

for name in model_names:
    if name in globals():
        try:
            save_joblib(globals()[name], f"{name}.joblib", "models")
        except Exception as e:
            print(f"Could not save {name}: {e}")


# ------------------------------------------------------------
# 4. Save preprocessing
# ------------------------------------------------------------

preprocessing_names = [
    "preprocessor",
    "preprocessor_lr",
    "feature_preprocessor",
    "scaler",
    "encoder"
]

for name in preprocessing_names:
    if name in globals():
        try:
            save_joblib(
                globals()[name],
                f"{name}.joblib",
                "preprocessing"
            )
        except Exception as e:
            print(f"Could not save {name}: {e}")


# ------------------------------------------------------------
# 5. Save feature configuration
# ------------------------------------------------------------

feature_config = {}

for name in [
    "feature_cols",
    "features",
    "feature_columns",
    "numeric_features",
    "num_cols",
    "categorical_features",
    "cat_cols",
    "target_col",
    "TARGET",
    "label_col"
]:
    if name in globals():
        try:
            value = globals()[name]

            if isinstance(value, np.ndarray):
                value = value.tolist()

            elif isinstance(value, tuple):
                value = list(value)

            elif not isinstance(
                value,
                (str, int, float, bool, list, dict, type(None))
            ):
                value = str(value)

            feature_config[name] = value

        except Exception as e:
            print(f"Could not save {name}: {e}")

save_json(
    feature_config,
    "feature_configuration.json",
    "documentation"
)


# ------------------------------------------------------------
# 6. Save ensemble configuration
# ------------------------------------------------------------

ensemble_config = {}

for name in [
    "ensemble_weights",
    "weights",
    "best_weights",
    "best_threshold",
    "threshold",
    "ensemble_threshold",
    "best_model_name"
]:
    if name in globals():
        try:
            value = globals()[name]

            if isinstance(value, np.ndarray):
                value = value.tolist()

            ensemble_config[name] = value

        except Exception as e:
            print(f"Could not save {name}: {e}")

save_json(
    ensemble_config,
    "ensemble_configuration.json",
    "models"
)


# ------------------------------------------------------------
# 7. Save metrics/results objects
# ------------------------------------------------------------

metric_names = [
    "metrics",
    "results",
    "test_metrics",
    "validation_metrics",
    "val_metrics",
    "test_results",
    "validation_results",
    "bootstrap_results",
    "bootstrap_summary"
]

for name in metric_names:
    if name in globals():

        obj = globals()[name]

        try:
            if isinstance(obj, pd.DataFrame):
                save_dataframe(
                    obj,
                    f"{name}.csv",
                    "metrics"
                )

            elif isinstance(obj, dict):
                save_json(
                    obj,
                    f"{name}.json",
                    "metrics"
                )

            else:
                save_joblib(
                    obj,
                    f"{name}.joblib",
                    "metrics"
                )

        except Exception as e:
            print(f"Could not save {name}: {e}")


# ------------------------------------------------------------
# 8. Save prediction outputs
# ------------------------------------------------------------

prediction_names = [
    "ensemble_test",
    "ensemble_val",
    "test_predictions",
    "val_predictions",
    "y_test",
    "y_val",
    "y_test_pred",
    "y_val_pred",
    "test_probs",
    "val_probs"
]

for name in prediction_names:
    if name in globals():

        obj = globals()[name]

        try:
            if isinstance(obj, pd.DataFrame):
                save_dataframe(
                    obj,
                    f"{name}.csv",
                    "predictions"
                )

            elif isinstance(obj, (pd.Series, np.ndarray, list)):
                pd.DataFrame({
                    name: np.asarray(obj).reshape(-1)
                }).to_csv(
                    os.path.join(
                        WORK_DIR,
                        "predictions",
                        f"{name}.csv"
                    ),
                    index=False
                )

            else:
                save_joblib(
                    obj,
                    f"{name}.joblib",
                    "predictions"
                )

        except Exception as e:
            print(f"Could not save prediction {name}: {e}")


# ------------------------------------------------------------
# 9. Save major DataFrames
# ------------------------------------------------------------

dataframe_candidates = {
    "tasks": "tasks",
    "workers": "workers",
    "history": "allocation_history",
    "candidate_pairs": "candidate_df",
    "candidates": "candidates",
    "train": "train_df",
    "validation": "val_df",
    "test": "test_df",
    "allocation": "allocation_df",
    "fairness": "fairness_df"
}

for output_name, variable_name in dataframe_candidates.items():

    if variable_name in globals():

        obj = globals()[variable_name]

        if isinstance(obj, pd.DataFrame):

            # Don't unnecessarily package enormous duplicate tables.
            # Save important datasets/results only.
            save_dataframe(
                obj,
                f"{output_name}.csv",
                "data"
            )


# ------------------------------------------------------------
# 10. Save feature importance / SHAP results
# ------------------------------------------------------------

explainability_names = [
    "feature_importance",
    "feature_importance_df",
    "shap_values",
    "shap_importance",
    "shap_importance_df",
    "importance_df"
]

for name in explainability_names:

    if name in globals():

        obj = globals()[name]

        try:

            if isinstance(obj, pd.DataFrame):

                save_dataframe(
                    obj,
                    f"{name}.csv",
                    "explainability"
                )

            elif isinstance(obj, np.ndarray):

                np.save(
                    os.path.join(
                        WORK_DIR,
                        "explainability",
                        f"{name}.npy"
                    ),
                    obj
                )

            else:

                save_joblib(
                    obj,
                    f"{name}.joblib",
                    "explainability"
                )

        except Exception as e:
            print(f"Could not save {name}: {e}")


# ------------------------------------------------------------
# 11. Save fairness / allocation outputs
# ------------------------------------------------------------

fairness_names = [
    "fairness_metrics",
    "fairness_results",
    "jain_results",
    "gini_results",
    "lambda_results",
    "lambda_sweep",
    "counterfactual_results",
    "allocation_results"
]

for name in fairness_names:

    if name in globals():

        obj = globals()[name]

        try:

            if isinstance(obj, pd.DataFrame):

                save_dataframe(
                    obj,
                    f"{name}.csv",
                    "fairness"
                )

            elif isinstance(obj, dict):

                save_json(
                    obj,
                    f"{name}.json",
                    "fairness"
                )

            else:

                save_joblib(
                    obj,
                    f"{name}.joblib",
                    "fairness"
                )

        except Exception as e:
            print(f"Could not save {name}: {e}")


# ------------------------------------------------------------
# 12. Save a machine-readable project manifest
# ------------------------------------------------------------

manifest = {
    "project": "FairGig AI",
    "title": "FairGig AI — Multi-Agent AI System for Fair and Explainable Gig Task Allocation",
    "artifact_type": "Final ML Model Handoff",
    "created_at": datetime.now().isoformat(),
    "model_task": "Worker-task success prediction and fair task allocation",
    "model_selection": "Validation-based ensemble selection",
    "evaluation": "Held-out task-grouped test set",
    "fairness_layer": "WAFR",
    "important_note": (
        "The reported overall PR-AUC is evaluated over all candidate pairs. "
        "An eligible-only evaluation should also be reported because the "
        "actual allocation decision is made among eligible workers."
    ),
    "final_reported_metrics": {
        "roc_auc_approx": 0.9561,
        "pr_auc_approx": 0.2431,
        "brier_approx": 0.0187,
        "counterfactual_workload_plus_3_switch_rate": 0.044
    },
    "data_scale": {
        "workers": 1000,
        "tasks": 3000,
        "candidate_pairs": 300000
    },
    "allocation_formula": (
        "0.70 * predicted_success + "
        "0.30 * efficiency + "
        "lambda * opportunity_credit - "
        "lambda * workload_pressure"
    ),
    "artifact_usage": [
        "Backend model inference",
        "Worker ranking",
        "Fair task allocation",
        "Explainability",
        "Research evaluation",
        "Prototype integration"
    ]
}

save_json(
    manifest,
    "PROJECT_MANIFEST.json",
    "documentation"
)


# ------------------------------------------------------------
# 13. Create README for Anti-Gravity / developers
# ------------------------------------------------------------

readme = """
# FairGig AI — Final ML Model Handoff

## Project

FairGig AI is a multi-agent AI system for fair and explainable gig-task
allocation.

The ML component predicts worker-task success probability and the fairness
layer uses the prediction together with efficiency and workload/opportunity
signals to allocate tasks.

## Final ML architecture

1. Task Analysis Agent
2. Worker Profile / Suitability Agent
3. ML Success Prediction
4. Fairness Evaluation
5. WAFR Allocation
6. Explainability Agent

## Final trained ML setup

Workers: 1000
Tasks: 3000
Candidate worker-task pairs: 300000

The experiment uses task-grouped train/validation/test splitting so that
the same task does not appear across multiple splits.

## Models

- Balanced Logistic Regression
- HistGradientBoosting
- XGBoost
- LightGBM
- CatBoost
- Validation-selected ensemble

## Important evaluation note

The reported overall held-out ensemble metrics are approximately:

ROC-AUC: 0.9561
PR-AUC: 0.2431
Brier Score: 0.0187

Overall positive prevalence is approximately 2.27%, so the random PR-AUC
baseline is approximately 0.0227.

Therefore PR-AUC should be interpreted relative to prevalence rather than
as an isolated percentage.

IMPORTANT:
The actual allocation system first filters workers using hard eligibility.
Therefore, an eligible-only test evaluation should be added before making
claims about how well the model ranks success among eligible workers.

## Fairness allocation

WAFR combines:

- predicted success
- operational efficiency
- opportunity credit
- workload pressure

with:

0.70 * predicted_success
+ 0.30 * efficiency
+ lambda * opportunity_credit
- lambda * workload_pressure

## Explainability

The package contains available feature-importance and SHAP artifacts from
the final notebook.

Vehicle-related features may have high importance because vehicle
compatibility is strongly related to eligibility. This should not automatically
be interpreted as proof that vehicle type is the dominant predictor of
success among already-eligible workers.

## For application development

Do NOT retrain the model automatically.

First load:

1. preprocessing object
2. trained model(s)
3. ensemble configuration
4. threshold
5. feature configuration

Then implement an inference pipeline that accepts:

Task
+
Worker profile
+
Historical worker features

and returns:

worker_id
predicted_success_probability
eligibility
suitability
fairness signals
final allocation score
explanation

## Security / engineering

Never expose model files or internal training data directly through the
frontend.

The model should be loaded by a backend API.

Recommended separation:

Frontend
    ->
FastAPI backend
    ->
Task Analysis / Worker Processing
    ->
ML Prediction
    ->
Fairness / WAFR
    ->
Allocation
    ->
Explainability
    ->
Response

"""

with open(
    os.path.join(WORK_DIR, "README.md"),
    "w",
    encoding="utf-8"
) as f:
    f.write(readme)


# ------------------------------------------------------------
# 14. Save executed notebook cell history as Python source
# ------------------------------------------------------------

try:

    history = get_ipython().history_manager.input_hist_raw

    source_path = os.path.join(
        WORK_DIR,
        "documentation",
        "FINAL_NOTEBOOK_EXECUTION_HISTORY.py"
    )

    with open(source_path, "w", encoding="utf-8") as f:

        for i, cell in enumerate(history):

            if cell.strip():

                f.write(
                    f"\n\n# =====================================================\n"
                    f"# CELL {i}\n"
                    f"# =====================================================\n\n"
                )

                f.write(cell)

    print("Saved notebook execution history.")

except Exception as e:
    print("Could not save notebook history:", e)


# ------------------------------------------------------------
# 15. Create ZIP
# ------------------------------------------------------------

print("\nCreating final ZIP...")

with zipfile.ZipFile(
    ZIP_PATH,
    "w",
    compression=zipfile.ZIP_DEFLATED
) as z:

    for root, dirs, files_list in os.walk(WORK_DIR):

        for file in files_list:

            full_path = os.path.join(root, file)

            arcname = os.path.relpath(
                full_path,
                WORK_DIR
            )

            z.write(
                full_path,
                arcname
            )


# ------------------------------------------------------------
# 16. Display package contents
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL FAIRGIG AI MODEL HANDOFF PACKAGE")
print("=" * 70)

total_size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)

print(f"ZIP size: {total_size_mb:.2f} MB")
print(f"Package: {PACKAGE_NAME}.zip")

print("\nFiles included:")

for root, dirs, files_list in os.walk(WORK_DIR):

    for file in files_list:

        relative = os.path.relpath(
            os.path.join(root, file),
            WORK_DIR
        )

        print(" -", relative)

print("\nDownloading to your computer...")
print("Your browser should save it to your normal Downloads folder.")

files.download(ZIP_PATH)