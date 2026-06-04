import { useState, useEffect, useRef } from 'react';
import { MoreVertical, Paperclip, Smile, Zap, Send, AlertCircle, Bot, Phone, CheckCircle, Loader2, MessageSquare } from 'lucide-react';
import { supabase } from '../supabaseClient';

export default function InboxChatView() {
  const [activeUsers, setActiveUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  
  const messagesEndRef = useRef(null);

  const glassCardStyle = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] flex flex-col backdrop-blur-md";
  const headerStyle = "p-4 border-b border-slate-700/50 bg-gradient-to-b from-white/5 to-transparent flex justify-between items-center";
  const chatCardStyle = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] flex flex-col backdrop-blur-md";
  const chatHeaderStyle = "p-4 border-b border-zinc-700/50 bg-gradient-to-b from-white/5 to-transparent flex justify-between items-center";

  // Cargar usuarios activos o que requieran atención
  const fetchUsers = async () => {
    try {
      // Priorizar los que están en modo HUMAN, luego ordenados por ultima actualizacion
      const { data } = await supabase
        .from('orus_users')
        .select('*')
        .order('session_mode', { ascending: false }) // 'HUMAN' > 'AI' (alfabeticamente, H va antes que A) wait, H comes after A. Let's just order by updated_at
        .order('last_interaction', { ascending: false })
        .limit(20);
      
      if (data) setActiveUsers(data);
    } catch (error) {
      console.error("Error al cargar usuarios:", error);
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchUsers();

    const usersChannel = supabase
      .channel('public:orus_users')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'orus_users' }, payload => {
        fetchUsers();
      })
      .subscribe();

    return () => supabase.removeChannel(usersChannel);
  }, []);

  // Cargar mensajes cuando se selecciona un usuario
  const fetchMessages = async (userId) => {
    setLoadingMessages(true);
    try {
      const { data } = await supabase
        .from('orus_messages')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: true });
      if (data) setMessages(data);
    } catch (error) {
      console.error("Error al cargar mensajes:", error);
    } finally {
      setLoadingMessages(false);
      scrollToBottom();
    }
  };

  useEffect(() => {
    if (selectedUser) {
      fetchMessages(selectedUser.id);

      const messagesChannel = supabase
        .channel(`messages-${selectedUser.id}`)
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'orus_messages', filter: `user_id=eq.${selectedUser.id}` }, payload => {
          setMessages(prev => [...prev, payload.new]);
          scrollToBottom();
        })
        .subscribe();

      return () => supabase.removeChannel(messagesChannel);
    }
  }, [selectedUser]);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // Enviar mensaje manual
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedUser) return;
    
    setSending(true);
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
      const API_KEY = import.meta.env.VITE_API_KEY || 'OrusDashboardAdmin2026'; // Default fallback config
      
      const response = await fetch(`${API_URL}/api/users/${selectedUser.id}/send_manual_message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY
        },
        body: JSON.stringify({ message: inputMessage.trim() })
      });

      if (!response.ok) {
        throw new Error('Error al enviar el mensaje');
      }

      setInputMessage('');
    } catch (error) {
      console.error("Error enviando mensaje manual:", error);
      alert("Error al enviar mensaje. Verifica que la API Key y la URL estén configuradas.");
    } finally {
      setSending(false);
    }
  };

  // Finalizar intervención (Devolver al Bot)
  const handleResolveSession = async () => {
    if (!selectedUser || selectedUser.session_mode === 'AI') return;

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'https://api.orusquiroterapia.online';
      const API_KEY = import.meta.env.VITE_API_KEY || 'OrusDashboardAdmin2026';
      
      await fetch(`${API_URL}/api/users/${selectedUser.id}/resolve`, {
        method: 'POST',
        headers: { 'x-api-key': API_KEY }
      });
      // La lista se actualizará sola vía Realtime
      setSelectedUser(prev => ({...prev, session_mode: 'AI'}));
    } catch (error) {
      console.error("Error al finalizar sesión:", error);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden p-4 gap-4 bg-white">

      {/* Column 1: Active Chats List */}
      <aside className={`w-1/4 ${glassCardStyle}`}>
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.02] to-transparent pointer-events-none"></div>

        <div className={headerStyle}>
          <h3 className="font-semibold text-slate-100 tracking-wide">Chats activos</h3>
        </div>
        <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-2 relative z-10">
          
          {loadingUsers ? (
            <div className="flex flex-col items-center justify-center p-6 opacity-50">
              <Loader2 className="animate-spin text-slate-400 mb-2" />
              <p className="text-xs text-slate-400">Cargando...</p>
            </div>
          ) : activeUsers.map(u => {
            const isHumanMode = u.session_mode === 'HUMAN';
            const isSelected = selectedUser?.id === u.id;
            
            return (
              <div 
                key={u.id}
                onClick={() => setSelectedUser(u)}
                className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all border ${
                  isSelected ? 'bg-white/10 border-white/20' : 
                  isHumanMode ? 'bg-gradient-to-br from-red-500/10 to-red-900/10 border-red-500/20 hover:border-red-500/40' : 
                  'border-transparent hover:bg-white/5 hover:border-white/10'
                }`}
              >
                <div className="w-10 h-10 rounded-full bg-slate-700 shrink-0 shadow-inner flex items-center justify-center text-slate-300 font-bold">
                  {u.push_name ? u.push_name[0].toUpperCase() : u.phone_number.substring(0,1)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-baseline mb-1">
                    <h4 className="text-sm text-slate-200 font-semibold truncate">{u.push_name || u.phone_number}</h4>
                    {isHumanMode && <span className="text-xs text-red-400 font-medium">Urgente</span>}
                  </div>
                  <span className={`inline-flex items-center gap-1 mt-1 text-[10px] px-2 py-0.5 rounded-md border font-medium ${
                    isHumanMode ? 'text-red-300 bg-red-500/20 border-red-500/30' : 'text-emerald-300 bg-emerald-500/20 border-emerald-500/30'
                  }`}>
                    {isHumanMode ? <><AlertCircle size={10} /> Requiere Humano</> : <><Bot size={10} /> IA Activa</>}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </aside>

      {/* Column 2: Live Chat Thread */}
      <main className={`flex-1 ${chatCardStyle}`}>
        <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none"></div>

        {!selectedUser ? (
          <div className="flex-1 flex flex-col items-center justify-center relative z-10 text-zinc-500">
            <MessageSquare size={48} className="mb-4 opacity-50" />
            <p className="font-medium">Selecciona un chat para comenzar</p>
          </div>
        ) : (
          <>
            {/* Chat Header */}
            <div className={`${chatHeaderStyle} shrink-0`}>
              <div className="flex items-center gap-4">
                <div className="w-11 h-11 rounded-full bg-zinc-700 border border-zinc-600 shadow-inner flex items-center justify-center font-bold text-zinc-300">
                  {selectedUser.push_name ? selectedUser.push_name[0].toUpperCase() : selectedUser.phone_number.substring(0,1)}
                </div>
                <div>
                  <h2 className="text-lg font-bold text-zinc-100 tracking-wide">{selectedUser.push_name || 'Desconocido'}</h2>
                  <p className="text-xs text-zinc-400 flex items-center gap-1 font-medium">
                    <Phone size={12} className="text-zinc-500" /> {selectedUser.phone_number}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                {selectedUser.session_mode === 'HUMAN' && (
                  <button onClick={handleResolveSession} className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30 px-3 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1">
                    <CheckCircle size={14} /> Finalizar Intervención
                  </button>
                )}
                <button className="text-zinc-400 hover:text-zinc-200 transition-colors p-2 rounded-full hover:bg-white/10">
                  <MoreVertical size={20} />
                </button>
              </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 relative z-10">
              {loadingMessages ? (
                <div className="flex justify-center p-4">
                  <Loader2 className="animate-spin text-zinc-500" />
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center text-zinc-500 font-medium mt-10">No hay mensajes en este chat.</div>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  return (
                    <div key={msg.id} className={`flex items-start gap-3 max-w-[80%] ${isUser ? '' : 'self-end flex-row-reverse ml-auto'}`}>
                      <div className={`w-8 h-8 rounded-full shrink-0 mt-1 shadow-inner flex items-center justify-center ${isUser ? 'bg-zinc-700' : 'bg-emerald-900/50 border border-emerald-500/30'}`}>
                        {isUser ? <span className="text-xs text-zinc-400 font-bold">U</span> : <Bot size={16} className="text-emerald-400" />}
                      </div>
                      <div className={`p-4 rounded-2xl text-sm backdrop-blur-sm ${
                        isUser 
                          ? 'bg-zinc-800/80 rounded-tl-sm border border-zinc-700/80 text-zinc-200 shadow-[0_4px_15px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.05)]' 
                          : 'bg-gradient-to-br from-emerald-900/40 to-emerald-950/40 rounded-tr-sm border border-emerald-500/20 text-emerald-100 shadow-[0_4px_15px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(16,185,129,0.2)]'
                      }`}>
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                        <span className="text-[10px] opacity-40 mt-2 block text-right">
                          {new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className="p-4 bg-zinc-900/50 border-t border-zinc-800 shrink-0 relative z-10 backdrop-blur-md">
              <div className="bg-zinc-800/80 border border-zinc-700/80 rounded-xl p-2 focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/50 transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  className="w-full bg-transparent border-none focus:ring-0 text-zinc-200 text-sm placeholder-zinc-500 resize-none p-2 min-h-[60px] outline-none"
                  placeholder="Escriba un mensaje manual... (Enter para enviar)"
                  disabled={sending}
                ></textarea>
                <div className="flex justify-between items-center mt-2 px-2">
                  <div className="flex gap-2 text-zinc-500">
                    <button className="hover:text-zinc-300 transition-colors"><Paperclip size={18} /></button>
                    <button className="hover:text-zinc-300 transition-colors"><Smile size={18} /></button>
                  </div>
                  <button 
                    onClick={handleSendMessage}
                    disabled={sending || !inputMessage.trim()}
                    className="bg-gradient-to-b from-emerald-500 to-emerald-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:from-emerald-400 hover:to-emerald-500 transition-all flex items-center gap-2 shadow-[0_4px_10px_rgba(16,185,129,0.3),inset_0_1px_0_rgba(255,255,255,0.2)] active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                  >
                    {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Enviar <Send size={14} /></>}
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Column 3: Client Intelligence */}
      <aside className={`w-1/4 ${glassCardStyle}`}>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/[0.03] via-transparent to-transparent pointer-events-none"></div>

        {!selectedUser ? (
          <div className="flex-1 flex items-center justify-center p-5 relative z-10 opacity-50">
            <p className="text-sm font-medium text-slate-400 text-center">Selecciona un cliente para ver su inteligencia</p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-5 relative z-10 no-scrollbar">
            <h3 className="text-base font-bold text-slate-100 mb-4 tracking-wide">Inteligencia del cliente</h3>

            <div className="flex flex-col items-center text-center mb-4">
              <div className="w-20 h-20 rounded-full border-4 border-slate-800 shadow-[0_10px_25px_rgba(0,0,0,0.5),inset_0_2px_4px_rgba(255,255,255,0.1)] bg-gradient-to-br from-slate-600 to-slate-800 mb-3 relative overflow-hidden flex items-center justify-center font-bold text-3xl text-slate-300">
                <div className="absolute inset-0 bg-white/5"></div>
                {selectedUser.push_name ? selectedUser.push_name[0].toUpperCase() : selectedUser.phone_number.substring(0,1)}
              </div>
              <h4 className="text-base font-bold text-slate-100">{selectedUser.push_name || 'Desconocido'}</h4>
              <p className="text-xs text-slate-400 mt-1">Registrado el {new Date(selectedUser.created_at).toLocaleDateString()}</p>
            </div>

            <div className="space-y-3">
              {/* Session State Box */}
              <div className={`p-4 rounded-2xl border relative overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] ${
                selectedUser.session_mode === 'HUMAN' 
                  ? 'bg-gradient-to-br from-red-900/20 to-slate-900/50 border-red-500/20' 
                  : 'bg-gradient-to-br from-emerald-900/20 to-slate-900/50 border-emerald-500/20'
              }`}>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-2">Modo de Sesión</p>
                <div className="flex items-center gap-3">
                  <span className="text-2xl filter drop-shadow-md">
                    {selectedUser.session_mode === 'HUMAN' ? '👨‍💻' : '🤖'}
                  </span>
                  <span className={`text-base font-bold tracking-wide ${selectedUser.session_mode === 'HUMAN' ? 'text-red-400' : 'text-emerald-400'}`}>
                    {selectedUser.session_mode === 'HUMAN' ? 'Intervención Humana' : 'Control por IA'}
                  </span>
                </div>
              </div>

              {/* Status Box */}
              <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 px-4 py-3 rounded-2xl border border-slate-700/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] flex justify-between items-center">
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Bloqueado</p>
                <p className={`text-sm font-black tracking-tight ${selectedUser.is_blocked ? 'text-red-400' : 'text-emerald-400'}`}>
                  {selectedUser.is_blocked ? 'SÍ' : 'NO'}
                </p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
