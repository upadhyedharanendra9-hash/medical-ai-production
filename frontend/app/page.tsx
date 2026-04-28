"use client";
import React, { useState } from 'react';
import { Database, Activity, AlertCircle, Loader2, Download, Terminal, CheckCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// --- REPLACE THIS WITH YOUR RENDER URL ---
const RENDER_URL = "https://your-backend-on-render.onrender.com";

export default function NexusDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const downloadDebug = () => {
    const blob = new Blob([logs.join('\n') + `\n\nError: ${error}`], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = "nexus_debug.txt";
    link.click();
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setData(null);
    setLogs(["[SYSTEM] Initializing node..."]);

    const fd = new FormData();
    fd.append("file", file);

    try {
      addLog(`Connecting to ${RENDER_URL}...`);
      // Note: Render spins down on free tier, this might take 30s to wake up
      const res = await fetch(`${RENDER_URL}/analyze`, { method: "POST", body: fd });
      
      if (!res.ok) throw new Error(`Server responded with ${res.status}`);

      const result = await res.json();
      if (result.logs) setLogs(result.logs);

      if (result.error) {
        setError(result.message);
      } else {
        setData(result);
        addLog("Data successfully synchronized.");
      }
    } catch (err: any) {
      addLog(`FATAL: ${err.message}`);
      setError("Connection Refused. Render may be waking up or URL is wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030508] text-slate-400 p-6 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center mb-10 bg-[#0a0c14] p-6 rounded-3xl border border-white/5 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="bg-blue-600 p-3 rounded-xl shadow-lg shadow-blue-500/20"><Activity className="text-white" /></div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tight italic">NEXUS_KERNEL</h1>
            <p className="text-[10px] font-mono text-blue-500 uppercase tracking-widest">Status: {loading ? 'Computing' : 'Ready'}</p>
          </div>
        </div>
        <label className="bg-white text-black px-6 py-3 rounded-xl font-bold text-sm cursor-pointer hover:bg-blue-600 hover:text-white transition-all flex items-center gap-2">
          <Database size={16} /> {loading ? "PROCESSING..." : "UPLOAD DATASET"}
          <input type="file" className="hidden" accept=".csv" onChange={onUpload} />
        </label>
      </div>

      {/* Error State */}
      {error && (
        <div className="max-w-4xl mx-auto mb-10 bg-red-950/20 border border-red-500/30 p-8 rounded-3xl">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-red-500 font-bold flex items-center gap-2"><AlertCircle /> KERNEL PANIC</h3>
              <p className="text-xs text-red-400/60 mt-1">{error}</p>
            </div>
            <button onClick={downloadDebug} className="text-xs bg-red-600 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2">
                <Download size={14}/> DEBUG REPORT
            </button>
          </div>
        </div>
      )}

      {/* Main UI */}
      {data && !error ? (
        <div className="space-y-6">
          <div className="grid grid-cols-4 gap-4">
            {data.db.kpis.map((k:any, i:number) => (
              <div key={i} className="bg-[#0a0c14] p-6 rounded-2xl border border-white/5">
                <p className="text-[10px] font-bold text-slate-600 uppercase">{k.l}</p>
                <p className="text-2xl font-black text-white">{k.v}</p>
              </div>
            ))}
          </div>
          
          <div className="bg-[#0a0c14] p-8 rounded-3xl border border-white/5">
            <h3 className="text-white font-bold mb-6">Top Influence Drivers</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.db.importance} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" width={100} tick={{fontSize: 10, fill: '#64748b'}} />
                  <Tooltip cursor={{fill: 'transparent'}} contentStyle={{backgroundColor: '#0a0c14', border: 'none', borderRadius: '8px'}} />
                  <Bar dataKey="val" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : loading ? (
        <div className="py-20 text-center flex flex-col items-center">
          <Loader2 className="animate-spin text-blue-600 mb-4" size={48} />
          <p className="text-white font-bold animate-pulse">Establishing Render Handshake...</p>
          <p className="text-[10px] text-slate-600 mt-2 italic">Note: Free tier servers take ~30s to wake up on first run.</p>
        </div>
      ) : (
        <div className="py-32 text-center opacity-40">
           <Database size={64} className="mx-auto mb-4" />
           <p className="text-sm font-medium italic">Awaiting secure CSV link...</p>
        </div>
      )}

      {/* System Console */}
      <div className="mt-12">
        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-700 mb-3 tracking-tighter">
            <Terminal size={12} /> SESSION_LOGS_STDOUT
        </div>
        <div className="bg-black/80 rounded-2xl p-6 h-48 overflow-y-auto font-mono text-[11px] text-blue-400/80 border border-white/5 shadow-inner">
          {logs.map((log, i) => <div key={i} className="mb-1">{log}</div>)}
          {loading && <div className="text-white animate-pulse">_</div>}
        </div>
      </div>
    </div>
  );
}
