import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  BarChart2,
  Info,
  Layers,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { getModelStatus, getModelMetrics } from '../api/client';

export const ModelInsightsPage: React.FC = () => {
  const [status, setStatus] = useState<any | null>(null);
  const [metrics, setMetrics] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    Promise.all([getModelStatus(), getModelMetrics()])
      .then(([s, m]) => {
        setStatus(s);
        setMetrics(m);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="w-8 h-8 text-[#8B7CF6] animate-spin" />
        <p className="text-sm font-medium text-[#77748C]">Loading model artifacts & research metrics...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Overview Banner */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <h2 className="text-xl font-bold text-[#29263D]">Machine Learning Model Architecture & Validation</h2>
          </div>
          <p className="text-xs text-[#77748C] mt-1">
            Dual-model ensemble combines HistGradientBoosting and CatBoost across 27 domain-engineered features.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-2xl bg-emerald-50 text-emerald-800 font-semibold text-xs border border-emerald-200">
            Ensemble Threshold: {status?.ensemble_threshold || 0.155}
          </span>
          <span className="px-3 py-1.5 rounded-2xl bg-violet-50 text-violet-800 font-semibold text-xs border border-violet-200">
            Features: {status?.total_features_expected || 27}
          </span>
        </div>
      </div>

      {/* Model Status & Weights */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-3xl bg-white border border-[#EAE7F2] shadow-xs space-y-2">
          <span className="text-xs text-[#77748C] font-semibold uppercase">HistGradientBoosting</span>
          <h4 className="text-2xl font-bold text-[#8B7CF6]">Weight 0.50</h4>
          <p className="text-[11px] text-[#77748C]">Evaluates 25 numerical features natively with fast histogram binning.</p>
          <span className="inline-block px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
            {status?.hgb_loaded ? 'Loaded' : 'Unavailable'}
          </span>
        </div>

        <div className="p-5 rounded-3xl bg-white border border-[#EAE7F2] shadow-xs space-y-2">
          <span className="text-xs text-[#77748C] font-semibold uppercase">CatBoost Classifier</span>
          <h4 className="text-2xl font-bold text-[#8B7CF6]">Weight 0.50</h4>
          <p className="text-[11px] text-[#77748C]">Evaluates all 27 features with native categorical handling on task & skill.</p>
          <span className="inline-block px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
            {status?.cat_loaded ? 'Loaded' : 'Unavailable'}
          </span>
        </div>

        <div className="p-5 rounded-3xl bg-white border border-[#EAE7F2] shadow-xs space-y-2">
          <span className="text-xs text-[#77748C] font-semibold uppercase">XGBoost & LightGBM</span>
          <h4 className="text-2xl font-bold text-slate-400">Weight 0.00</h4>
          <p className="text-[11px] text-[#77748C]">Validation simplex optimization determined zero weight in final ensemble.</p>
          <span className="inline-block px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold text-[10px]">
            Zero-weighted
          </span>
        </div>

        <div className="p-5 rounded-3xl bg-white border border-[#EAE7F2] shadow-xs space-y-2">
          <span className="text-xs text-[#77748C] font-semibold uppercase">Environment Status</span>
          <h4 className="text-2xl font-bold text-emerald-700">Operational</h4>
          <p className="text-[11px] text-[#77748C]">Inference verified on Windows with Python 3.13 and scikit-learn shim.</p>
          <span className="inline-block px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
            Verified Parity
          </span>
        </div>
      </div>

      {/* Historical Research Metrics Box */}
      {metrics?.research_metrics && (
        <div className="bg-gradient-to-r from-[#FAF9FE] to-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Held-Out Research Test Set Metrics</h3>
              <p className="text-xs text-[#77748C]">
                Reported experimental results on 60,000 held-out candidate pairs from Google Colab.
              </p>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-amber-50 text-amber-800 font-semibold border border-amber-200">
              Reference Benchmark
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="p-4 rounded-2xl bg-white border border-[#EAE7F2]">
              <span className="text-xs text-[#77748C]">ROC-AUC (Discrimination)</span>
              <h4 className="text-2xl font-bold text-[#8B7CF6] mt-1">{metrics.research_metrics.roc_auc_approx}</h4>
              <span className="text-[10px] text-[#77748C]">Overall candidate pairs</span>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-[#EAE7F2]">
              <span className="text-xs text-[#77748C]">PR-AUC (Precision-Recall)</span>
              <h4 className="text-2xl font-bold text-emerald-700 mt-1">{metrics.research_metrics.pr_auc_approx}</h4>
              <span className="text-[10px] text-emerald-700">10.7× baseline ({metrics.research_metrics.baseline_pr_auc})</span>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-[#EAE7F2]">
              <span className="text-xs text-[#77748C]">Brier Score (Calibration)</span>
              <h4 className="text-2xl font-bold text-[#29263D] mt-1">{metrics.research_metrics.brier_approx}</h4>
              <span className="text-[10px] text-[#77748C]">Mean squared prob error</span>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-[#EAE7F2]">
              <span className="text-xs text-[#77748C]">+3h Workload Switch Rate</span>
              <h4 className="text-2xl font-bold text-pink-700 mt-1">{metrics.research_metrics.counterfactual_switch_rate}</h4>
              <span className="text-[10px] text-[#77748C]">Counterfactual sensitivity</span>
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-violet-50/50 border border-violet-100 text-xs text-[#77748C] leading-relaxed flex items-start gap-2">
            <Info className="w-4 h-4 text-[#8B7CF6] flex-shrink-0 mt-0.5" />
            <span>
              <strong>Methodology Note:</strong> PR-AUC should be interpreted relative to positive class prevalence (~2.27%).
              Because the allocation engine first applies hard eligibility filtering, eligible-only ranking evaluates specifically within viable candidate pools.
            </span>
          </div>
        </div>
      )}

      {/* Charts: Feature Importance and Calibration Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CatBoost Feature Importance Chart */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">CatBoost Feature Importances</h3>
              <p className="text-xs text-[#77748C]">Top predictive features learned by the tree ensemble</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#F3F0FF] text-[#8B7CF6] font-semibold">
              Top 10 Features
            </span>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={metrics?.feature_importances?.slice(0, 10) || []}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 70, bottom: 10 }}
              >
                <XAxis type="number" tick={{ fontSize: 10, fill: '#77748C' }} />
                <YAxis dataKey="feature" type="category" tick={{ fontSize: 10, fill: '#29263D' }} />
                <Tooltip />
                <Bar dataKey="importance" fill="#8B7CF6" radius={[0, 6, 6, 0]} name="Importance" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Held-Out Calibration Curve */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Held-Out Probability Calibration</h3>
              <p className="text-xs text-[#77748C]">Quantile bins: Predicted probability vs Observed frequency</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#D9F3E4] text-emerald-800 font-semibold">
              Reliability Curve
            </span>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics?.calibration_curve || []} margin={{ top: 10, right: 30, left: -10, bottom: 20 }}>
                <XAxis dataKey="predicted_probability" tick={{ fontSize: 10, fill: '#77748C' }} name="Predicted Probability" />
                <YAxis tick={{ fontSize: 10, fill: '#77748C' }} domain={[0, 1]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="observed_frequency" stroke="#8B7CF6" strokeWidth={2.5} name="FairGig Ensemble" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
