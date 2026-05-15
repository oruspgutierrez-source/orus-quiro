import { Filter, ChevronLeft, ChevronRight } from 'lucide-react';

const glassCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";
const darkCard  = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

const logs = [
  { id: 1, time: '2023-10-27 14:32:01', severity: 'ERROR',   module: 'Meta API',         msg: 'Connection timeout establishing stream to graph.facebook.com endpoint.' },
  { id: 2, time: '2023-10-27 14:31:45', severity: 'WARNING', module: 'Supabase',          msg: "High latency detected on query 'get_user_profiles' (>500ms)." },
  { id: 3, time: '2023-10-27 14:30:12', severity: 'INFO',    module: 'Auth Service',      msg: 'User session established successfully for id: user_88291a.' },
  { id: 4, time: '2023-10-27 14:28:55', severity: 'ERROR',   module: 'Payment Gateway',  msg: 'Failed to process webhook payload from Stripe: invalid signature.' },
  { id: 5, time: '2023-10-27 14:25:30', severity: 'INFO',    module: 'Calendar',         msg: "Cron job 'sync_events' completed successfully in 1.2s." },
  { id: 6, time: '2023-10-27 14:20:10', severity: 'WARNING', module: 'Storage Service',  msg: 'Bucket approaching capacity limits (85% utilization).' },
];

const severityConfig = {
  ERROR:   { pill: 'text-red-300 bg-red-500/20 border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.25)]',   dot: 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.7)]' },
  WARNING: { pill: 'text-amber-300 bg-amber-500/20 border-amber-500/30 shadow-[0_0_8px_rgba(245,158,11,0.25)]', dot: 'bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.7)]' },
  INFO:    { pill: 'text-emerald-300 bg-emerald-500/20 border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.25)]', dot: 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.7)]' },
};

export default function SystemLogsView() {
  return (
    <div className="flex-1 flex flex-col p-4 gap-4 bg-white overflow-auto">

      {/* Header / Filters Panel */}
      <div className={`${glassCard} p-5 flex justify-between items-center relative z-10`}>
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.02] to-transparent pointer-events-none" />
        <div className="relative z-10">
          <h2 className="text-xl font-bold text-slate-100 tracking-wide">Registros del Sistema</h2>
          <p className="text-sm text-slate-400 mt-1 font-medium">Monitorea eventos del sistema en tiempo real.</p>
        </div>
        <div className="flex gap-3 relative z-10">
          <select className="bg-slate-800/80 border border-slate-700/80 text-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] cursor-pointer">
            <option>Todas las Severidades</option>
            <option>Error</option>
            <option>Warning</option>
            <option>Info</option>
          </select>
          <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/80 rounded-xl px-4 py-2 cursor-pointer hover:border-emerald-500/50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
            <span className="text-sm text-slate-300 font-medium">Últimas 24 horas</span>
          </div>
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
                <th className="p-4 text-xs font-bold text-zinc-400 uppercase tracking-widest w-36">Severidad</th>
                <th className="p-4 text-xs font-bold text-zinc-400 uppercase tracking-widest w-44">Módulo</th>
                <th className="p-4 text-xs font-bold text-zinc-400 uppercase tracking-widest">Mensaje</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const cfg = severityConfig[log.severity];
                return (
                  <tr key={log.id} className="border-b border-zinc-800/50 hover:bg-white/[0.03] transition-colors group">
                    <td className="p-4 text-zinc-500 text-sm font-mono whitespace-nowrap">{log.time}</td>
                    <td className="p-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full border ${cfg.pill}`}>
                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                        {log.severity}
                      </span>
                    </td>
                    <td className="p-4 font-semibold text-zinc-200 text-sm">{log.module}</td>
                    <td className="p-4 text-zinc-400 group-hover:text-zinc-300 text-sm transition-colors">{log.msg}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t border-zinc-800 flex items-center justify-between relative z-10 bg-gradient-to-t from-black/20 to-transparent rounded-b-2xl">
          <span className="text-zinc-500 text-xs font-medium">Mostrando 1-6 de 1,245 registros</span>
          <div className="flex items-center gap-2">
            <button className="p-1.5 text-zinc-500 hover:text-emerald-400 transition-colors disabled:opacity-30 hover:bg-white/10 rounded-lg" disabled>
              <ChevronLeft size={18} />
            </button>
            <span className="text-zinc-400 text-xs font-medium px-3 py-1.5 bg-white/5 rounded-lg border border-zinc-700/50">Página 1 de 208</span>
            <button className="p-1.5 text-zinc-500 hover:text-emerald-400 transition-colors hover:bg-white/10 rounded-lg">
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
