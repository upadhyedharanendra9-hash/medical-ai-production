"use client";
import React, { useState } from 'react';
import { Database, Activity, AlertCircle, Loader2, Terminal, CheckCircle, Download } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// --- PASTE YOUR RENDER URL HERE (e.g., https://my-app.onrender.com) ---
const BASE_URL = "https://your-app-name.onrender.com";

export default function NexusDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (m: string) => setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${m}`]);

  const downloadReport = () => {
    const report = `SYSTEM LOGS\n${'='.repeat(20)}\n${logs.join('\n')}\n\nError: ${error || 'None'}`;
    const blob = new Blob([report], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = "nexus_debug_report.txt";
    link.click();
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setData(null);
    setLogs([`[SYSTEM] Connecting to Node: ${BASE_URL}`]);

    const fd = new FormData();
    fd.append("file", file);

    try {
      addLog("Transmitting data packets...");
      const res = await fetch(`${BASE_URL}/analyze`, { 
        method: "POST", 
        body: fd 
      });

      if (!res.ok) throw new Error(`Handshake Failed (Status: ${res.status})`);

      const result = await res.json();
      if (result.logs) setLogs(prev => [...prev, ...result.logs]);

      if (result.error) {
        setError(result.message);
      } else {
        setData(result);
        addLog("Synchronization Complete.");
      }
    } catch (err: any) {
      setError("CONNECTION REFUSED: The backend server is either offline or still waking up.");
      addLog(`FATAL: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020408] text-slate-400 p-8 font-sans">
      {/* Header Panel */}
      <div className="max-w-6xl mx-auto flex justify-between items-center mb-10 bg-[#0a0c14] p-6 rounded-3xl border border-white/5 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="bg-blue-600 p-3 rounded-2xl"><Activity className="text-white" /></div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tighter italic">NEXUS_KERNEL</h1>
            <p className="text-[10px] font-mono text-blue-500 uppercase tracking-widest">{loading ? 'COMPUTING...' : 'ONLINE'}</p>
          </div>
        </div>
        <label className="bg-white text-black px-8 py-4 rounded-2xl font-bold text-sm cursor-pointer hover:bg-blue-600 hover:text-white transition-all shadow-xl">
          {loading ? "PROCESSING..." : "INGEST DATASET"}
          <input type="file" className="hidden" accept=".csv" onChange={onUpload} disabled={loading} />
        </label>
      </div>

      {/* Error UI */}
      {error && (
        <div className="max-w-4xl mx-auto mb-10 bg-red-950/20 border border-red-500/20 p-8 rounded-3xl flex justify-between items-center">
          <div>
            <h3 className="text-red-500 font-bold flex items-center gap-2"><AlertCircle size={18} /> KERNEL PANIC</h3>
            <p className="text-xs text-red-400/60 mt-1">{error}</p>
          </div>
          <button onClick={downloadReport} className="bg-red-600 text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2">
            <Download size={14}/> DOWNLOAD LOGS
          </button>
        </div>
      )}

      {/* Main Dashboard Layout */}
      <div className="max-w-6xl mx-auto grid grid-cols-12 gap-8">
        {/* Left Side: Visuals */}
        <div className="col-span-12 lg:col-span-8 space-y-8">
          {data ? (
            <>
              <div className="grid grid-cols-3 gap-4">
                {data.db.kpis.map((k:any, i:number) => (
                  <div key={i} className="bg-[#0a0c14] p-6 rounded-2xl border border-white/5">
                    <p className="text-[10px] font-bold text-slate-600 uppercase mb-2">{k.l}</p>
                    <p className="text-3xl font-black text-white">{k.v}</p>
                  </div>
                ))}
              </div>
              <div className="bg-[#0a0c14] p-8 rounded-3xl border border-white/5">
                <h3 className="text-white font-bold mb-6 text-sm">Feature Importance Analysis</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.db.importance} layout="vertical">
                      <XAxis type="number" hide />
                      <YAxis dataKey="name" type="category" width={100} tick={{fontSize: 10, fill: '#475569'}} />
                      <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{backgroundColor: '#0a0c14', border: 'none'}} />
                      <Bar dataKey="val" fill="#2563eb" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              {data.steps.map((s:any) => s.img && (
                <div key={s.id} className="bg-[#0a0c14] p-4 rounded-3xl border border-white/5 overflow-hidden">
                   <img src={`data:image/png;base64,${s.img}`} className="w-full rounded-xl" />
                </div>
              ))}
            </>
          ) : loading ? (
            <div className="h-[400px] flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5">
              <Loader2 className="animate-spin text-blue-600 mb-4" size={48} />
              <p className="text-white font-bold">Node Handshake in Progress</p>
              <p className="text-[10px] text-slate-600 mt-2">Free servers take up to 45s to wake up on first run.</p>
            </div>
          ) : (
            <div className="h-[400px] flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5 opacity-20">
              <Database size={64} className="mb-4" />
              <p className="italic text-sm">Awaiting secure CSV link...</p>
            </div>
          )}
        </div>

        {/* Right Side: Real-time Terminal */}
        <div className="col-span-12 lg:col-span-4">
          <div className="bg-black/50 p-6 rounded-3xl border border-white/5 h-[600px] flex flex-col sticky top-8">
            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-700 mb-6 tracking-widest uppercase">
              <Terminal size={14} /> LIVE_KERNEL_STDOUT
            </div>
            <div className="flex-1 overflow-y-auto font-mono text-[11px] text-blue-400/70 space-y-2">
              {logs.map((log, i) => (
                <div key={i} className="border-l-2 border-blue-600/20 pl-4 py-1">{log}</div>
              ))}
              {loading && <div className="animate-pulse text-white pl-4">_</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
