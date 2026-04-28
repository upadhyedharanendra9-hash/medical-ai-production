"use client";
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Database, Activity, CheckCircle, AlertCircle, Loader2, Target, TrendingUp, BarChart3, Award, Terminal, Download } from 'lucide-react';

const COLORS = ['#6366f1', '#22d3ee', '#f472b6', '#4ade80', '#fb923c', '#a78bfa'];

export default function ProGenericBIDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'bi' | 'notebook'>('bi');
  const [error, setError] = useState<string | null>(null);
  const [systemLogs, setSystemLogs] = useState<string[]>([]);

  // Helper to add timestamped logs
  const addLog = (msg: string) => {
    const ts = new Date().toLocaleTimeString();
    setSystemLogs(prev => [...prev, `[${ts}] ${msg}`]);
  };

  // Function to download the log file for the developer (you)
  const downloadDebugLog = () => {
    const logContent = `SYSTEM DEBUG REPORT\n====================\nError: ${error || "None"}\n\nConsole Output:\n${systemLogs.join('\n')}\n\nRaw Response:\n${JSON.stringify(data, null, 2)}`;
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `nexus_debug_${Date.now()}.txt`;
    link.click();
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setData(null);
    setError(null);
    setLoading(true);
    setSystemLogs([]); // Reset logs for new session
    
    addLog(`Initiating upload: ${file.name}`);
    addLog(`File size: ${(file.size / 1024).toFixed(2)} KB`);

    const fd = new FormData();
    fd.append("file", file);

    try {
      addLog("Sending POST request to http://localhost:8000/analyze...");
      const res = await fetch("http://localhost:8000/analyze", { 
        method: "POST", 
        body: fd 
      });

      if (!res.ok) {
        throw new Error(`HTTP Error! Status: ${res.status}`);
      }

      const result = await res.json();
      addLog("Response received from Kernel.");

      if (result.logs) {
        setSystemLogs(prev => [...prev, ...result.logs]);
      }

      if (result.error) {
        addLog(`Backend Error: ${result.message}`);
        setError(result.message || "Analysis failed");
      } else {
        addLog("Data successfully synchronized with UI.");
        setData(result);
      }
    } catch (err: any) {
      const errMsg = "Connection Refused: Backend is likely offline or Port 8000 is blocked.";
      addLog(`FATAL ERROR: ${err.message}`);
      setError(errMsg);
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
      {/* Header */}
      <div className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-5">
          <div className="bg-gradient-to-br from-blue-600 to-violet-600 p-4 rounded-2xl shadow-lg shadow-blue-500/20">
            <Activity className="text-white" size={32} />
          </div>
          <div>
            <h1 className="text-4xl font-black text-white tracking-tighter">Nexus Kernel v3</h1>
            <p className="text-slate-500 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Universal AI Engine Active
            </p>
          </div>
        </div>

        <div className="flex gap-4">
            {error && (
               <button 
               onClick={downloadDebugLog}
               className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 px-6 py-4 rounded-2xl font-bold flex items-center gap-2 transition-all"
             >
               <Download size={18} /> DOWNLOAD ERROR LOG
             </button>
            )}
            <label className="bg-white hover:bg-blue-600 hover:text-white text-black px-8 py-4 rounded-2xl cursor-pointer font-semibold flex items-center gap-3 transition-all shadow-2xl">
                <Database size={22} />
                {loading ? "PROCESSING..." : "UPLOAD DATASET"}
                <input type="file" className="hidden" accept=".csv" onChange={onUpload} />
            </label>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="animate-spin text-blue-500 mb-6" size={64} />
          <p className="text-2xl font-semibold text-white">Kernel Node Computing...</p>
          <div className="w-full max-w-2xl mt-10 bg-black/50 border border-white/5 rounded-xl p-4 font-mono text-[10px] text-blue-400/70">
              {systemLogs.slice(-3).map((log, i) => (
                  <div key={i}>{log}</div>
              ))}
          </div>
        </div>
      )}

      {error && (
        <div className="max-w-3xl mx-auto bg-red-950/20 border border-red-600/30 p-10 rounded-3xl mb-10">
          <div className="flex items-center gap-4 text-red-500 mb-4">
              <AlertCircle size={32} />
              <h2 className="text-2xl font-bold">Kernel Panic Detected</h2>
          </div>
          <p className="text-red-300 text-sm font-mono bg-black/40 p-4 rounded-xl border border-red-500/10 mb-6">{error}</p>
          <p className="text-slate-500 text-xs uppercase tracking-widest mb-4">Internal Trace History:</p>
          <div className="bg-black/60 rounded-xl p-6 h-48 overflow-y-auto font-mono text-[10px] text-slate-500 border border-white/5">
              {systemLogs.map((log, i) => <div key={i} className="mb-1">{log}</div>)}
          </div>
        </div>
      )}

      {data ? (
        <div className="max-w-[1900px] mx-auto space-y-10">
          {/* Toggle */}
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
                18-STEP NOTEBOOK
              </button>
            </div>
          </div>

          {view === 'bi' ? (
            <div className="space-y-10">
              {/* KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                {data.db?.kpis?.map((k: any, i: number) => (
                  <div key={i} className="bg-[#111620] border border-white/10 p-6 rounded-3xl min-h-[140px] flex flex-col justify-between">
                    <p className="text-xs uppercase tracking-widest text-slate-500 line-clamp-1">{k.l}</p>
                    <p className="text-4xl font-black text-white mt-3 tracking-tighter break-words">{k.v}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-12 gap-8">
                {/* Insights Sidebar */}
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

                {/* Main Content */}
                <div className="col-span-12 lg:col-span-9 space-y-8">
                  {/* Feature Importance */}
                  <div className="bg-[#111620] p-7 rounded-3xl border border-white/10">
                    <h3 className="text-white font-bold text-lg mb-5 flex items-center gap-3">
                      <BarChart3 size={24} /> Top Feature Importance
                    </h3>
                    <div className="h-[420px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data.db?.importance || []} layout="vertical">
                          <XAxis type="number" stroke="#475569" />
                          <YAxis dataKey="name" type="category" width={180} stroke="#475569" />
                          <Tooltip contentStyle={{backgroundColor: '#111620', borderColor: '#334155'}} />
                          <Bar dataKey="val" fill="#6366f1" radius={[0, 8, 8, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Trend Analysis */}
                  <div className="bg-[#111620] p-7 rounded-3xl border border-white/10">
                    <h3 className="text-white font-bold text-lg mb-5 flex items-center gap-3">
                      <TrendingUp size={24} /> Performance Trend
                    </h3>
                    <div className="h-[420px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={trendData}>
                          <XAxis dataKey="month" stroke="#475569" />
                          <YAxis stroke="#475569" />
                          <Tooltip contentStyle={{backgroundColor: '#111620', borderColor: '#334155'}} />
                          <Area type="natural" dataKey="value1" stroke="#6366f1" fill="#6366f120" strokeWidth={4} />
                          <Area type="natural" dataKey="value2" stroke="#f472b6" fill="#f472b620" strokeWidth={4} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* 18-Step Notebook */
            <div className="max-w-5xl mx-auto space-y-12 pb-20">
              {data.steps?.map((s: any, index: number) => (
                <div key={`step-${s.id}-${index}`} className="relative border-l-2 border-white/10 pl-10">
                  <div className="absolute -left-2 top-3 w-5 h-5 rounded-full bg-blue-600 ring-4 ring-[#05070a]" />
                  <div className="flex justify-between mb-4">
                    <span className="text-blue-500 font-black text-xs tracking-widest">{s.pct}% COMPLETE</span>
                    <code className="bg-black/50 px-3 py-1 rounded text-slate-500 text-[10px]">{s.cmd}</code>
                  </div>
                  <div className="bg-[#111620] border border-white/5 p-9 rounded-3xl">
                    <h4 className="text-white font-black text-sm mb-6 flex items-center gap-3">
                      <CheckCircle size={18} className="text-emerald-500" /> 
                      STEP {s.id} — {s.title}
                    </h4>
                    {s.out && <div className="notebook-table mb-8 text-[10px] overflow-x-auto" dangerouslySetInnerHTML={{ __html: s.out }} />}
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
      ) : !loading && !error && (
        <div className="h-[60vh] flex flex-col items-center justify-center text-center">
          <Database size={100} className="mb-10 text-slate-800" />
          <h2 className="text-5xl font-black text-white tracking-tighter">System Idle</h2>
          <p className="text-xl text-slate-500 mt-6 max-w-lg">Kernel Node ready for dataset processing. Connection established on Port 8000.</p>
        </div>
      )}

      {/* Persistence Log Footer */}
      <div className="mt-20 pt-10 border-t border-white/5">
          <div className="flex items-center gap-2 text-slate-600 text-[10px] font-bold uppercase mb-4 tracking-widest">
              <Terminal size={14} /> System Node Logs
          </div>
          <div className="bg-black/40 border border-white/5 rounded-2xl p-6 h-40 overflow-y-auto font-mono text-[10px] text-slate-500">
              {systemLogs.length > 0 ? (
                  systemLogs.map((log, i) => <div key={i} className="mb-1">{log}</div>)
              ) : (
                  <div className="italic text-slate-700">Waiting for kernel activity...</div>
              )}
          </div>
      </div>

      <style jsx global>{`
        .notebook-table table { width: 100%; border-collapse: collapse; background: #0a0c14; border-radius: 12px; overflow: hidden; }
        .notebook-table th, .notebook-table td { padding: 12px 16px; border-bottom: 1px solid #ffffff10; text-align: left; }
        .notebook-table th { background: #111620; color: #6366f1; text-transform: uppercase; font-size: 9px; }
      `}</style>
    </div>
  );
}
