"use client";
import React, { useState } from 'react';
import { Activity, Database, Terminal, Loader2, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// --- UPDATE THIS URL ---
const BASE_URL = "https://your-app-name.onrender.com"; 

export default function NexusDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setLogs([`[${new Date().toLocaleTimeString()}] Handshaking with Render Node...`]);

    const fd = new FormData();
    fd.append("file", file);

    try {
      // Connect to the /analyze endpoint
      const res = await fetch(`${BASE_URL}/analyze`, { 
        method: "POST", 
        body: fd 
      });
      
      if (!res.ok) throw new Error(`Server status ${res.status}`);

      const result = await res.json();
      if (result.logs) setLogs(prev => [...prev, ...result.logs]);

      if (result.error) {
        setError(result.message);
      } else {
        setData(result);
      }
    } catch (err: any) {
      setError("CONNECTION ERROR: Render is waking up. Please try again in 30 seconds.");
      setLogs(prev => [...prev, `[FATAL] ${err.message}`]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020408] text-slate-400 p-8 font-sans">
      {/* Header */}
      <div className="max-w-6xl mx-auto flex justify-between items-center mb-10 bg-[#0a0c14] p-6 rounded-3xl border border-white/5">
        <div className="flex items-center gap-4">
          <Activity className="text-blue-500" />
          <h1 className="text-xl font-bold text-white italic">NEXUS_KERNEL</h1>
        </div>
        <label className="bg-white text-black px-6 py-3 rounded-xl font-bold text-sm cursor-pointer hover:bg-blue-600 hover:text-white transition-all">
          {loading ? "PROCESING..." : "UPLOAD CSV"}
          <input type="file" className="hidden" accept=".csv" onChange={onUpload} disabled={loading} />
        </label>
      </div>

      {error && (
        <div className="max-w-4xl mx-auto mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-500 text-xs flex items-center gap-2">
          <AlertCircle size={14}/> {error}
        </div>
      )}

      <div className="max-w-6xl mx-auto grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {data ? (
            <div className="bg-[#0a0c14] p-8 rounded-3xl border border-white/5">
                <div className="grid grid-cols-2 gap-4 mb-8">
                   {data.db.kpis.map((k:any, i:number) => (
                       <div key={i} className="bg-black/40 p-4 rounded-xl">
                           <p className="text-[10px] text-slate-500 uppercase">{k.l}</p>
                           <p className="text-2xl font-bold text-white">{k.v}</p>
                       </div>
                   ))}
                </div>
                {data.steps.map((s:any) => s.img && (
                    <img key={s.id} src={`data:image/png;base64,${s.img}`} className="w-full rounded-xl border border-white/5" />
                ))}
            </div>
          ) : loading ? (
            <div className="h-64 flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5">
              <Loader2 className="animate-spin text-blue-500 mb-2" />
              <p className="text-xs">Waking up cloud node...</p>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center bg-[#0a0c14] rounded-3xl border border-white/5 opacity-20">
              <Database />
              <p className="text-xs mt-2 italic">Waiting for data ingestion...</p>
            </div>
          )}
        </div>

        {/* Console */}
        <div className="col-span-12 lg:col-span-4 bg-black p-6 rounded-3xl border border-white/5 h-[500px] overflow-hidden flex flex-col">
          <div className="flex items-center gap-2 text-[10px] text-slate-600 font-bold mb-4 uppercase"><Terminal size={12}/> Console_Output</div>
          <div className="flex-1 overflow-y-auto font-mono text-[11px] text-blue-400 space-y-2">
            {logs.map((l, i) => <div key={i}>{l}</div>)}
          </div>
        </div>
      </div>
    </div>
  );
}
