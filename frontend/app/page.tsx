"use client";
import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Database, Activity, CheckCircle, Loader2, Award, BarChart3, TrendingUp } from 'lucide-react';

export default function ProGenericBIDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'bi' | 'notebook'>('bi');
  const [error, setError] = useState<string | null>(null);

  const BACKEND_URL = "https://terrific-emotion-production.up.railway.app";

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setData(null);
    setError(null);
    setLoading(true);

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/analyze`, { 
        method: "POST", 
        body: fd 
      });

      const result = await res.json();

      if (result.error) {
        setError(result.message || "Analysis failed");
      } else {
        setData(result);
      }
    } catch (err: any) {
      setError("Cannot connect to backend. Please check if Railway service is running.");
    } finally {
      setLoading(false);
    }
  };

  const trendData = React.useMemo(() => Array.from({ length: 12 }, (_, i) => ({
    month: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i],
    value1: 4200 + Math.random() * 7800,
    value2: 650 + Math.random() * 2600,
  })), []);

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-300 p-6 font-sans">
      <div className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-5">
          <div className="bg-gradient-to-br from-blue-600 to-violet-600 p-4 rounded-2xl">
            <Activity className="text-white" size={32} />
          </div>
          <div>
            <h1 className="text-4xl font-black text-white tracking-tighter">Intelligence Dashboard</h1>
            <p className="text-slate-500">Universal BI • Any Dataset</p>
          </div>
        </div>

        <label className="bg-white hover:bg-blue-600 hover:text-white text-black px-8 py-4 rounded-2xl cursor-pointer font-semibold flex items-center gap-3 transition-all shadow-2xl">
          <Database size={22} />
          {loading ? "ANALYZING..." : "UPLOAD ANY CSV"}
          <input type="file" className="hidden" accept=".csv" onChange={onUpload} />
        </label>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-32">
          <Loader2 className="animate-spin text-blue-500 mb-6" size={64} />
          <p className="text-2xl font-semibold text-white">Analyzing Dataset...</p>
        </div>
      )}

      {error && (
        <div className="max-w-2xl mx-auto bg-red-950/80 border border-red-600 p-10 rounded-3xl">
          <p className="font-bold text-red-400 text-xl mb-3">Analysis Failed</p>
          <pre className="text-red-300 text-sm whitespace-pre-wrap">{error}</pre>
        </div>
      )}

      {data ? (
        <div className="max-w-[1900px] mx-auto space-y-10">
          <div className="flex justify-center">
            <div className="bg-[#111620] border border-white/10 rounded-full p-1.5 flex shadow-inner">
              <button 
                onClick={() => setView('bi')} 
                className={`px-12 py-3.5 rounded-full text-sm font-semibold transition-all ${view === 'bi' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                BI DASHBOARD
              </button>
              <button 
                onClick={() => setView('notebook')} 
                className={`px-12 py-3.5 rounded-full text-sm font-semibold transition-all ${view === 'notebook' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                17-STEP NOTEBOOK
              </button>
            </div>
          </div>

          {view === 'bi' ? (
            <div className="space-y-10">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                {data.db?.kpis?.map((k: any, i: number) => (
                  <div key={i} className="bg-[#111620] border border-white/10 p-6 rounded-3xl min-h-[130px] flex flex-col justify-between">
                    <p className="text-xs uppercase tracking-widest text-slate-500 line-clamp-2">{k.l}</p>
                    <p className="text-4xl font-black text-white mt-3 tracking-tighter break-words">{k.v}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-12 gap-8">
                <div className="col-span-12 lg:col-span-3">
                  <div className="bg-[#111620] border border-white/10 p-7 rounded-3xl sticky top-8">
                    <h3 className="text-white font-bold text-xl mb-6 flex items-center gap-3">
                      <Award size={24} /> Key Insights
                    </h3>
                    {(data.db?.strategy || []).map((s: any, i: number) => (
                      <div key={i} className="mb-8 p-5 bg-black/40 rounded-2xl">
                        <p className="font-semibold text-blue-400 line-clamp-2">{s.t}</p>
                        <p className="text-sm text-slate-400 mt-3 leading-relaxed line-clamp-4">{s.d}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="col-span-12 lg:col-span-9 space-y-8">
                  <div className="bg-[#111620] p-7 rounded-3xl border border-white/10">
                    <h3 className="text-white font-bold text-lg mb-5 flex items-center gap-3">
                      <BarChart3 size={24} /> Top Feature Importance
                    </h3>
                    <div className="h-[420px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data.db?.importance || []} layout="vertical">
                          <XAxis type="number" />
                          <YAxis dataKey="name" type="category" width={180} />
                          <Tooltip />
                          <Bar dataKey="val" fill="#6366f1" radius={[0, 8, 8, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-[#111620] p-7 rounded-3xl border border-white/10">
                    <h3 className="text-white font-bold text-lg mb-5 flex items-center gap-3">
                      <TrendingUp size={24} /> Performance Trend
                    </h3>
                    <div className="h-[420px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={trendData}>
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip />
                          <Area type="natural" dataKey="value1" stroke="#6366f1" fill="#6366f120" strokeWidth={4} />
                          <Area type="natural" dataKey="value2" stroke="#f472b6" fill="#f472b620" strokeWidth={4} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-[#111620] p-7 rounded-3xl border border-white/10">
                    <h3 className="text-white font-bold text-lg mb-5">Processed Data Sample</h3>
                    <div className="overflow-x-auto max-h-[460px] border border-white/10 rounded-2xl bg-[#0a0c14]">
                      <table className="w-full text-sm">
                        <thead className="bg-[#0f121a] sticky top-0 z-10">
                          <tr>
                            {Object.keys(data.db?.processed?.[0] || {}).map((k) => (
                              <th key={k} className="p-4 text-left text-indigo-400 font-medium whitespace-nowrap">{k}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/10">
                          {(data.db?.processed || []).map((row: any, idx: number) => (
                            <tr key={idx} className="hover:bg-white/5">
                              {Object.values(row).map((val: any, i: number) => (
                                <td key={i} className="p-4 text-slate-300 whitespace-nowrap">{String(val)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-5xl mx-auto space-y-12 pb-20">
              {data.steps?.map((s: any, index: number) => (
                <div key={`step-${s.id}-${index}`} className="relative border-l-2 border-white/10 pl-10">
                  <div className="absolute -left-2 top-3 w-5 h-5 rounded-full bg-blue-600 ring-4 ring-[#05070a]" />
                  <div className="flex justify-between mb-4">
                    <span className="text-blue-500 font-black text-xs tracking-widest">{s.pct}% COMPLETE</span>
                    <code className="bg-black/50 px-3 py-1 rounded text-slate-500 text-xs">{s.cmd}</code>
                  </div>
                  <div className="bg-[#111620] border border-white/5 p-9 rounded-3xl">
                    <h4 className="text-white font-black text-sm mb-6 flex items-center gap-3">
                      <CheckCircle size={18} className="text-emerald-500" /> 
                      STEP {s.id} — {s.title}
                    </h4>
                    {s.out && <div className="notebook-table mb-8 text-[10px]" dangerouslySetInnerHTML={{ __html: s.out }} />}
                    {s.img && (
                      <div className="bg-black/60 p-4 rounded-2xl border border-white/5">
                        <img src={`data:image/png;base64,${s.img}`} className="w-full rounded-xl shadow-2xl" alt={`Step ${s.id}`} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : !loading && (
        <div className="h-[80vh] flex flex-col items-center justify-center text-center">
          <Database size={140} className="mb-10 text-slate-700" />
          <h2 className="text-6xl font-black text-white tracking-tighter">Upload Any Dataset</h2>
          <p className="text-xl text-slate-500 mt-6 max-w-lg">Get instant professional BI dashboard</p>
        </div>
      )}

      <style jsx global>{`
        .notebook-table table { width: 100%; border-collapse: collapse; }
        .notebook-table th, .notebook-table td { padding: 12px 16px; border-bottom: 1px solid #ffffff10; }
        .notebook-table th { background: #111620; color: #60a5fa; text-transform: uppercase; font-size: 10px; }
      `}</style>
    </div>
  );
}
