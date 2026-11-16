import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  ShieldCheck,
  BrainCircuit,
  Database,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Key,
  Cpu
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [lambdaDefault, setLambdaDefault] = useState<number>(0.08);
  const [appMode, setAppMode] = useState<string>('Research & Demonstration');
  const [defaultPolicy, setDefaultPolicy] = useState<string>('WAFR');
  const [savedNotice, setSavedNotice] = useState<boolean>(false);

  // LLM and Explainable AI settings
  const [ollamaUrl, setOllamaUrl] = useState<string>(() => {
    const savedUrl = localStorage.getItem('fairgig_ollama_url') || '';
    return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(?:\/|$)/i.test(savedUrl) ? '' : savedUrl;
  });
  const [llmProvider, setLlmProvider] = useState<string>(() => localStorage.getItem('fairgig_llm_provider') || 'auto');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('fairgig_ollama_url', ollamaUrl);
    localStorage.setItem('fairgig_llm_provider', llmProvider);
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl pb-16">
      {/* Banner */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-[#29263D]">Platform & Algorithm Settings</h2>
          <p className="text-xs text-[#77748C] mt-1">
            Configure default optimization parameters, verify model integrity, and inspect data store status.
          </p>
        </div>
        {savedNotice && (
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Preferences Saved</span>
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* General Settings */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-sm text-[#29263D] flex items-center gap-2">
            <SettingsIcon className="w-4 h-4 text-[#8B7CF6]" /> General Configuration
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-medium text-[#29263D] mb-1">Application Environment</label>
              <select
                value={appMode}
                onChange={(e) => setAppMode(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
              >
                <option value="Research & Demonstration">Research & Demonstration</option>
                <option value="Production Simulation">Production Simulation</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-[#29263D] mb-1">Default Allocation Policy</label>
              <select
                value={defaultPolicy}
                onChange={(e) => setDefaultPolicy(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
              >
                <option value="WAFR">WAFR (Workload-Aware Fair Ranking)</option>
                <option value="ML-Only">ML-Only (Pure Success Probability)</option>
                <option value="Nearest Eligible">Nearest Eligible (Operational Distance)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Fairness Settings */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-sm text-[#29263D] flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[#8B7CF6]" /> Fairness Parameter Tuning
          </h3>

          <div className="text-xs space-y-3">
            <div>
              <label className="block font-medium text-[#29263D] mb-1">Default Fairness Coefficient (λ)</label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  step="0.01"
                  min="0.0"
                  max="0.5"
                  value={lambdaDefault}
                  onChange={(e) => setLambdaDefault(parseFloat(e.target.value) || 0.08)}
                  className="w-28 p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] font-mono font-bold text-[#8B7CF6]"
                />
                <span className="text-[#77748C]">
                  Determines the relative weight assigned to worker opportunity credit and workload pressure.
                </span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] text-[11px] text-[#77748C]">
              <strong className="text-[#29263D] block mb-1">WAFR Scoring Formulation:</strong>
              <code>Score = 0.70 × P(succ) + 0.30 × Eff + λ × Opp_Credit - λ × Workload_Pressure</code>
            </div>
          </div>
        </div>

        {/* Model & Artifact Integrity */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-sm text-[#29263D] flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-[#8B7CF6]" /> ML Model Artifacts & Integrity
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-[#FAF9FE] rounded-2xl border border-[#EAE7F2]">
              <span className="text-[10px] uppercase font-bold text-[#77748C] block">Ensemble Setup</span>
              <strong className="text-[#29263D]">HistGradientBoosting (0.5) + CatBoost (0.5)</strong>
            </div>
            <div className="p-3 bg-[#FAF9FE] rounded-2xl border border-[#EAE7F2]">
              <span className="text-[10px] uppercase font-bold text-[#77748C] block">Expected Features</span>
              <strong className="text-[#8B7CF6]">27 Features (25 numeric, 2 categorical)</strong>
            </div>
            <div className="p-3 bg-[#FAF9FE] rounded-2xl border border-[#EAE7F2]">
              <span className="text-[10px] uppercase font-bold text-[#77748C] block">Classification Threshold</span>
              <strong className="text-[#29263D]">0.155 (Validation Tuned)</strong>
            </div>
            <div className="p-3 bg-[#FAF9FE] rounded-2xl border border-[#EAE7F2]">
              <span className="text-[10px] uppercase font-bold text-[#77748C] block">Artifacts Location</span>
              <strong className="text-[#29263D] font-mono text-[11px]">models/cat_model.joblib</strong>
            </div>
          </div>
        </div>

        {/* Explainable AI & LLM Provider Configuration */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-sm text-[#29263D] flex items-center gap-2">
            <Key className="w-4 h-4 text-[#8B7CF6]" /> Explainable AI (XAI) & Prompt Engineering Setup
          </h3>

          <div className="text-xs space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-medium text-[#29263D] mb-1">Default Reasoning Provider</label>
                <select
                  value={llmProvider}
                  onChange={(e) => setLlmProvider(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                >
                  <option value="auto">Auto (Detects Best Gemini Model or Offline CoT)</option>
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash (Recommended)</option>
                  <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                  <option value="gemini-1.5-flash-latest">Gemini 1.5 Flash Latest</option>
                  <option value="gemini-pro">Gemini Pro</option>
                  <option value="ollama">Ollama (Remote Endpoint)</option>
                  <option value="heuristic">FairGig Prompt-Engineered CoT (Zero-Shot Rule Engine)</option>
                </select>
              </div>

              <div>
                <p className="rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] p-3 text-[#77748C]">
                  Gemini credentials are configured server-side with the <code>GEMINI_API_KEY</code> environment variable. They are never stored in this browser.
                </p>
              </div>
            </div>

            <div>
              <label className="block font-medium text-[#29263D] mb-1">Reachable Ollama API Endpoint</label>
              <input
                type="text"
                placeholder="https://your-ollama-endpoint.example"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
              />
            </div>
          </div>
        </div>

        {/* Database Status */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-sm text-[#29263D] flex items-center gap-2">
            <Database className="w-4 h-4 text-[#8B7CF6]" /> Database & Seed Data Source
          </h3>

          <div className="text-xs text-[#77748C] space-y-2">
            <p>
              Persistent database connection configured server-side with <code>DATABASE_URL</code>. Demo data is initialized from:
            </p>
            <ul className="list-disc list-inside space-y-1 text-[#29263D]">
              <li><strong>1,000 workers</strong> from <code>data/workers.csv</code></li>
              <li><strong>3,000 tasks</strong> from <code>data/tasks.csv</code></li>
              <li><strong>Confirmed allocations</strong> stored independently in local database table</li>
            </ul>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="px-6 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all"
          >
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
};
