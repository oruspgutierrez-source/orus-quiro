import { DollarSign, Bot, Headset, ArrowRight, TrendingUp } from 'lucide-react';

const glassCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";
const darkCard  = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

export default function DashboardView() {
  const bars = [
    { h: 30, label: 'Lun', val: 42 },
    { h: 55, label: 'Mar', val: 86 },
    { h: 100, label: 'Mié', val: 142 },
    { h: 80, label: 'Jue', val: 112 },
    { h: 95, label: 'Vie', val: 168 },
    { h: 40, label: 'Sáb', val: 58 },
    { h: 20, label: 'Dom', val: 28 },
  ];

  return (
    <div className="flex-1 p-4 space-y-4 overflow-auto" style={{background: 'radial-gradient(circle at 50% 50%, #ffffff 0%, #fafafa 40%, #f0f0f0 75%, #e9e9e9 100%)'}}>

      {/* Page Header */}
      <div className="flex justify-between items-end relative z-10">
        <div>
          <h3 className="text-2xl font-bold text-slate-800">Buenos días, Admin</h3>
          <p className="text-slate-500 mt-1 font-medium">Aquí tienes el último vistazo de las operaciones de Orus.</p>
        </div>
        <div className="text-slate-500 text-sm flex items-center gap-2 bg-white/80 border border-slate-200 px-4 py-2 rounded-xl shadow-sm backdrop-blur-sm font-medium">
          Oct 24, 2023
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
        <MetricCard
          icon={<DollarSign size={22} />}
          title="Ingresos Totales (30d)"
          value="$124,500"
          badge="+12.5%"
          badgeColor="emerald"
          accentColor="from-emerald-500/20 to-emerald-900/10"
          glowColor="rgba(16,185,129,0.15)"
          borderAccent="border-emerald-500/20"
        />
        <MetricCard
          icon={<Bot size={22} />}
          title="Tasa de Éxito del Bot"
          value="85.2%"
          badge="85%"
          badgeColor="amber"
          accentColor="from-amber-500/20 to-amber-900/10"
          glowColor="rgba(245,158,11,0.15)"
          borderAccent="border-amber-500/20"
        />
        <MetricCard
          icon={<Headset size={22} />}
          title="Intervenciones Humanas"
          value="14 / día prom."
          badge="3 Pendientes"
          badgeColor="red"
          accentColor="from-red-500/20 to-red-900/10"
          glowColor="rgba(239,68,68,0.15)"
          borderAccent="border-red-500/20"
        />
      </div>

      {/* Main Data Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
        {/* Chart Card */}
        <div className={`lg:col-span-2 ${darkCard} p-6 flex flex-col`}>
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.02] to-transparent pointer-events-none" />
          <div className="flex justify-between items-center mb-6 relative z-10">
            <h4 className="text-lg font-bold text-zinc-100 tracking-wide">Actividad de Usuarios Esta Semana</h4>
            <button className="text-emerald-400 text-sm font-semibold hover:text-emerald-300 flex items-center gap-1 transition-colors">
              Ver Informe <ArrowRight size={15} />
            </button>
          </div>
          {/* Bar Chart */}
          <div className="flex-1 min-h-[220px] flex items-end gap-3 relative z-10 pt-4">
            {bars.map((b, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                <div
                  className={`w-full rounded-t-lg transition-all relative ${i === 2 ? 'bg-gradient-to-t from-emerald-600 to-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.4)]' : 'bg-gradient-to-t from-zinc-700 to-zinc-600 group-hover:from-emerald-800 group-hover:to-emerald-600'}`}
                  style={{ height: `${b.h}%` }}
                >
                  {/* Tooltip */}
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-zinc-800 text-zinc-100 text-xs px-2 py-1 rounded-md border border-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-lg">
                    {b.val} activos
                  </div>
                  {/* Top shimmer */}
                  <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
                </div>
                <span className="text-xs text-zinc-500 font-medium">{b.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Handovers Card */}
        <div className={`${glassCard} flex flex-col`}>
          <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none" />
          <div className="p-4 border-b border-slate-700/50 flex justify-between items-center relative z-10 bg-gradient-to-b from-white/5 to-transparent">
            <h4 className="font-bold text-slate-100 tracking-wide">Handovers de Clientes</h4>
            <span className="bg-red-500/20 text-red-300 text-xs px-2 py-0.5 rounded-full font-semibold border border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.2)]">
              3 Req. Acción
            </span>
          </div>
          <div className="flex-1 p-2 space-y-1 relative z-10 overflow-y-auto no-scrollbar">
            {[
              { name: 'Sarah Jenkins', issue: 'Error de Facturación', time: '2m', urgent: true },
              { name: 'Marcus Chen', issue: 'Soporte Técnico', time: '15m', urgent: true },
              { name: 'Emily Davis', issue: 'Consulta de Producto', time: '3h', urgent: false },
            ].map((item, i) => (
              <div key={i} className={`p-3 rounded-xl cursor-pointer flex items-center gap-3 border transition-all ${item.urgent ? 'border-red-500/20 bg-red-500/5 hover:bg-red-500/10' : 'border-transparent hover:bg-white/5 hover:border-white/10'}`}>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 border border-slate-600/50 shrink-0 shadow-inner flex items-center justify-center">
                  <span className="text-slate-300 text-xs font-bold">{item.name[0]}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-200 truncate">{item.name}</p>
                  <p className="text-xs text-slate-500 truncate">{item.issue}</p>
                </div>
                <div className="text-xs text-slate-500 whitespace-nowrap">{item.time}</div>
              </div>
            ))}
          </div>
          <div className="p-3 border-t border-slate-800 relative z-10">
            <button className="w-full py-2 text-sm font-semibold text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 rounded-xl border border-slate-700/50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
              Ver Todos los Handovers
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, title, value, badge, badgeColor, accentColor, glowColor, borderAccent }) {
  const badgeStyles = {
    emerald: 'text-emerald-300 bg-emerald-500/20 border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.2)]',
    amber:   'text-amber-300 bg-amber-500/20 border-amber-500/30 shadow-[0_0_8px_rgba(245,158,11,0.2)]',
    red:     'text-red-300 bg-red-500/20 border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.2)]',
  };
  const iconStyles = {
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    amber:   'text-amber-400 bg-amber-500/10 border-amber-500/20',
    red:     'text-red-400 bg-red-500/10 border-red-500/20',
  };

  return (
    <div className={`${glassCard} ${borderAccent} p-6 flex flex-col`}>
      {/* Radial glow behind card */}
      <div className={`absolute -right-8 -top-8 w-32 h-32 rounded-full blur-2xl bg-gradient-to-br ${accentColor} pointer-events-none`} />
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.015] to-transparent pointer-events-none" />

      <div className="flex justify-between items-start mb-5 relative z-10">
        <div className={`p-3 rounded-xl border ${iconStyles[badgeColor]} shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]`}>
          {icon}
        </div>
        <span className={`text-xs font-bold px-3 py-1.5 rounded-full border ${badgeStyles[badgeColor]}`}>
          {badge}
        </span>
      </div>

      <h4 className="text-sm font-medium text-slate-400 mb-2 relative z-10 tracking-wide uppercase">{title}</h4>
      <div className="text-3xl font-black text-slate-100 relative z-10 tracking-tight"
           style={{ textShadow: `0 0 20px ${glowColor}` }}>
        {value}
      </div>
      {/* Bottom shimmer */}
      <div className="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </div>
  );
}
