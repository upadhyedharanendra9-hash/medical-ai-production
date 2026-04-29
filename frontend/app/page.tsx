"use client";
import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Database, Activity, CheckCircle, Loader2, Award, BarChart3, TrendingUp, Download, Heart, ShoppingCart, Users, Briefcase } from 'lucide-react';

export default function ProGenericBIDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'bi' | 'notebook'>('bi');
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const BACKEND_URL = "https://terrific-emotion-production.up.railway.app";

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${timestamp}] ${message}`]);
    console.log(`[LOG] ${message}`);
  };

  const downloadLogs = () => {
    const logText = logs.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-logs-${new Date().toISOString().slice(0,19)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadCleanedData = () => {
    if (!data?.db?.cleaned_csv) return;
    const blob = new Blob([data.db.cleaned_csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cleaned_dataset.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addLog("Cleaned dataset downloaded");
  };

  const getBusinessTheme = (type: string = 'general') => {
    const themes: Record<string, any> = {
      retail: {
        color: '#f59e0b',
        icon: ShoppingCart,
        title: 'Retail Sales Intelligence',
        accent: 'amber'
      },
      healthcare: {
        color: '#ef4444',
        icon: Heart,
        title: 'Healthcare Analytics Dashboard',
        accent: 'rose'
      },
      saas: {
        color: '#3b82f6',
        icon: Users,
        title: 'SaaS Performance Dashboard',
        accent: 'blue'
      },
      ecommerce: {
        color: '#8b5cf6',
        icon: ShoppingCart,
        title: 'E-commerce Intelligence',
        accent: 'violet'
      },
      general: {
        color: '#6366f1',
        icon: Briefcase,
        title: 'Business Intelligence Dashboard',
        accent: 'indigo'
      }
    };

    const lowerType = type.toLowerCase();
    return themes[lowerType] || themes.general;
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setData(null);
    setError(null);
    setLogs([]);
    setLoading(true);

    addLog(`Starting analysis for: ${file.name}`);

    const fd = new FormData();
    fd.append("file", file);

    try {
      addLog(`Sending request to: ${BACKEND_URL}/analyze`);
      const res = await fetch(`${BACKEND_URL}/analyze`, { method: "POST", body: fd });
      addLog(`Response status: ${res.status}`);

      const result = await res.json();
      addLog("Response parsed successfully");

      if (result.error) {
        setError(result.message || "Analysis failed");
        addLog(`Backend Error: ${result.message}`);
      } else {
        setData(result);
        addLog(`Analysis completed. Business Type: ${result.db?.business_type || 'general'}`);
      }
    } catch (err: any) {
      setError(`Connection failed: ${err.message}`);
      addLog(`Frontend Connection Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const theme = data?.db?.business_type ? getBusinessTheme(data.db.business_type) : getBusinessTheme();

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-300 p-6 font-sans">
      {/* Dynamic Header */}
      <div className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-5">
          <div className={`p-4 rounded-2xl bg-gradient-to-br from-[${theme.color}] to-violet-600`}>
            <theme.icon className="text-white" size={34} />
          </div>
          <div>
            <h1 className="text-4xl font-black text-white tracking-tighter">{theme.title}</h1>
            <p className="text-slate-500">Dynamic Business Intelligence • Powered by Nexus</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button onClick={downloadLogs} className="bg-white/10 hover:bg-white/20 px-6 py-3 rounded-2xl flex items-center gap-2 transition-all">
            <Download size={20} /> Logs
          </button>
          {data && (
            <button onClick={downloadCleanedData} className="bg-emerald-600 hover:bg-emerald-700 px-6 py-3 rounded-2xl flex items-center gap-2 font-medium">
              <Download size={20} /> Download Cleaned Data
            </button>
          )}
          <label className="bg-white hover:bg-blue-600 hover:text-white text-black px-8 py-4 rounded-2xl cursor-pointer font-semibold flex items-center gap-3 transition-all shadow-2xl">
            <Database size={22} />
            {loading ? "ANALYZING..." : "UPLOAD CSV"}
            <input type="file" className="hidden" accept=".csv" onChange={onUpload} />
          </label>
        </div>
      </div>

      {/* Live Logs */}
      {logs.length > 0 && (
        <div className="mb-8 bg-black/70 border border-white/10 p-5 rounded-3xl max-h-80 overflow-auto font-mono text-xs">
          <p className="text-blue-400 font-bold mb-2">LIVE ANALYSIS LOGS</p>
          {logs.map((log, i) => <div key={i} className="mb-1 break-all">{log}</div>)}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-32">
          <Loader2 className="animate-spin text-blue-500 mb-6" size={64} />
          <p className="text-2xl font-semibold text-white">Analyzing your dataset...</p>
        </div>
      )}

      {error && (
        <div className="max-w-3xl mx-auto bg-red-950/80 border border-red-600 p-10 rounded-3xl">
          <p className="font-bold text-red-400 text-xl mb-3">Analysis Failed</p>
          <pre className="text-red-300 whitespace-pre-wrap">{error}</pre>
        </div>
      )}

      {data && (
        <div className="max-w-[1900px] mx-auto space-y-10">
          <div className="flex justify-center">
            <div className="bg-[#111620] border border-white/10 rounded-full p-1.5 flex shadow-inner">
              <button 
                onClick={() => setView('bi')} 
                className={`px-14 py-3.5 rounded-full font-semibold transition-all ${view === 'bi' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                BI DASHBOARD
              </button>
              <button 
                onClick={() => setView('notebook')} 
                className={`px-14 py-3.5 rounded-full font-semibold transition-all ${view === 'notebook' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
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
                    <p className="text-xs uppercase tracking-widest text-slate-500">{k.l}</p>
                    <p className="text-4xl font-black text-white mt-3 tracking-tighter">{k.v}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-12 gap-8">
                <div className="col-span-12 lg:col-span-3">
                  <div className="bg-[#111620] border border-white/10 p-7 rounded-3xl sticky top-8">
                    <h3 className="text-white font-bold text-xl mb-6 flex items-center gap-3">
                      <Award size={24} /> Key Business Insights
                    </h3>
                    {(data.db?.strategy || []).map((s: any, i: number) => (
                      <div key={i} className="mb-8 p-5 bg-black/40 rounded-2xl">
                        <p className="font-semibold text-blue-400">{s.t}</p>
                        <p className="text-sm text-slate-400 mt-3 leading-relaxed">{s.d}</p>
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
                          <Bar dataKey="val" fill={theme.color} radius={[0, 8, 8, 0]} />
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
                        <AreaChart data={Array.from({ length: 12 }, (_, i) => ({ 
                          month: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i], 
                          value: 4000 + Math.random()*7000 
                        }))}>
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip />
                          <Area type="natural" dataKey="value" stroke={theme.color} fill={`${theme.color}30`} strokeWidth={4} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-[#111620] p-7 rounded-3xl border border-white/10">
                    <div className="flex justify-between items-center mb-5">
                      <h3 className="text-white font-bold text-lg">Processed Data Sample</h3>
                      <button 
                        onClick={downloadCleanedData} 
                        className="bg-emerald-600 hover:bg-emerald-700 px-6 py-2.5 rounded-xl text-sm flex items-center gap-2"
                      >
                        <Download size={18} /> Download Full CSV
                      </button>
                    </div>
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
                    {s.out && <div className="notebook-table mb-8 text-[11px]" dangerouslySetInnerHTML={{ __html: s.out }} />}
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
      )}

      {!data && !loading && (
        <div className="h-[80vh] flex flex-col items-center justify-center text-center">
          <Database size={140} className="mb-10 text-slate-700" />
          <h2 className="text-6xl font-black text-white tracking-tighter">Upload Any Dataset</h2>
          <p className="text-xl text-slate-500 mt-6 max-w-lg">Get dynamic business intelligence dashboard</p>
        </div>
      )}
    </div>
  );
}
