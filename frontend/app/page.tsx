"use client";
import React, { useState } from 'react';
import { HeartPulse, Database, Terminal, Loader2, AlertCircle, CheckCircle2, Cpu, ChevronRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// --- PRODUCTION URL ---
const BASE_URL = "https://medical-ai-production-jjxr.onrender.com";

export default function MedicalDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true); setError(null); setData(null);
    setLogs([`[${new Date().toLocaleTimeString()}] Handshaking with Production Node...`]);

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch(`${BASE_URL}/analyze`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`Node Connection Error: ${res.status}`);
      const result = await res.json();
      if (result.logs) setLogs(prev => [...prev, ...result.logs]);
      if (result.error) setError(result.message);
      else setData(result);
    } catch (err: any) {
      setError("CONNECTION FAILED: Render node is waking up. Try again in 20 seconds.");
      setLogs(prev => [...prev, `[FATAL] ${err.message}`]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020306] text-slate-400 p-8 font-sans">
      {/* Header */}
      <div className="max-w-7xl mx-auto flex justify-between items-center mb-8 bg-[#0a0c14] p-6 rounded-3xl border border-white/5">
        <div className="flex items-center gap-4">
          <div className="bg-red-600 p-3 rounded-2xl shadow-lg shadow-red-500/20"><HeartPulse className="text-white" /></div>
          <div>
            <h1 className="text-xl font-black text-white italic tracking-tighter">MEDICAL_AI.PROD</h1>
            <p className="text-[10px] font-mono text-red-500 uppercase tracking-widest">{loading ? 'Computing Pipeline' : 'Node Active'}</p>
          </div>
        </div>
        <label className="bg-white text-black px-8 py-4 rounded-2xl font-bold text-sm cursor-pointer hover:bg-red-600 hover:text-white transition-all shadow-xl">
          {loading ? "PROCESSING..." : "INGEST PATIENT DATA"}
          <input type="file" className="hidden" accept=".csv" onChange={onUpload} disabled={loading} />
        </label>
      </div>

      {error && (
        <div className="max-w-7xl mx-auto mb-6 p-6 bg-red-950/20 border border-red-500/20 rounded-2xl flex items-center gap-4 text-red-500 text-xs">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      <div className="max-w-7xl mx-auto grid grid-cols-12 gap-8">
        {/* Left Column: Metrics & Timeline */}
        <div className="col-span-12 lg:col-span-8 space-y-8">
          {data ? (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-3 gap-4">
                {data.db.kpis.map((k:any, i:number) => (
                  <div key={i} className="bg-[#0a0c14] p-6 rounded-2xl border border-white/5">
                    <p className="text-[10px] font-bold text-slate-600 uppercase mb-1 tracking-widest">{k.l}</p>
                    <p className="text-3xl font-black text-white tracking-tighter">{k.v}</p>
                  </div>
                ))}
              </div>

              {/* 18-Step Timeline */}
              <div className="bg-[#0a0c14] p-8 rounded-3xl border border-white/5">
                <h3 className="text-white font-bold mb-6 text-sm flex items-center gap-2 underline underline-offset-8 decoration-red-500/50">18-STEP KERNEL EXECUTION</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {data.steps.map((step:any) => (
                    <div key={step.id} className="bg-black/40 p-4 rounded-xl border border-white/5 flex items-start gap-3">
                      <div className="text-[10px] font-mono text-red-500 mt-1">#{step.id.toString().padStart(2, '0')}</div>
                      <div className="flex-1">
                        <p className="text-white font-bold text-xs">{step.title}</p>
                        <p className="text-[10px] text-slate-500 font-mono mt-1 opacity-70 italic">{step.cmd}</p>
                        {step.out && <p className="text-[10px] text-blue-400 mt-2 bg-blue-500/5 p-1 rounded inline-block">{step.out}</p>}
                        {step.img && (
                          <div className="mt-4 border border-white/5 rounded-lg overflow-hidden grayscale hover:grayscale-0 transition-all">
                             <img src={`data:image/png;base64,${step.img}`} className="w-full" />
                          </div>
                        )}
                      </div>
                      <CheckCircle2 size={14} className="text-green-500 shrink-0" />
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : loading ? (
            <div className="h-[500px] flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5">
              <Loader2 className="animate-spin text-red-600 mb-4" size={48} />
              <p className="text-white font-bold animate-pulse tracking-widest text-sm uppercase">Stabilizing Handshake</p>
              <p className="text-[10px] text-slate-600 mt-2 font-mono italic text-center px-10">Initializing 18-step medical inference. First run on Render Cloud takes ~40s.</p>
            </div>
          ) : (
            <div className="h-[500px] flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5 opacity-20">
              <Database size={64} className="mb-4" />
              <p className="italic text-sm font-medium tracking-[0.2em] uppercase">Awaiting Clinical Dataset</p>
            </div>
          )}
        </div>

        {/* Right Column: Console & Insights */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
          <div className="bg-black/80 rounded-3xl p-6 h-[600px] flex flex-col border border-white/5 shadow-2xl">
            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-700 mb-8 tracking-[0.3em] uppercase">
              <Terminal size={14} /> Clinical_Logs
            </div>
            <div className="flex-1 overflow-y-auto font-mono text-[11px] text-blue-500/80 space-y-4">
              {logs.map((log, i) => <div key={i} className="border-l border-red-900/30 pl-4 py-1">{log}</div>)}
              {loading && <div className="text-white animate-pulse pl-4 italic">Executing_Medical_Weights...</div>}
            </div>
          </div>

          {data && (
            <div className="bg-[#0a0c14] p-6 rounded-3xl border border-white/5">
              <h3 className="text-white font-bold mb-6 text-sm flex items-center gap-2"><Cpu size={14}/> Top Feature Drivers</h3>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.db.importance} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" width={80} tick={{fontSize: 10, fill: '#475569'}} />
                    <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{backgroundColor: '#0a0c14', border: 'none'}} />
                    <Bar dataKey="val" fill="#ef4444" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
