"use client";
import React, { useState } from 'react';
import { Activity, Database, Terminal, Loader2, AlertCircle, HeartPulse, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// --- YOUR VERIFIED PRODUCTION URL ---
const BASE_URL = "https://medical-ai-production-jjxr.onrender.com";

export default function MedicalAIDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setData(null);
    setLogs([`[${new Date().toLocaleTimeString()}] Handshaking with Production Node...`]);

    const fd = new FormData();
    fd.append("file", file);

    try {
      // POST request to your Render analyze endpoint
      const res = await fetch(`${BASE_URL}/analyze`, { 
        method: "POST", 
        body: fd 
      });
      
      if (!res.ok) throw new Error(`Node Connection Error (Status: ${res.status})`);

      const result = await res.json();
      if (result.logs) setLogs(prev => [...prev, ...result.logs]);

      if (result.error) {
        setError(result.message);
      } else {
        setData(result);
        setLogs(prev => [...prev, "[SUCCESS] Clinical analysis finalized."]);
      }
    } catch (err: any) {
      setError("CONNECTION REFUSED: Render node is waking up or URL is blocked. Please try again in 10 seconds.");
      setLogs(prev => [...prev, `[FATAL ERROR] ${err.message}`]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030508] text-slate-400 p-8 font-sans tracking-tight">
      {/* Header */}
      <div className="max-w-6xl mx-auto flex justify-between items-center mb-10 bg-[#0a0c14] p-6 rounded-3xl border border-white/5 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="bg-red-600 p-3 rounded-2xl shadow-lg shadow-red-500/20"><HeartPulse className="text-white" /></div>
          <div>
            <h1 className="text-xl font-black text-white italic tracking-tighter uppercase">Medical_AI.v1</h1>
            <p className="text-[10px] font-mono text-red-500 uppercase tracking-widest">{loading ? 'Computing' : 'Node Ready'}</p>
          </div>
        </div>
        <label className="bg-white text-black px-8 py-4 rounded-2xl font-bold text-sm cursor-pointer hover:bg-red-600 hover:text-white transition-all shadow-xl">
          {loading ? "PROCESSING..." : "INGEST PATIENT CSV"}
          <input type="file" className="hidden" accept=".csv" onChange={onUpload} disabled={loading} />
        </label>
      </div>

      {error && (
        <div className="max-w-6xl mx-auto mb-10 bg-red-950/20 border border-red-500/20 p-8 rounded-3xl flex items-center gap-6 text-red-500">
          <AlertCircle size={32} className="shrink-0" />
          <div className="text-xs">
            <p className="font-bold uppercase tracking-widest">Kernel Error Detected</p>
            <p className="opacity-70 mt-1 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="max-w-6xl mx-auto grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-8 space-y-8">
          {data ? (
            <>
              <div className="grid grid-cols-3 gap-4">
                {data.db.kpis.map((k:any, i:number) => (
                  <div key={i} className="bg-[#0a0c14] p-8 rounded-3xl border border-white/5">
                    <p className="text-[10px] font-bold text-slate-600 uppercase mb-2 tracking-widest">{k.l}</p>
                    <p className="text-3xl font-black text-white tracking-tighter">{k.v}</p>
                  </div>
                ))}
              </div>

              <div className="bg-[#0a0c14] p-8 rounded-3xl border border-white/5">
                <h3 className="text-white font-bold mb-8 text-sm flex items-center gap-2"><BarChart3 size={16}/> Clinical Drivers</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.db.importance} layout="vertical">
                        <XAxis type="number" hide />
                        <YAxis dataKey="name" type="category" width={100} tick={{fontSize: 10, fill: '#475569'}} />
                        <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{backgroundColor: '#0a0c14', border: 'none'}} />
                        <Bar dataKey="val" fill="#ef4444" radius={[0, 4, 4, 0]} />
                    </BarChart>
                    </ResponsiveContainer>
                </div>
              </div>

              {data.img && (
                <div className="bg-[#0a0c14] p-4 rounded-3xl border border-white/5">
                    <img src={`data:image/png;base64,${data.img}`} className="w-full rounded-2xl grayscale hover:grayscale-0 transition-all duration-500" />
                </div>
              )}
            </>
          ) : loading ? (
            <div className="h-[500px] flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5 border-dashed">
              <Loader2 className="animate-spin text-red-600 mb-4" size={48} />
              <p className="text-white font-bold animate-pulse tracking-widest text-sm uppercase">Stabilizing Handshake</p>
              <p className="text-[10px] text-slate-600 mt-2 font-mono italic">Node is currently warming up on Render Cloud...</p>
            </div>
          ) : (
            <div className="h-[500px] flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5 opacity-20 transition-opacity hover:opacity-30">
              <Database size={64} className="mb-4" />
              <p className="italic text-sm font-medium tracking-[0.2em] uppercase">Pending Clinical Data Ingestion</p>
            </div>
          )}
        </div>

        {/* Sidebar Console */}
        <div className="col-span-12 lg:col-span-4">
          <div className="bg-black/90 rounded-3xl p-6 h-[650px] flex flex-col border border-white/5 shadow-2xl sticky top-8">
            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-700 mb-8 tracking-[0.3em] uppercase">
              <Terminal size={14} /> Output_Stream
            </div>
            <div className="flex-1 overflow-y-auto font-mono text-[11px] text-blue-500/80 space-y-4">
              {logs.map((log, i) => (
                <div key={i} className="border-l border-red-500/20 pl-4 py-1 leading-relaxed">{log}</div>
              ))}
              {loading && <div className="text-white animate-pulse pl-4 italic">Processing_Buffer...</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
