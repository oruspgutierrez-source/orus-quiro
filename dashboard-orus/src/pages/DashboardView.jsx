import { useState, useEffect } from 'react';
import { DollarSign, Bot, Headset, ArrowRight, TrendingUp, MessageSquare, X, User, Calendar, CheckCircle2, AlertTriangle, Users } from 'lucide-react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';

const glassCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";
const darkCard  = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

export default function DashboardView() {
  const navigate = useNavigate();
  const [handovers, setHandovers] = useState([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [totalMessages, setTotalMessages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [bars, setBars] = useState([
    { h: 0, label: 'Lun', val: 0 },
    { h: 0, label: 'Mar', val: 0 },
    { h: 0, label: 'Mié', val: 0 },
    { h: 0, label: 'Jue', val: 0 },
    { h: 0, label: 'Vie', val: 0 },
    { h: 0, label: 'Sáb', val: 0 },
    { h: 0, label: 'Dom', val: 0 },
  ]);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportData, setReportData] = useState({
    total: 0,
    phase1: 0,
    phase2: 0,
    paid: 0,
    booked: 0,
    biometrics: 0,
    human: 0,
    stuckList: []
  });

  useEffect(() => {
    fetchDashboardData();
    
    // Suscribirse a cambios en tiempo real
    const usersSubscription = supabase
      .channel('public:orus_users')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'orus_users' }, payload => {
        fetchDashboardData();
      })
      .subscribe();

    return () => {
      supabase.removeChannel(usersSubscription);
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      // 1. Obtener todos los usuarios de la base de datos
      const { data: allUsers } = await supabase
        .from('orus_users')
        .select('*');

      // 1.1 Obtener todas las evaluaciones completadas
      const { data: allEvaluations } = await supabase
        .from('evaluaciones_completas')
        .select('wa_id');

      if (allUsers) {
        const total = allUsers.length;
        setTotalUsers(total);

        // Handovers activos (usuarios en modo HUMAN)
        const humanUsers = allUsers.filter(u => u.session_mode === 'HUMAN');
        setHandovers(humanUsers.map(u => ({
          id: u.id,
          name: u.wa_name || u.phone_number,
          issue: 'Solicitó intervención humana',
          time: new Date(u.updated_at || u.last_interaction || new Date()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          urgent: true
        })));

        // Normalizar números de teléfono para cruce
        const cleanPhone = (p) => p ? p.trim().replace('@s.whatsapp.net', '') : '';
        const completedEvalPhones = new Set(
          (allEvaluations || []).map(ev => cleanPhone(ev.wa_id))
        );

        // Calcular datos del reporte de embudo
        const phase1 = allUsers.filter(u => u.session_mode === 'AI' && u.payment_status !== 'paid' && u.payment_status !== 'pagado' && !u.appointment_date).length;
        const phase2 = allUsers.filter(u => u.session_mode === 'PHASE_2_AUDIO' || u.session_mode === 'PHASE_2_IMAGE' || u.payment_status === 'paid' || u.payment_status === 'pagado').length;
        const paid = allUsers.filter(u => u.payment_status === 'paid' || u.payment_status === 'pagado').length;
        const booked = allUsers.filter(u => (u.payment_status === 'paid' || u.payment_status === 'pagado') && u.appointment_date).length;
        const biometrics = allUsers.filter(u => completedEvalPhones.has(cleanPhone(u.phone_number))).length;
        const human = humanUsers.length;

        // Lista de usuarios que se quedaron en el camino (sin completar evaluación biométrica)
        const stuckList = allUsers.filter(u => !completedEvalPhones.has(cleanPhone(u.phone_number))).map(u => {
          const hasPaid = u.payment_status === 'paid' || u.payment_status === 'pagado';
          const hasBooked = !!u.appointment_date;
          
          let currentStage = 'Diagnóstico Inicial';
          if (hasPaid && hasBooked) {
            currentStage = 'Evaluación Biométrica';
          } else if (hasPaid && !hasBooked) {
            currentStage = 'Proceso de Reserva';
          } else if (u.session_mode === 'PHASE_2_AUDIO' || u.session_mode === 'PHASE_2_IMAGE') {
            currentStage = 'Audio Explicativo';
          } else if (u.session_mode === 'HUMAN') {
            currentStage = 'Atención Humana';
          } else if (u.session_mode && u.session_mode.startsWith('BOOKING_')) {
            currentStage = 'Proceso de Reserva';
          }
          
          return {
            id: u.id,
            name: u.wa_name || u.phone_number,
            phone: u.phone_number,
            stage: currentStage,
            lastActive: u.last_interaction ? new Date(u.last_interaction).toLocaleDateString('es-ES', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A',
            rawLastActive: u.last_interaction ? new Date(u.last_interaction) : new Date(0)
          };
        }).sort((a, b) => b.rawLastActive - a.rawLastActive);

        setReportData({
          total,
          phase1,
          phase2,
          paid,
          booked,
          biometrics,
          human,
          stuckList
        });
      }

      // 2. Total de mensajes
      const { count: msgCount } = await supabase
        .from('orus_messages')
        .select('*', { count: 'exact', head: true });
      setTotalMessages(msgCount || 0);

      // 3. Calcular Actividad de la Semana
      const now = new Date();
      const day = now.getDay();
      const diffToMonday = day === 0 ? -6 : 1 - day;
      const monday = new Date(now);
      monday.setDate(now.getDate() + diffToMonday);
      monday.setHours(0, 0, 0, 0);

      const { data: weekMessages } = await supabase
        .from('orus_messages')
        .select('created_at')
        .gte('created_at', monday.toISOString());

      const counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 0: 0 };
      if (weekMessages) {
        weekMessages.forEach(msg => {
          const date = new Date(msg.created_at);
          const msgDay = date.getDay();
          counts[msgDay] = (counts[msgDay] || 0) + 1;
        });
      }

      const maxVal = Math.max(...Object.values(counts), 1);
      const updatedBars = [
        { label: 'Lun', val: counts[1], h: counts[1] > 0 ? Math.max(Math.round((counts[1] / maxVal) * 100), 5) : 0 },
        { label: 'Mar', val: counts[2], h: counts[2] > 0 ? Math.max(Math.round((counts[2] / maxVal) * 100), 5) : 0 },
        { label: 'Mié', val: counts[3], h: counts[3] > 0 ? Math.max(Math.round((counts[3] / maxVal) * 100), 5) : 0 },
        { label: 'Jue', val: counts[4], h: counts[4] > 0 ? Math.max(Math.round((counts[4] / maxVal) * 100), 5) : 0 },
        { label: 'Vie', val: counts[5], h: counts[5] > 0 ? Math.max(Math.round((counts[5] / maxVal) * 100), 5) : 0 },
        { label: 'Sáb', val: counts[6], h: counts[6] > 0 ? Math.max(Math.round((counts[6] / maxVal) * 100), 5) : 0 },
        { label: 'Dom', val: counts[0], h: counts[0] > 0 ? Math.max(Math.round((counts[0] / maxVal) * 100), 5) : 0 },
      ];
      setBars(updatedBars);

      setLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      setLoading(false);
    }
  };

  const MetricCard = ({ icon, title, value, badge, badgeColor, accentColor, glowColor, borderAccent }) => (
    <div className={`${glassCard} p-5`}>
      <div className={`absolute inset-0 bg-gradient-to-br ${accentColor} opacity-50`} />
      <div className="flex items-center gap-4 relative z-10">
        <div className={`p-3 rounded-xl bg-slate-800 border ${borderAccent} text-slate-200`}>{icon}</div>
        <div>
          <p className="text-sm text-slate-400 font-medium">{title}</p>
          <p className="text-2xl font-bold text-slate-100">{value}</p>
        </div>
      </div>
    </div>
  );

  const todayIdx = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;
  const currentDate = new Date().toLocaleDateString('es-ES', { month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <div className="flex-1 p-4 space-y-4 overflow-auto" style={{background: 'radial-gradient(circle at 50% 50%, #ffffff 0%, #fafafa 40%, #f0f0f0 75%, #e9e9e9 100%)'}}>

      {/* Page Header */}
      <div className="flex justify-between items-end relative z-10">
        <div>
          <h3 className="text-2xl font-bold text-slate-800">Buenos días, Admin</h3>
          <p className="text-slate-500 mt-1 font-medium">Aquí tienes el último vistazo de las operaciones de Orus.</p>
        </div>
        <div className="text-slate-500 text-sm flex items-center gap-2 bg-white/80 border border-slate-200 px-4 py-2 rounded-xl shadow-sm backdrop-blur-sm font-medium">
          {currentDate}
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
        <MetricCard
          icon={<Bot size={22} />}
          title="Total de Usuarios"
          value={loading ? "..." : totalUsers.toString()}
        />
        <MetricCard
          icon={<MessageSquare size={22} />}
          title="Total de Mensajes"
          value={loading ? "..." : totalMessages.toString()}
        />
        <MetricCard
          icon={<Headset size={22} />}
          title="Intervenciones Humanas"
          value={loading ? "..." : `${handovers.length} Activas`}
        />
      </div>

      {/* Main Data Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
        {/* Chart Card */}
        <div className={`lg:col-span-2 ${darkCard} p-6 flex flex-col`}>
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.02] to-transparent pointer-events-none" />
          <div className="flex justify-between items-center mb-6 relative z-10">
            <h4 className="text-lg font-bold text-zinc-100 tracking-wide">Actividad de Usuarios Esta Semana</h4>
            <button 
              onClick={() => setReportModalOpen(true)}
              className="text-emerald-400 text-sm font-semibold hover:text-emerald-300 flex items-center gap-1 transition-colors bg-white/5 px-3 py-1.5 rounded-xl border border-emerald-500/20 shadow-sm"
            >
              Ver Informe <ArrowRight size={15} />
            </button>
          </div>
          {/* Bar Chart */}
          <div className="flex-1 min-h-[220px] flex items-end gap-3 relative z-10 pt-4 h-[220px]">
            {bars.map((b, i) => (
              <div key={i} className="flex-1 h-full flex flex-col justify-end items-center gap-2 group">
                <div className="w-full flex-1 flex items-end relative">
                  <div
                    className={`w-full rounded-t-lg transition-all relative ${i === todayIdx ? 'bg-gradient-to-t from-emerald-600 to-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.4)]' : 'bg-gradient-to-t from-zinc-700 to-zinc-600 group-hover:from-emerald-800 group-hover:to-emerald-600'}`}
                    style={{ height: `${b.h}%` }}
                  >
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-zinc-800 text-zinc-100 text-xs px-2 py-1 rounded-md border border-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-lg z-20">
                      {b.val} activos
                    </div>
                    <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
                  </div>
                </div>
                <span className="text-xs text-zinc-500 font-medium shrink-0">{b.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Handovers Card */}
        <div className={`${glassCard} flex flex-col`}>
          <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none" />
          <div className="p-4 border-b border-slate-700/50 flex justify-between items-center relative z-10 bg-gradient-to-b from-white/5 to-transparent">
            <h4 className="font-bold text-slate-100 tracking-wide">Handovers Activos</h4>
            <span className={`${handovers.length > 0 ? 'bg-red-500/20 text-red-300 border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.2)]' : 'bg-slate-500/20 text-slate-300 border-slate-500/30'} text-xs px-2 py-0.5 rounded-full font-semibold border`}>
              {handovers.length} Req. Acción
            </span>
          </div>
          <div className="flex-1 p-2 space-y-1 relative z-10 overflow-y-auto no-scrollbar min-h-[220px]">
            {handovers.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 opacity-70">
                <Bot size={40} className="mb-2 opacity-50" />
                <p className="text-sm font-medium">El bot tiene todo bajo control.</p>
                <p className="text-xs">No hay usuarios esperando.</p>
              </div>
            ) : (
              handovers.map((item, i) => (
                <div 
                  key={item.id || i} 
                  onClick={() => navigate(`/chat?userId=${item.id}`)}
                  className={`p-3 rounded-xl cursor-pointer flex items-center gap-3 border transition-all ${item.urgent ? 'border-red-500/20 bg-red-500/5 hover:bg-red-500/10' : 'border-transparent hover:bg-white/5 hover:border-white/10'}`}
                >
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 border border-slate-600/50 shrink-0 shadow-inner flex items-center justify-center">
                    <span className="text-slate-300 text-xs font-bold">{item.name[0]?.toUpperCase()}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-200 truncate">{item.name}</p>
                    <p className="text-xs text-slate-500 truncate">{item.issue}</p>
                  </div>
                  <div className="text-xs text-slate-500 whitespace-nowrap">{item.time}</div>
                </div>
              ))
            )}
          </div>
          <div className="p-3 border-t border-slate-800 relative z-10">
            <button 
              onClick={() => {
                if (handovers.length > 0) {
                  navigate(`/chat?userId=${handovers[0].id}`);
                } else {
                  navigate('/chat');
                }
              }}
              className="w-full py-2 text-sm font-semibold text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 rounded-xl border border-slate-700/50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
            >
              Ver En Inbox
            </button>
          </div>
        </div>
      </div>

      {/* Report Modal */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className="relative w-full max-w-4xl bg-gradient-to-b from-slate-900 via-zinc-950 to-slate-950 border border-slate-800/80 rounded-3xl shadow-2xl p-6 md:p-8 max-h-[85vh] overflow-y-auto flex flex-col gap-6 scrollbar-thin scrollbar-thumb-zinc-700">
            
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-slate-800/60 pb-4">
              <div>
                <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <TrendingUp className="text-emerald-400" size={24} />
                  Informe de Conversión y Flujo de Clientes
                </h3>
                <p className="text-slate-400 text-sm mt-1 font-medium">Análisis en tiempo real de leads, audio explicativo, pagos y agendamiento.</p>
              </div>
              <button 
                onClick={() => setReportModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-slate-800"
              >
                <X size={18} />
              </button>
            </div>

            {/* Metrics Dashboard Inside Modal */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="bg-slate-950/40 border border-slate-800 p-4 rounded-2xl flex flex-col">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tasa Conversión (Leads a Pago)</span>
                <span className="text-2xl font-black text-emerald-400 mt-1">
                  {totalUsers > 0 ? ((reportData.paid / totalUsers) * 100).toFixed(1) : "0.0"}%
                </span>
                <span className="text-xs text-slate-400 mt-1">{reportData.paid} de {totalUsers} clientes</span>
              </div>
              <div className="bg-slate-950/40 border border-slate-800 p-4 rounded-2xl flex flex-col">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tasa Agendamiento (Pagos a Cita)</span>
                <span className="text-2xl font-black text-blue-400 mt-1">
                  {reportData.paid > 0 ? ((reportData.booked / reportData.paid) * 100).toFixed(1) : "0.0"}%
                </span>
                <span className="text-xs text-slate-400 mt-1">{reportData.booked} de {reportData.paid} pagados</span>
              </div>
              <div className="bg-slate-950/40 border border-slate-800 p-4 rounded-2xl flex flex-col">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tasa Biométrica (Citas a Eval)</span>
                <span className="text-2xl font-black text-purple-400 mt-1">
                  {reportData.booked > 0 ? ((reportData.biometrics / reportData.booked) * 100).toFixed(1) : "0.0"}%
                </span>
                <span className="text-xs text-slate-400 mt-1">{reportData.biometrics} de {reportData.booked} agendados</span>
              </div>
              <div className="bg-slate-950/40 border border-slate-800 p-4 rounded-2xl flex flex-col">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tasa de Atención Humana</span>
                <span className="text-2xl font-black text-amber-400 mt-1">
                  {totalUsers > 0 ? ((reportData.human / totalUsers) * 100).toFixed(1) : "0.0"}%
                </span>
                <span className="text-xs text-slate-400 mt-1">{reportData.human} requeridos</span>
              </div>
            </div>

            {/* Funnel Section */}
            <div className="bg-slate-950/20 border border-slate-800/80 rounded-2xl p-6">
              <h4 className="font-bold text-slate-200 text-sm mb-4 uppercase tracking-wider flex items-center gap-2">
                <Users size={16} className="text-slate-400" />
                Embudo de Conversión (Funnel)
              </h4>
              
              <div className="space-y-4">
                {/* Step 1: Leads */}
                <div className="space-y-1">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-slate-300">Paso 1: Leads Totales (Chat Iniciado)</span>
                    <span className="text-slate-400">{totalUsers} (100%)</span>
                  </div>
                  <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div className="h-full bg-slate-700" style={{ width: '100%' }} />
                  </div>
                </div>

                {/* Step 2: Audio Explicativo */}
                <div className="space-y-1">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-slate-300">Paso 2: Audio Explicativo Enviado</span>
                    <span className="text-slate-400">
                      {reportData.phase2} ({totalUsers > 0 ? ((reportData.phase2 / totalUsers) * 100).toFixed(0) : 0}%)
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500" style={{ width: `${totalUsers > 0 ? (reportData.phase2 / totalUsers) * 100 : 0}%` }} />
                  </div>
                </div>

                {/* Step 3: Pago Confirmado */}
                <div className="space-y-1">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-slate-300">Paso 3: Pago Confirmado</span>
                    <span className="text-slate-400">
                      {reportData.paid} ({totalUsers > 0 ? ((reportData.paid / totalUsers) * 100).toFixed(0) : 0}%)
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500" style={{ width: `${totalUsers > 0 ? (reportData.paid / totalUsers) * 100 : 0}%` }} />
                  </div>
                </div>

                {/* Step 4: Cita Agendada */}
                <div className="space-y-1">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-slate-300">Paso 4: Cita Agendada en Calendario</span>
                    <span className="text-slate-400">
                      {reportData.booked} ({totalUsers > 0 ? ((reportData.booked / totalUsers) * 100).toFixed(0) : 0}%)
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500" style={{ width: `${totalUsers > 0 ? (reportData.booked / totalUsers) * 100 : 0}%` }} />
                  </div>
                </div>

                {/* Step 5: Biometrics */}
                <div className="space-y-1">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-slate-300">Paso 5: Evaluación Biométrica Completada (Formulario y Fotos)</span>
                    <span className="text-slate-400">
                      {reportData.biometrics} ({totalUsers > 0 ? ((reportData.biometrics / totalUsers) * 100).toFixed(0) : 0}%)
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500" style={{ width: `${totalUsers > 0 ? (reportData.biometrics / totalUsers) * 100 : 0}%` }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Stuck Users List */}
            <div className="flex-grow flex flex-col gap-3">
              <h4 className="font-bold text-slate-200 text-sm uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-500" />
                Clientes que no continuaron (Abandono/Stuck)
              </h4>
              
              <div className="flex-grow border border-slate-800 rounded-2xl overflow-hidden bg-slate-950/20">
                <div className="overflow-x-auto max-h-[300px]">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold sticky top-0 z-10">
                        <th className="p-3 pl-4">Cliente</th>
                        <th className="p-3">Teléfono</th>
                        <th className="p-3">Etapa Abandonada</th>
                        <th className="p-3">Última Actividad</th>
                        <th className="p-3 pr-4 text-right">Acción</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {reportData.stuckList.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="p-8 text-center text-slate-500 font-medium">
                            Ningún cliente estancado actualmente.
                          </td>
                        </tr>
                      ) : (
                        reportData.stuckList.map((client) => (
                          <tr key={client.id} className="hover:bg-white/[0.02] text-slate-300 transition-colors">
                            <td className="p-3 pl-4 font-semibold text-slate-200">{client.name}</td>
                            <td className="p-3 font-mono text-xs text-slate-400">{client.phone}</td>
                            <td className="p-3">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${
                                client.stage === 'Audio Explicativo' 
                                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                                  : client.stage === 'Atención Humana'
                                  ? 'bg-red-500/10 text-red-300 border-red-500/20'
                                  : 'bg-zinc-500/10 text-zinc-300 border-zinc-500/20'
                              }`}>
                                {client.stage}
                              </span>
                            </td>
                            <td className="p-3 text-slate-400 text-xs">{client.lastActive}</td>
                            <td className="p-3 pr-4 text-right">
                              <button 
                                onClick={() => {
                                  setReportModalOpen(false);
                                  navigate(`/chat?userId=${client.id}`);
                                }}
                                className="px-3 py-1.5 bg-emerald-500 text-slate-950 hover:bg-emerald-400 transition-colors font-bold rounded-lg text-xs"
                              >
                                Abrir Chat
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      )}
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
