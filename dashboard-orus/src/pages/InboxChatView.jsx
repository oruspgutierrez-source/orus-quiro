import { MoreVertical, Paperclip, Smile, Zap, Send, AlertCircle, Bot, Phone } from 'lucide-react';

export default function InboxChatView() {
  // Premium 3D Dark Card Style (columns 1 & 3)
  const glassCardStyle = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 border border-slate-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] flex flex-col backdrop-blur-md";
  const headerStyle = "p-4 border-b border-slate-700/50 bg-gradient-to-b from-white/5 to-transparent flex justify-between items-center";
  // Zinc dark palette — center chat column only
  const chatCardStyle = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] flex flex-col backdrop-blur-md";
  const chatHeaderStyle = "p-4 border-b border-zinc-700/50 bg-gradient-to-b from-white/5 to-transparent flex justify-between items-center";

  return (
    <div className="flex-1 flex overflow-hidden p-4 gap-4 bg-white">

      {/* Column 1: Active Chats List */}
      <aside className={`w-1/4 ${glassCardStyle}`}>
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.02] to-transparent pointer-events-none"></div>

        <div className={headerStyle}>
          <h3 className="font-semibold text-slate-100 tracking-wide">Chats activos</h3>
        </div>
        <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-2 relative z-10">

          {/* Chat Item: Human Req */}
          <div className="flex items-start gap-3 p-3 rounded-xl bg-gradient-to-br from-red-500/10 to-red-900/10 cursor-pointer border border-red-500/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] hover:border-red-500/40 transition-all">
            <div className="w-10 h-10 rounded-full bg-slate-700 shrink-0 shadow-inner"></div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-baseline mb-1">
                <h4 className="text-sm text-slate-200 font-semibold truncate">Sarah Jenkins</h4>
                <span className="text-xs text-red-400">2 metros</span>
              </div>
              <p className="text-sm text-slate-400 truncate">¡Necesito hablar con un...</p>
              <span className="inline-flex items-center gap-1 mt-2 text-[10px] text-red-300 bg-red-500/20 px-2 py-0.5 rounded-md border border-red-500/30 font-medium">
                <AlertCircle size={10} /> Requisitos humanos
              </span>
            </div>
          </div>

          {/* Chat Item: AI Active */}
          <div className="flex items-start gap-3 p-3 rounded-xl hover:bg-white/5 cursor-pointer transition-all border border-transparent hover:border-white/10 hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
            <div className="w-10 h-10 rounded-full bg-slate-700 shrink-0 relative shadow-inner">
              <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-slate-900 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-baseline mb-1">
                <h4 className="text-sm text-slate-200 font-semibold truncate">Marcus Cole</h4>
                <span className="text-xs text-slate-500">15 metros</span>
              </div>
              <p className="text-sm text-slate-400 truncate">Me parece bien, proced...</p>
              <span className="inline-flex items-center gap-1 mt-2 text-[10px] text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-md border border-emerald-500/30 font-medium">
                <Bot size={10} /> IA activa
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Column 2: Live Chat Thread */}
      <main className={`flex-1 ${chatCardStyle}`}>
        <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none"></div>

        {/* Chat Header */}
        <div className={`${chatHeaderStyle} shrink-0`}>
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 rounded-full bg-zinc-700 border border-zinc-600 shadow-inner"></div>
            <div>
              <h2 className="text-lg font-bold text-zinc-100 tracking-wide">Sarah Jenkins</h2>
              <p className="text-xs text-zinc-400 flex items-center gap-1 font-medium">
                <Phone size={12} className="text-zinc-500" /> +1 (555) 019-2834
              </p>
            </div>
          </div>
          <button className="text-zinc-400 hover:text-zinc-200 transition-colors p-2 rounded-full hover:bg-white/10">
            <MoreVertical size={20} />
          </button>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 relative z-10">
          <div className="text-center">
            <span className="text-xs text-zinc-500 font-medium bg-zinc-800/80 px-3 py-1 rounded-full border border-zinc-700/50">Hoy, 10:42 a. m.</span>
          </div>

          {/* User Message */}
          <div className="flex items-start gap-3 max-w-[80%]">
            <div className="w-8 h-8 rounded-full bg-zinc-700 shrink-0 mt-1 shadow-inner"></div>
            <div className="bg-zinc-800/80 p-4 rounded-2xl rounded-tl-sm border border-zinc-700/80 text-zinc-200 text-sm shadow-[0_4px_15px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.05)] backdrop-blur-sm">
              <p>Hola, estaba revisando mi última factura y creo que hay un error.</p>
            </div>
          </div>

          {/* AI Message */}
          <div className="flex items-start gap-3 max-w-[80%] self-end flex-row-reverse ml-auto">
            <div className="w-8 h-8 rounded-full bg-emerald-900/50 border border-emerald-500/30 flex items-center justify-center shrink-0 mt-1 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
              <Bot size={16} className="text-emerald-400" />
            </div>
            <div className="bg-gradient-to-br from-emerald-900/40 to-emerald-950/40 p-4 rounded-2xl rounded-tr-sm border border-emerald-500/20 text-emerald-100 text-sm shadow-[0_4px_15px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(16,185,129,0.2)] backdrop-blur-sm">
              <p>Hola Sarah. Con mucho gusto te ayudaré con eso. Permíteme consultar tu historial de facturación reciente.</p>
            </div>
          </div>
        </div>

        {/* Chat Input */}
        <div className="p-4 bg-zinc-900/50 border-t border-zinc-800 shrink-0 relative z-10 backdrop-blur-md">
          <div className="bg-zinc-800/80 border border-zinc-700/80 rounded-xl p-2 focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/50 transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]">
            <textarea
              className="w-full bg-transparent border-none focus:ring-0 text-zinc-200 text-sm placeholder-zinc-500 resize-none p-2 min-h-[60px] outline-none"
              placeholder="Escriba un mensaje manual..."
            ></textarea>
            <div className="flex justify-between items-center mt-2 px-2">
              <div className="flex gap-2 text-zinc-500">
                <button className="hover:text-zinc-300 transition-colors"><Paperclip size={18} /></button>
                <button className="hover:text-zinc-300 transition-colors"><Smile size={18} /></button>
                <button className="hover:text-zinc-300 transition-colors"><Zap size={18} /></button>
              </div>
              <button className="bg-gradient-to-b from-emerald-500 to-emerald-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:from-emerald-400 hover:to-emerald-500 transition-all flex items-center gap-2 shadow-[0_4px_10px_rgba(16,185,129,0.3),inset_0_1px_0_rgba(255,255,255,0.2)] active:scale-95">
                Enviar <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Column 3: Client Intelligence */}
      <aside className={`w-1/4 ${glassCardStyle}`}>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/[0.03] via-transparent to-transparent pointer-events-none"></div>

        <div className="flex-1 overflow-y-auto p-5 relative z-10 no-scrollbar">
          <h3 className="text-base font-bold text-slate-100 mb-4 tracking-wide">Inteligencia del cliente</h3>

          <div className="flex flex-col items-center text-center mb-4">
            <div className="w-20 h-20 rounded-full border-4 border-slate-800 shadow-[0_10px_25px_rgba(0,0,0,0.5),inset_0_2px_4px_rgba(255,255,255,0.1)] bg-gradient-to-br from-slate-600 to-slate-800 mb-3 relative overflow-hidden">
              <div className="absolute inset-0 bg-white/5"></div>
            </div>
            <h4 className="text-base font-bold text-slate-100">Sarah Jenkins</h4>
            <p className="text-xs text-slate-400 mt-1">Cliente desde agosto de 2022</p>
          </div>

          <div className="space-y-3">
            {/* Sentiment Box */}
            <div className="bg-gradient-to-br from-red-900/20 to-slate-900/50 p-4 rounded-2xl border border-red-500/20 relative overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
              <div className="absolute -top-10 -right-10 w-24 h-24 bg-red-500/10 blur-2xl rounded-full"></div>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-2">Sentimiento Actual</p>
              <div className="flex items-center gap-3">
                <span className="text-2xl filter drop-shadow-md">😠</span>
                <span className="text-base text-red-400 font-bold tracking-wide">Frustrado</span>
              </div>
              <p className="text-xs text-slate-500 mt-3 border-t border-slate-700/50 pt-2 font-medium">Detectado en función de los mensajes recientes.</p>
            </div>

            {/* Total Spent Box */}
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 px-4 py-2 rounded-2xl border border-slate-700/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Total Gastado</p>
              <p className="text-xl text-slate-100 font-black tracking-tight">$1,249.50</p>
            </div>
          </div>
        </div>
      </aside>

    </div>
  );
}
