import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Plus, StickyNote, Save, Loader2, Calendar as CalIcon, Trash2, Edit2 } from 'lucide-react';

const glassCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";
const darkCard  = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

const days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
const hours = ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00'];

const colorMap = {
  emerald: { bg: 'bg-emerald-900/40 border-emerald-500/40', bar: 'bg-emerald-400', text: 'text-emerald-300', label: 'text-emerald-400' },
  amber:   { bg: 'bg-amber-900/30 border-amber-500/30',     bar: 'bg-amber-400',   text: 'text-amber-200',   label: 'text-amber-400' },
  slate:   { bg: 'bg-slate-700/40 border-slate-500/30',     bar: 'bg-slate-400',   text: 'text-slate-200',   label: 'text-slate-400' },
  rose:    { bg: 'bg-rose-900/40 border-rose-500/40',       bar: 'bg-rose-400',    text: 'text-rose-300',    label: 'text-rose-400' },
};

export default function CalendarView() {
  const [events, setEvents] = useState([]);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingNotes, setLoadingNotes] = useState(true);
  const [savingNote, setSavingNote] = useState(false);
  
  const [weekOffset, setWeekOffset] = useState(0);
  const [activeNoteEvent, setActiveNoteEvent] = useState(null);
  const [noteContent, setNoteContent] = useState('');
  const [expandedEventId, setExpandedEventId] = useState(null);
  const [eventColors, setEventColors] = useState({});
  const [expandedNoteId, setExpandedNoteId] = useState(null);

  // Fetch Events from Google Calendar
  useEffect(() => {
    async function fetchEvents() {
      setLoading(true);
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
        const API_KEY = import.meta.env.VITE_API_KEY || 'OrusDashboardAdmin2026';
        
        // Calcular inicio y fin de la semana seleccionada
        const today = new Date();
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay() + 1 + (weekOffset * 7));
        startOfWeek.setHours(0,0,0,0);
        
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 7);
        
        const timeMin = startOfWeek.toISOString();
        const timeMax = endOfWeek.toISOString();

        const res = await fetch(`${API_URL}/api/calendar/events?time_min=${timeMin}&time_max=${timeMax}`, {
          headers: { 'x-api-key': API_KEY }
        });
        
        if (res.ok) {
          const data = await res.json();
          // Map google events to our layout
          const mapped = data.events.map(ev => {
            if (!ev.start || !ev.start.dateTime) return null;
            const start = new Date(ev.start.dateTime);
            const end = new Date(ev.end.dateTime);
            
            // Calculate column (0 = Monday, 6 = Sunday)
            let col = start.getDay() - 1;
            if (col === -1) col = 6;
            
            // Calculate top and height based on 800px grid (12 hours: 08:00 to 20:00 = 12 slots)
            const slotHeight = 800 / 12; // 66.66px per hour
            
            const startHour = start.getHours() + (start.getMinutes() / 60);
            const endHour = end.getHours() + (end.getMinutes() / 60);
            
            const top = (startHour - 8) * slotHeight;
            const h = (endHour - startHour) * slotHeight;
            
            return {
              id: ev.id,
              col,
              top: Math.max(0, top),
              h: Math.max(20, h), // min height
              title: ev.summary || 'Cita',
              time: `${start.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})} - ${end.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}`,
              team: ev.attendees ? ev.attendees.map(a=>a.email).join(', ') : 'Paciente',
              color: 'emerald',
              rawStart: start
            };
          }).filter(e => e !== null);
          setEvents(mapped);
        }
      } catch (e) {
        console.error("Error fetching events", e);
      } finally {
        setLoading(false);
      }
    }
    fetchEvents();
  }, [weekOffset]);

  // Fetch Notes
  useEffect(() => {
    async function fetchNotes() {
      setLoadingNotes(true);
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
        const API_KEY = import.meta.env.VITE_API_KEY || 'OrusDashboardAdmin2026';
        
        const res = await fetch(`${API_URL}/api/calendar/notes`, {
          headers: { 'x-api-key': API_KEY }
        });
        
        if (res.ok) {
          const data = await res.json();
          setNotes(data.notes || []);
        }
      } catch (e) {
        console.error("Error fetching notes", e);
      } finally {
        setLoadingNotes(false);
      }
    }
    fetchNotes();
  }, []);

  const handleSaveNote = async () => {
    if (!activeNoteEvent) return;
    setSavingNote(true);
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
      const API_KEY = import.meta.env.VITE_API_KEY || 'OrusDashboardAdmin2026';
      
      const eventDateStr = activeNoteEvent.rawStart ? new Date(activeNoteEvent.rawStart).toLocaleDateString() : new Date().toLocaleDateString();
      const finalClientName = (eventDateStr && !activeNoteEvent.title.includes(eventDateStr))
        ? `${activeNoteEvent.title} - ${eventDateStr}`
        : activeNoteEvent.title;

      const payload = {
        event_id: activeNoteEvent.id,
        client_name: finalClientName,
        note_content: noteContent
      };

      const res = await fetch(`${API_URL}/api/calendar/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const responseData = await res.json();
        const realId = (responseData.data && responseData.data.length > 0) ? responseData.data[0].id : ('temp_' + Date.now());

        // UI update with real ID
        const newNote = {
          id: realId,
          event_id: activeNoteEvent.id,
          client_name: finalClientName,
          note_content: noteContent,
          created_at: new Date().toISOString()
        };
        setNotes([newNote, ...notes.filter(n => n.event_id !== activeNoteEvent.id)]);
        setActiveNoteEvent(null);
        setNoteContent('');
      } else {
        alert("Error al guardar la nota");
      }
    } catch (e) {
      console.error(e);
      alert("Error de conexión");
    } finally {
      setSavingNote(false);
    }
  };

  const handleDeleteNote = async (noteId, e) => {
    e.stopPropagation();
    if (!confirm("¿Seguro que deseas eliminar esta nota?")) return;
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
      const API_KEY = import.meta.env.VITE_API_KEY || 'OrusDashboardAdmin2026';
      
      const res = await fetch(`${API_URL}/api/calendar/notes/${noteId}`, {
        method: 'DELETE',
        headers: { 'x-api-key': API_KEY }
      });
      if (res.ok) {
        setNotes(notes.filter(n => n.id !== noteId));
      } else {
        alert("Error al eliminar nota");
      }
    } catch (err) {
      console.error(err);
      alert("Error de conexión");
    }
  };

  // Setup current week dates
  const todayDate = new Date();
  const currentDates = days.map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - d.getDay() + 1 + i + (weekOffset * 7));
    return d.getDate();
  });
  const todayIdx = weekOffset === 0 ? todayDate.getDay() - 1 : -1;

  // Recent upcoming events for the sidebar
  const upcomingItems = events
    .filter(e => e.rawStart >= new Date())
    .sort((a,b) => a.rawStart - b.rawStart)
    .slice(0, 3);

  return (
    <div className="flex-1 flex p-4 gap-4 bg-white overflow-auto">

      {/* Calendar Main Card */}
      <div className={`flex-1 ${glassCard} flex flex-col min-w-0`}>
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.02] to-transparent pointer-events-none" />
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        {/* Controls */}
        <div className="p-4 border-b border-slate-700/50 flex justify-between items-center relative z-10 bg-gradient-to-b from-white/5 to-transparent">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-bold text-slate-100 tracking-wide">
              {new Date().toLocaleString('es-ES', { month: 'long', year: 'numeric' }).toUpperCase()}
            </h2>
            <div className="flex items-center gap-1 bg-slate-800/80 rounded-xl p-1 border border-slate-700/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
              <button onClick={() => setWeekOffset(w=>w-1)} className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-white/10 transition-colors"><ChevronLeft size={16} /></button>
              <button onClick={() => setWeekOffset(0)} className="font-semibold text-sm text-slate-200 px-3 py-1 rounded-lg hover:bg-white/10 transition-colors">Hoy</button>
              <button onClick={() => setWeekOffset(w=>w+1)} className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-white/10 transition-colors"><ChevronRight size={16} /></button>
            </div>
            {loading && <Loader2 size={16} className="text-emerald-500 animate-spin" />}
          </div>
        </div>

        {/* Week Header */}
        <div className="grid grid-cols-[60px_1fr_1fr_1fr_1fr_1fr_1fr_1fr] border-b border-slate-800/50 relative z-10 sticky top-0 bg-slate-900/60 backdrop-blur-sm">
          <div className="p-2 border-r border-slate-800/50" />
          {days.map((d, i) => (
            <div key={i} className={`p-3 text-center border-r border-slate-800/50 flex flex-col ${i === todayIdx ? 'bg-emerald-500/5' : ''}`}>
              <span className={`text-[10px] font-bold uppercase tracking-widest ${i === todayIdx ? 'text-emerald-400' : 'text-slate-500'}`}>{d}</span>
              <span className={`text-lg font-bold mt-1 mx-auto w-8 h-8 flex items-center justify-center rounded-full ${i === todayIdx ? 'bg-emerald-500 text-white shadow-[0_0_12px_rgba(16,185,129,0.5)]' : 'text-slate-300'}`}>{currentDates[i]}</span>
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
            
            {/* Events */}
            {events.map((ev, i) => {
              const currentColor = eventColors[ev.id] || ev.color;
              const c = colorMap[currentColor] || colorMap.emerald;
              // Ajustar left y width basándonos en (100% - 60px) / 7
              const isExpanded = expandedEventId === ev.id;
              
              // Ajustar altura si se sale del contenedor
              const finalH = ev.top + ev.h > 800 ? 800 - ev.top : ev.h;
              if(ev.top > 800 || ev.top < 0) return null; // Fuera del rango de 8am a 8pm

              // Si está en las últimas dos columnas y se expande, podríamos querer que flote hacia la izquierda para que no se salga de la pantalla.
              const transformOrigin = ev.col > 4 ? 'origin-top-right' : 'origin-top-left';

              return (
                <div
                  key={ev.id || i}
                  onClick={() => setExpandedEventId(isExpanded ? null : ev.id)}
                  className={`absolute mx-1 border rounded-xl p-2 transition-all cursor-pointer ${c.bg} backdrop-blur-sm flex flex-col justify-start group ${transformOrigin} ${isExpanded ? 'z-50 shadow-[0_10px_40px_rgba(0,0,0,0.5)] scale-110' : 'z-20 hover:scale-[1.01]'}`}
                  style={{
                    left: `calc(60px + ((100% - 60px) / 7) * ${ev.col})`,
                    width: isExpanded ? '200px' : `calc(((100% - 60px) / 7) - 8px)`,
                    top: `${ev.top}px`,
                    height: isExpanded ? 'max-content' : `${finalH}px`,
                    minHeight: `${finalH}px`,
                    overflow: isExpanded ? 'visible' : 'hidden'
                  }}
                >
                  <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-xl ${c.bar}`} />
                  <div className="absolute inset-0 bg-gradient-to-b from-white/[0.04] to-transparent rounded-xl pointer-events-none" />
                  
                  <div className="pl-3 relative z-10 flex justify-between items-start mb-2">
                    <div className="flex-1 pr-2">
                      <p className={`text-[10px] font-bold ${c.label} mb-0.5`}>{ev.time}</p>
                      <p className={`text-xs font-bold ${c.text} leading-tight transition-all ${isExpanded ? '' : 'truncate'}`} style={isExpanded ? { wordBreak: 'break-word' } : {}}>{ev.title}</p>
                    </div>
                    {/* Botón para Añadir Nota */}
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveNoteEvent(ev);
                        // Buscar si ya existe una nota para pre-llenarla
                        const existingNote = notes.find(n => n.event_id === ev.id);
                        setNoteContent(existingNote ? existingNote.note_content : '');
                      }}
                      className={`w-6 h-6 rounded-md bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-opacity flex-shrink-0 ${isExpanded ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                      title="Agregar/Ver Nota Clínica"
                    >
                      <Plus size={14} />
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="pl-3 mt-auto pt-3 border-t border-white/10 flex gap-2 relative z-10">
                       <button onClick={(e) => { e.stopPropagation(); setEventColors({...eventColors, [ev.id]: 'emerald'}); }} className="w-5 h-5 rounded-full bg-emerald-500 hover:ring-2 ring-offset-1 ring-offset-transparent ring-emerald-300 transition-all shadow-sm" title="Confirmado (Verde)" />
                       <button onClick={(e) => { e.stopPropagation(); setEventColors({...eventColors, [ev.id]: 'amber'}); }} className="w-5 h-5 rounded-full bg-amber-500 hover:ring-2 ring-offset-1 ring-offset-transparent ring-amber-300 transition-all shadow-sm" title="Pendiente (Amarillo)" />
                       <button onClick={(e) => { e.stopPropagation(); setEventColors({...eventColors, [ev.id]: 'slate'}); }} className="w-5 h-5 rounded-full bg-slate-500 hover:ring-2 ring-offset-1 ring-offset-transparent ring-slate-300 transition-all shadow-sm" title="Finalizado (Gris)" />
                       <button onClick={(e) => { e.stopPropagation(); setEventColors({...eventColors, [ev.id]: 'rose'}); }} className="w-5 h-5 rounded-full bg-rose-500 hover:ring-2 ring-offset-1 ring-offset-transparent ring-rose-300 transition-all shadow-sm" title="Cancelado (Rojo)" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-[320px] flex flex-col gap-5 flex-shrink-0">
        
        {/* Editor de Nota Activa (Aparece al hacer clic en el + de un evento) */}
        {activeNoteEvent && (
          <div className={`${darkCard} flex-shrink-0 animate-in fade-in slide-in-from-right-4 duration-300`}>
            <div className="p-4 border-b border-emerald-500/30 bg-emerald-900/20 flex items-center justify-between relative z-10">
              <h3 className="font-bold text-emerald-400 text-sm flex items-center gap-2">
                <StickyNote size={16} /> Nueva Nota
              </h3>
              <button onClick={() => setActiveNoteEvent(null)} className="text-zinc-500 hover:text-white">✕</button>
            </div>
            <div className="p-4 relative z-10 flex flex-col gap-3">
              <div className="bg-black/40 rounded-lg p-2 border border-zinc-800">
                <p className="text-xs text-zinc-500">Paciente</p>
                <p className="text-sm font-bold text-zinc-200 truncate">{activeNoteEvent.title}</p>
              </div>
              <textarea 
                value={noteContent}
                onChange={e => setNoteContent(e.target.value)}
                placeholder="Escribe el progreso, diagnóstico o pendientes de la cita..."
                className="w-full h-32 bg-zinc-900/80 border border-zinc-700 rounded-lg p-3 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 resize-none transition-all shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]"
              />
              <button 
                onClick={handleSaveNote}
                disabled={savingNote || !noteContent.trim()}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-500 text-white font-bold text-sm shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:bg-emerald-400 hover:shadow-[0_0_20px_rgba(16,185,129,0.5)] transition-all disabled:opacity-50"
              >
                {savingNote ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                Guardar Nota
              </button>
            </div>
          </div>
        )}

        {/* Upcoming Appointments Card */}
        <div className={`${darkCard} flex-shrink-0`}>
          <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none" />
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          <div className="p-4 border-b border-slate-700/50 flex items-center gap-2 relative z-10 bg-gradient-to-b from-white/5 to-transparent">
            <CalIcon size={16} className="text-slate-400" />
            <h3 className="font-bold text-slate-100 text-sm tracking-wide">Próximas Citas</h3>
          </div>
          <div className="p-4 space-y-2 relative z-10 max-h-48 overflow-y-auto no-scrollbar">
            {upcomingItems.length === 0 ? (
              <p className="text-xs text-zinc-500 text-center">No hay citas próximas hoy.</p>
            ) : upcomingItems.map((item, i) => (
              <div key={i} className="bg-slate-800/50 border border-slate-700/30 rounded-lg p-3 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-400 rounded-l-lg" />
                <div className="pl-2">
                  <p className="text-[10px] font-bold text-emerald-400 mb-0.5">{item.time}</p>
                  <p className="text-sm font-bold text-slate-200 truncate">{item.title}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Notas Clínicas Guardadas */}
        <div className={`flex-1 ${darkCard} flex flex-col min-h-[300px]`}>
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/10 via-transparent to-black/40 pointer-events-none z-10" />
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent z-20" />
          <div className="p-4 border-b border-slate-700/50 relative z-20 bg-gradient-to-b from-white/5 to-transparent flex items-center gap-2">
            <StickyNote size={16} className="text-emerald-400" />
            <h3 className="font-bold text-slate-100 text-sm tracking-wide">Notas de Sesión</h3>
          </div>
          <div className="flex-1 p-4 space-y-3 relative z-20 overflow-y-auto no-scrollbar">
            {loadingNotes ? (
              <Loader2 size={24} className="text-emerald-500 animate-spin mx-auto mt-10" />
            ) : notes.length === 0 ? (
              <p className="text-xs text-zinc-500 text-center mt-10">Sin notas registradas.</p>
            ) : (
              notes.map((note) => (
                <div key={note.id} className="bg-black/40 border border-zinc-700/50 rounded-xl p-3 hover:border-emerald-500/30 transition-all group cursor-pointer" onClick={() => {
                  setExpandedNoteId(expandedNoteId === note.id ? null : note.id);
                }}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="text-xs flex flex-col gap-0.5 pr-2">
                      {note.client_name.split(' - ').map((part, idx) => (
                        <span key={idx} className={idx === 0 ? "font-bold text-zinc-200" : idx === 1 ? "text-zinc-400 font-medium" : "text-emerald-400 text-[10px]"}>
                          {part}
                        </span>
                      ))}
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveNoteEvent({ id: note.event_id, title: note.client_name });
                          setNoteContent(note.note_content);
                        }}
                        className="text-zinc-600 hover:text-emerald-400 p-1 transition-colors"
                        title="Editar Nota"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button 
                        onClick={(e) => handleDeleteNote(note.id, e)}
                        className="text-zinc-600 hover:text-rose-500 p-1 transition-colors"
                        title="Eliminar Nota"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                  <p className={`text-xs text-zinc-400 leading-relaxed border-t border-zinc-800/50 pt-2 ${expandedNoteId === note.id ? '' : 'line-clamp-3'}`}>{note.note_content}</p>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
