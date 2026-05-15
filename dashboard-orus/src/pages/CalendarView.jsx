import { ChevronLeft, ChevronRight, Plus, MapPin } from 'lucide-react';

const glassCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";
const darkCard  = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

const days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
const dates = [16, 17, 18, 19, 20, 21, 22];
const todayIdx = 1; // Martes

const events = [
  { col: 0, top: 100, h: 100, title: 'Strategic Alignment', time: '09:30 - 11:00', team: 'Alpha Team', color: 'emerald' },
  { col: 1, top: 466, h: 66,  title: 'Deep Reading',        time: '15:00 - 16:00', team: 'Carlos',     color: 'emerald', featured: true },
  { col: 3, top: 200, h: 133, title: 'Quarterly Review',    time: '11:00 - 13:00', team: 'Exec Team',  color: 'amber' },
  { col: 4, top: 400, h: 100, title: 'System Maintenance',  time: '14:00 - 15:30', team: 'Ops Team',   color: 'slate' },
];

const hours = ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00'];

const colorMap = {
  emerald: { bg: 'bg-emerald-900/40 border-emerald-500/40', bar: 'bg-emerald-400', text: 'text-emerald-300', label: 'text-emerald-400' },
  amber:   { bg: 'bg-amber-900/30 border-amber-500/30',     bar: 'bg-amber-400',   text: 'text-amber-200',   label: 'text-amber-400' },
  slate:   { bg: 'bg-slate-700/40 border-slate-500/30',     bar: 'bg-slate-400',   text: 'text-slate-200',   label: 'text-slate-400' },
};

const upcomingItems = [
  { title: 'Deep Reading',      time: '15:00 - 16:00 (Hoy)',    team: 'Carlos',    color: 'emerald' },
  { title: 'Quarterly Review',  time: 'Mañana, 11:00',          team: 'Exec Team', color: 'amber'   },
  { title: 'System Maintenance',time: 'Vie, 14:00',             team: 'Ops Team',  color: 'slate'   },
];

