import { useState, useEffect } from 'react';
import { Filter, ChevronLeft, ChevronRight, Loader2, Bot, Copy, Check, CheckCircle } from 'lucide-react';
import { supabase } from '../supabaseClient';

const glassCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";
const darkCard  = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

const severityConfig = {
  ERROR:   { pill: 'text-red-300 bg-red-500/20 border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.25)]',   dot: 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.7)]' },
  WARNING: { pill: 'text-amber-300 bg-amber-500/20 border-amber-500/30 shadow-[0_0_8px_rgba(245,158,11,0.25)]', dot: 'bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.7)]' },
  INFO:    { pill: 'text-emerald-300 bg-emerald-500/20 border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.25)]', dot: 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.7)]' },
};

export default function SystemLogsView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [severityFilter, setSeverityFilter] = useState('Todas las Severidades');
  
  // States for the AI Analysis and UX actions
  const [analyzingLogIds, setAnalyzingLogIds] = useState(new Set());
  const [deletingLogIds, setDeletingLogIds] = useState(new Set());
  const [aiAnalysis, setAiAnalysis] = useState({});
  const [copiedLogId, setCopiedLogId] = useState(null);

  const limit = 50;

  useEffect(() => {
    async function fetchLogs() {
      setLoading(true);
      try {
        const startIdx = (page - 1) * limit;
        const endIdx = startIdx + limit - 1;

        let query = supabase.from('orus_logs').select('*', { count: 'exact' });
        
        if (severityFilter !== 'Todas las Severidades') {
          query = query.eq('severity', severityFilter.toUpperCase());
        }
        
        const { data, error, count } = await query
          .order('created_at', { ascending: false })
          .range(startIdx, endIdx);

        if (!error && data) {
          setLogs(data);
          setTotalCount(count || 0);
        } else if (error) {
          console.error("Supabase Error:", error);
        }
      } catch (err) {
        console.error("Javascript Error fetching logs:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchLogs();
  }, [page, severityFilter]);

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedLogId(id);
    setTimeout(() => setCopiedLogId(null), 2000);
  };

  const handleResolve = async (id) => {
    setDeletingLogIds(prev => {
      const newSet = new Set(prev);
      newSet.add(id);
      return newSet;
    });

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
      
      const response = await fetch(`${API_URL}/api/logs/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        // Optimistically remove from state
        setLogs(prevLogs => prevLogs.filter(log => log.id !== id));
        setTotalCount(prevCount => Math.max(0, prevCount - 1));
      } else {
        const data = await response.json();
        alert("Error al resolver: " + (data.detail || "Error desconocido"));
      }
    } catch (err) {
      console.error(err);
      alert("Error de conexión al resolver el log.");
    } finally {
      setDeletingLogIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleAnalyze = async (log) => {
    if (aiAnalysis[log.id]) return;
    
    setAnalyzingLogIds(prev => {
      const newSet = new Set(prev);
      newSet.add(log.id);
      return newSet;
    });

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
      const API_KEY = import.meta.env.VITE_API_KEY || 'OrusDashboardAdmin2026';
      
      const response = await fetch(`${API_URL}/api/logs/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY
        },
        body: JSON.stringify({
          error_message: log.error_message || "Error desconocido",
          stack_trace: log.stack_trace || "Sin stack trace"
        })
      });
      
      const data = await response.json();
      if (response.ok) {
        setAiAnalysis(prev => ({ ...prev, [log.id]: data.analysis }));
      } else {
        alert("Error al analizar: " + (data.detail || "Error desconocido"));
      }
    } catch (err) {
      console.error(err);
      alert("Error de conexión al solicitar análisis de IA.");
    } finally {
      setAnalyzingLogIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(log.id);
        return newSet;
      });
    }
  };

  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="flex-1 flex flex-col p-4 gap-4 bg-white overflow-auto">

      {/* Header / Filters Panel */}
      <div className={`${glassCard} p-5 flex justify-between items-center relative z-10`}>
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.02] to-transparent pointer-events-none" />
        <div className="relative z-10">
          <h2 className="text-xl font-bold text-slate-100 tracking-wide">Operaciones y Alertas</h2>
          <p className="text-sm text-slate-400 mt-1 font-medium">Monitorea fallos, analízalos y dales por concluidos para mantener tu tablero limpio.</p>
        </div>
        <div className="flex gap-3 relative z-10">
          <select 
            value={severityFilter}
            onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
            className="bg-slate-800/80 border border-slate-700/80 text-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] cursor-pointer"
          >
            <option>Todas las Severidades</option>
            <option>Error</option>
            <option>Warning</option>
            <option>Info</option>
          </select>
        </div>
      </div>

      {/* Data Table Card */}
      <div className={`${darkCard} flex-1 flex flex-col relative z-10`}>
        <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none rounded-2xl" />
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        <div className="overflow-x-auto flex-1 relative z-10">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-zinc-700/50 bg-gradient-to-b from-white/5 to-transparent">
                <th className="p-4 text-xs font-bold text-zinc-400 uppercase tracking-widest w-48">Marca de Tiempo</th>
                <th className="p-4 text-xs font-bold text-zinc-400 uppercase tracking-widest w-32">Severidad</th>
                <th className="p-4 text-xs font-bold text-zinc-400 uppercase tracking-widest w-48">Origen</th>
                <th className="p-4 text-xs font-bold text-zinc-400 uppercase tracking-widest">Mensaje de Evento</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" className="p-8 text-center text-zinc-500">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-500" />
                    Cargando registros...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="4" className="p-8 text-center text-zinc-500 font-medium">Todos los sistemas operativos. No hay alertas pendientes.</td>
                </tr>
              ) : (
                logs.map((log) => {
                  const cfg = severityConfig[log.severity] || severityConfig['INFO'];
                  const isDeleting = deletingLogIds.has(log.id);
                  
                  return (
                    <tr key={log.id} className={`border-b border-zinc-800/50 hover:bg-white/[0.03] transition-all group ${isDeleting ? 'opacity-50 pointer-events-none' : ''}`}>
                      <td className="p-4 text-zinc-500 text-sm font-mono whitespace-nowrap align-top">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="p-4 align-top">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full border ${cfg.pill}`}>
                          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                          {log.severity}
                        </span>
                      </td>
                      <td className="p-4 text-zinc-400 text-xs font-medium align-top">
                        {log.event_type || 'SYSTEM_EVENT'}
                      </td>
                      <td className="p-4 text-zinc-400 group-hover:text-zinc-300 text-sm transition-colors break-words max-w-2xl align-top">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="font-semibold text-zinc-200 mb-1">{log.error_message || "Log del Sistema"}</div>
                            {log.stack_trace && (
                              <div className="text-xs font-mono text-zinc-500 bg-black/30 p-2 rounded border border-white/5 mt-2 overflow-x-auto whitespace-pre-wrap">
                                {log.stack_trace}
                              </div>
                            )}
                            
                            {/* AI Analysis Block */}
                            {aiAnalysis[log.id] && (
                              <div className="mt-3 p-3 rounded-lg bg-zinc-900/80 border border-zinc-700/50 text-zinc-300 text-xs leading-relaxed shadow-inner">
                                <div className="flex items-center gap-2 mb-1 text-emerald-400/80 font-medium">
                                  <Bot size={14} /> Análisis del Ingeniero IA
                                </div>
                                <div className="whitespace-pre-wrap">{aiAnalysis[log.id]}</div>
                              </div>
                            )}
                          </div>
                          
                          {/* Actions (Visible on Hover) */}
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                            {log.severity === 'ERROR' && !aiAnalysis[log.id] && (
                              <button
                                onClick={() => handleAnalyze(log)}
                                disabled={analyzingLogIds.has(log.id)}
                                className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-400 hover:text-white transition-all disabled:opacity-50"
                                title="Analizar con IA"
                              >
                                {analyzingLogIds.has(log.id) ? <Loader2 size={14} className="animate-spin" /> : <Bot size={14} />}
                              </button>
                            )}
                            
                            <button
                              onClick={() => handleCopy(`${log.error_message}\n${log.stack_trace || ''}`, log.id)}
                              className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-400 hover:text-zinc-200 transition-all"
                              title="Copiar Detalles"
                            >
                              {copiedLogId === log.id ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                            </button>
                            
                            {/* Resolve / Concluir Button */}
                            <button
                              onClick={() => handleResolve(log.id)}
                              className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 hover:text-emerald-300 transition-all"
                              title="Marcar como Concluido (Eliminar)"
                            >
                              {isDeleting ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t border-zinc-800 flex items-center justify-between relative z-10 bg-gradient-to-t from-black/20 to-transparent rounded-b-2xl">
          <span className="text-zinc-500 text-xs font-medium">
            Mostrando {logs.length > 0 ? (page - 1) * limit + 1 : 0}-{Math.min(page * limit, totalCount)} de {totalCount} registros
          </span>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 text-zinc-500 hover:text-emerald-400 transition-colors disabled:opacity-30 disabled:hover:text-zinc-500 hover:bg-white/10 rounded-lg"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="text-zinc-400 text-xs font-medium px-3 py-1.5 bg-white/5 rounded-lg border border-zinc-700/50">
              Página {totalPages === 0 ? 0 : page} de {totalPages}
            </span>
            <button 
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 text-zinc-500 hover:text-emerald-400 transition-colors disabled:opacity-30 disabled:hover:text-zinc-500 hover:bg-white/10 rounded-lg"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
