"use client";
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area, CartesianGrid } from 'recharts';
import { LayoutDashboard, Database, FileText, CheckCircle, TrendingUp, Filter, Activity } from 'lucide-react';

export default function NexusUniversalApp() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'bi' | 'notebook'>('bi');
  const [mounted, setMounted] = useState(false);

  // Fixes the Hydration/Chart width errors
  useEffect(() => {
    setMounted(true);
  }, []);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    setData(null); setLoading(true);
    const fd = new FormData();
    fd.append("file", e.target.files[0]);
    try {
      const res = await fetch("http://localhost:8000/analyze", { method: "POST", body: fd });
      const result = await res.json();
      setData(result);
    } catch (err) { alert("Backend Error"); }
    setLoading(false);
  };

  if (!mounted) return <div className="min-h-screen bg-[#05070a]" />;

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-400 p-4 font-sans">
      {/* HEADER BAR */}
      <nav className="bg-[#111620] border border-white/10 p-4 rounded-xl mb-6 flex justify-between items-center shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="bg-blue-600 p-2 rounded shadow-lg shadow-blue-500/20"><Activity className="text-white" size={18}/></div>
          <h1 className="text-white font-black text-xs tracking-widest uppercase italic">Nexus_Universal_Kernel</h1>
        </div>
        <div className="flex gap-4">
          {data && (
            <div className="flex bg-black/40 p-1 rounded-lg border border-white/5">
                <button onClick={() => setView('bi')} className={`px-5 py-2 rounded-md text-[10px] font-black transition-all ${view === 'bi' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-white'}`}>ENTERPRISE_BI</button>
                <button onClick={() => setView('notebook')} className={`px-5 py-2 rounded-md text-[10px] font-black transition-all ${view === 'notebook' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-white'}`}>17_STEP_NOTEBOOK</button>
            </div>
          )}
          <label className="bg-white text-black px-6 py-2 rounded-md cursor-pointer font-black text-[10px] hover:bg-blue-600 hover:text-white transition-all uppercase flex items-center gap-2">
            <Database size={14}/> {loading ? "Computing..." : "Import Dataset"}
            <input type="file" className="hidden" onChange={onUpload} />
          </label>
        </div>
      </nav>

      {data ? (
        <div className="animate-in fade-in zoom-in-95 duration-500 max-w-[1600px] mx-auto">
          {view === 'bi' ? (
            <div className="grid grid-cols-12 gap-5">
              {/* SLICERS */}
              <div className="col-span-12 flex gap-4 bg-[#111620] p-4 rounded-xl border border-white/5 shadow-xl">
                <div className="flex items-center gap-2 text-blue-500 font-black text-[10px] uppercase border-r border-white/10 pr-4"><Filter size={14}/> Slicers</div>
                {data.db.filters && Object.keys(data.db.filters).map(f => (
                  <select key={f} className="bg-black/40 border border-white/10 rounded px-3 py-1 text-[10px] text-slate-300 outline-none focus:ring-1 ring-blue-500">
                    <option>{f} (All)</option>
                    {data.db.filters[f].map((opt:any) => <option key={opt}>{opt}</option>)}
                  </select>
                ))}
              </div>

              {/* KPI CARDS */}
              <div className="col-span-12 grid grid-cols-5 gap-4">
                {data.db.kpis.map((k:any, i:number) => (
                  <div key={i} className="bg-[#111620] border-l-4 border-blue-500 p-5 rounded-lg shadow-xl">
                    <p className="text-[9px] uppercase font-bold text-slate-500 mb-1">{k.l}</p>
                    <div className="flex justify-between items-end">
                      <h2 className="text-2xl font-black text-white italic">{k.v}</h2>
                      <TrendingUp size={14} className="text-emerald-500 opacity-50 mb-1"/>
                    </div>
                  </div>
                ))}
              </div>

              {/* STRATEGY & CHARTS */}
              <div className="col-span-12 lg:col-span-3 bg-[#1a212e] rounded-xl border border-white/5 p-6 shadow-2xl h-fit">
                <h3 className="text-blue-500 text-[10px] font-black uppercase mb-6 tracking-[0.2em] underline underline-offset-8">Strategic Roadmap</h3>
                <div className="space-y-8">
                  {data.db.strategy.map((s:any, idx:number) => (
                    <div key={idx} className="group">
                      {/* FIXED: Changed <p> to <div> to allow internal <div> bullets */}
                      <div className="text-white text-[11px] font-black mb-2 flex items-center gap-2 italic uppercase">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full shrink-0"/> {s.t}
                      </div>
                      <p className="text-[10px] text-slate-400 leading-relaxed pl-4">{s.d}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="col-span-12 lg:col-span-9 grid grid-cols-2 gap-5">
                <div className="bg-[#111620] p-6 rounded-xl border border-white/5 min-h-[320px]">
                  <p className="text-white text-[10px] font-black mb-6 uppercase border-l-2 border-blue-500 pl-3 italic">Impact Influence (Hover for Data)</p>
                  <div className="h-[240px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.db.importance} layout="vertical">
                        <XAxis type="number" hide />
                        <YAxis dataKey="name" type="category" stroke="#475569" fontSize={9} width={80} />
                        <Tooltip 
                           cursor={{fill: 'rgba(255,255,255,0.05)'}}
                           contentStyle={{backgroundColor: '#111620', border: '1px solid rgba(255,255,255,0.1)', fontSize: '10px'}}
                        />
                        <Bar dataKey="val" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="bg-[#111620] p-6 rounded-xl border border-white/5 min-h-[320px]">
                   <p className="text-white text-[10px] font-black mb-6 uppercase border-l-2 border-blue-500 pl-3 italic">Lead Density Trend</p>
                   <div className="h-[240px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={Array.from({length: 12}).map((_, i) => ({name: i, y: Math.floor(Math.random()*100)}))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                        <XAxis dataKey="name" hide />
                        <YAxis stroke="#475569" fontSize={9} />
                        <Tooltip contentStyle={{backgroundColor: '#111620', border: '1px solid rgba(255,255,255,0.1)', fontSize: '10px'}} />
                        <Area type="monotone" dataKey="y" stroke="#3b82f6" fill="#3b82f611" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* DATA PREVIEW TABLE */}
                <div className="col-span-2 bg-[#111620] p-6 rounded-xl border border-white/5 overflow-hidden">
                  <p className="text-white text-[10px] font-black mb-4 uppercase italic">Cleaned Dataset Sample</p>
                  <div className="overflow-x-auto max-h-[150px] text-[9px]">
                    <table className="w-full text-left">
                      <thead className="text-blue-500 border-b border-white/10 sticky top-0 bg-[#111620]">
                        <tr>{Object.keys(data.db.raw[0]).map(k => <th key={k} className="p-2 uppercase">{k}</th>)}</tr>
                      </thead>
                      <tbody className="text-slate-500">
                        {data.db.raw.map((r:any, i:number) => (
                          <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            {Object.values(r).map((v:any, j) => <td key={j} className="p-2">{String(v)}</td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* --- 17-STEP NOTEBOOK VIEW (UNCHANGED BUT PROTECTED) --- */
            <div className="max-w-4xl mx-auto space-y-12 pb-20">
               {data.steps.map((s: any) => (
                 <div key={s.id} className="relative border-l-2 border-white/5 pl-8 ml-4">
                   <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-blue-600 shadow-lg shadow-blue-500/50" />
                   <div className="flex justify-between items-center mb-4">
                     <span className="text-blue-500 font-black text-[9px] uppercase tracking-widest">{s.pct}% SYNCED</span>
                     <code className="text-slate-600 text-[9px] bg-black/40 px-2 py-1 rounded">CMD: {s.cmd}</code>
                   </div>
                   <div className="bg-[#111620] border border-white/5 p-8 rounded-2xl shadow-2xl">
                     <h4 className="text-white font-black text-xs mb-6 flex items-center gap-3 italic uppercase">
                        <CheckCircle size={14} className="text-emerald-500"/> STEP_{s.id}: {s.title}
                     </h4>
                     {s.out && <div className="text-[10px] overflow-auto max-h-[500px] notebook-table mb-6" dangerouslySetInnerHTML={{__html: s.out}} />}
                     {s.img && (
                       <div className="mt-6 p-4 bg-black/40 rounded-xl border border-white/5">
                         <p className="text-[9px] font-bold text-slate-600 uppercase mb-4 italic tracking-widest">Graphical_Node_Output:</p>
                         <img src={`data:image/png;base64,${s.img}`} className="w-full rounded-lg shadow-2xl" alt="Analysis Plot" />
                       </div>
                     )}
                   </div>
                 </div>
               ))}
            </div>
          )}
        </div>
      ) : (
        <div className="h-[75vh] flex flex-col items-center justify-center opacity-10">
          <Database size={100} className="mb-4 animate-pulse text-white"/>
          <h2 className="text-5xl font-black italic tracking-tighter text-white uppercase underline decoration-blue-600 underline-offset-8">Awaiting_Uplink</h2>
        </div>
      )}

      <style jsx global>{`
        .notebook-table table { width: 100%; border-collapse: collapse; }
        .notebook-table th { text-align: left; padding: 12px; border-bottom: 2px solid #ffffff10; color: #fff; font-size: 10px; text-transform: uppercase; }
        .notebook-table td { padding: 12px; border-bottom: 1px solid #ffffff05; color: #64748b; font-size: 10px; }
      `}</style>
    </div>
  );
}