export default function CalendarView() {
  return (
    <div className="flex-1 flex p-4 gap-4 bg-white overflow-auto">

      {/* Calendar Main Card */}
      <div className={`flex-1 ${glassCard} flex flex-col min-w-0`}>
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.02] to-transparent pointer-events-none" />
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        {/* Controls */}
        <div className="p-4 border-b border-slate-700/50 flex justify-between items-center relative z-10 bg-gradient-to-b from-white/5 to-transparent">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-bold text-slate-100 tracking-wide">Octubre 2023</h2>
            <div className="flex items-center gap-1 bg-slate-800/80 rounded-xl p-1 border border-slate-700/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
              <button className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-white/10 transition-colors"><ChevronLeft size={16} /></button>
              <button className="font-semibold text-sm text-slate-200 px-3 py-1 rounded-lg hover:bg-white/10 transition-colors">Hoy</button>
              <button className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-white/10 transition-colors"><ChevronRight size={16} /></button>
            </div>
          </div>
          <div className="flex bg-slate-800/80 rounded-xl p-1 border border-slate-700/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
            {['Día','Semana','Mes'].map((v, i) => (
              <button key={i} className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors ${i === 1 ? 'bg-slate-700 text-slate-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]' : 'text-slate-500 hover:text-slate-200'}`}>{v}</button>
            ))}
          </div>
        </div>

        {/* Week Header */}
        <div className="grid grid-cols-[60px_1fr_1fr_1fr_1fr_1fr_1fr_1fr] border-b border-slate-800/50 relative z-10 sticky top-0 bg-slate-900/60 backdrop-blur-sm">
          <div className="p-2 border-r border-slate-800/50" />
          {days.map((d, i) => (
            <div key={i} className={`p-3 text-center border-r border-slate-800/50 flex flex-col ${i === todayIdx ? 'bg-emerald-500/5' : ''}`}>
              <span className={`text-[10px] font-bold uppercase tracking-widest ${i === todayIdx ? 'text-emerald-400' : 'text-slate-500'}`}>{d}</span>
              <span className={`text-lg font-bold mt-1 mx-auto w-8 h-8 flex items-center justify-center rounded-full ${i === todayIdx ? 'bg-emerald-500 text-white shadow-[0_0_12px_rgba(16,185,129,0.5)]' : 'text-slate-300'}`}>{dates[i]}</span>
            </div>
          ))}
        </div>

        {/* Time Grid */}
        <div className="flex-1 overflow-y-auto no-scrollbar relative z-10">
          <div className="relative" style={{ height: '800px' }}>
            {/* Hour lines */}
            <div className="absolute inset-0 flex flex-col pointer-events-none">
              {hours.map((h, i) => (
                <div key={i} className="flex-1 border-b border-slate-800/40 relative">
                  <span className="absolute -top-2.5 right-0 pr-2 text-[10px] font-medium text-slate-600 w-[60px] text-right">{h}</span>
                </div>
              ))}
            </div>
            {/* Column lines */}
            <div className="absolute inset-0 grid grid-cols-[60px_1fr_1fr_1fr_1fr_1fr_1fr_1fr] pointer-events-none">
              {Array(8).fill(null).map((_, i) => (
                <div key={i} className={`border-r border-slate-800/40 ${i === 2 ? 'bg-emerald-500/[0.02]' : ''}`} />
              ))}
            </div>
            {/* Current time indicator */}
            <div className="absolute left-[60px] right-0 top-[45%] h-px bg-red-500/70 pointer-events-none z-10">
              <div className="absolute -left-1.5 -top-1.5 w-3 h-3 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.7)]" />
            </div>
            {/* Events */}
            {events.map((ev, i) => {
              const c = colorMap[ev.color];
              const leftPct = (ev.col / 7) * 100;
              return (
                <div
                  key={i}
                  className={`absolute mx-1 border rounded-xl p-2 cursor-pointer transition-all hover:scale-[1.01] ${c.bg} ${ev.featured ? 'shadow-[0_0_18px_rgba(16,185,129,0.2)]' : ''} backdrop-blur-sm flex flex-col justify-between group z-20`}
                  style={{
                    left: `calc(60px + ${leftPct}%)`,
                    width: `calc(${100/7}% - 8px)`,
                    top: `${ev.top}px`,
                    height: `${ev.h}px`,
                  }}
                >
                  <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-xl ${c.bar}`} />
                  <div className="absolute inset-0 bg-gradient-to-b from-white/[0.04] to-transparent rounded-xl pointer-events-none" />
                  <div className="pl-3 relative z-10">
                    <p className={`text-[10px] font-bold ${c.label} mb-0.5`}>{ev.time}</p>
                    <p className={`text-xs font-bold ${c.text} leading-tight group-hover:brightness-125 transition-all`}>{ev.title}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-72 flex flex-col gap-5 flex-shrink-0">
        {/* Upcoming Appointments Card */}
        <div className={`${darkCard} flex-1 flex flex-col`}>
          <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none" />
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          <div className="p-5 border-b border-slate-700/50 flex items-center gap-3 relative z-10 bg-gradient-to-b from-white/5 to-transparent">
            <h3 className="font-bold text-slate-100 tracking-wide">Próximas Citas</h3>
          </div>
          <div className="flex-1 p-4 space-y-3 relative z-10 overflow-y-auto no-scrollbar">
            {upcomingItems.map((item, i) => {
              const c = colorMap[item.color];
              return (
                <div key={i} className={`group bg-slate-800/50 hover:bg-slate-800 border border-transparent hover:border-slate-700/50 rounded-xl p-4 transition-all cursor-pointer relative overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]`}>
                  <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-xl ${c.bar}`} />
                  <div className="pl-3">
                    <p className={`text-[11px] font-bold ${c.label} mb-1`}>{item.time}</p>
                    <p className="text-sm font-bold text-slate-200">{item.title}</p>
                    <p className="text-xs text-slate-500 mt-1">{item.team}</p>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="p-4 border-t border-slate-800 relative z-10">
            <button className="w-full py-2 text-sm font-semibold text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 rounded-xl border border-slate-700/50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
              Ver Todas
            </button>
          </div>
        </div>

        {/* Location Mini-Map Card */}
        <div className={`h-48 ${darkCard} flex-shrink-0`}>
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/20 via-transparent to-black/40 pointer-events-none rounded-2xl z-10" />
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent z-20" />
          <div className="absolute inset-0 flex items-center justify-center opacity-20 z-0">
            <div className="grid grid-cols-6 gap-1.5 w-full h-full p-3">
              {Array(48).fill(null).map((_, i) => (
                <div key={i} className="bg-slate-600/50 rounded-sm" />
              ))}
            </div>
          </div>
          <div className="absolute bottom-5 left-5 z-20">
            <p className="text-xs text-emerald-400 font-bold uppercase tracking-widest flex items-center gap-1">
              <MapPin size={12} className="text-emerald-400" /> Ubicación Actual
            </p>
            <p className="text-sm font-bold text-slate-100 mt-1">Sector 4</p>
          </div>
          <div className="absolute right-5 top-1/2 -translate-y-1/2 z-20">
            <div className="w-4 h-4 rounded-full bg-emerald-500 shadow-[0_0_16px_rgba(16,185,129,0.8)] animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}
