import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, LineChart, Users, Settings, Terminal, Shield, Network, Bell, WifiHigh, CircleUserRound, Search, HelpCircle, LogOut, FileImage } from 'lucide-react';
import clsx from 'clsx';

function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-900 font-public-sans text-sm">
      {/* Sidebar */}
      <nav className="w-64 bg-slate-950 flex flex-col z-50 flex-shrink-0 shadow-[10px_0_30px_rgba(0,0,0,0.5)]">
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center overflow-hidden shrink-0">
            {/* Avatar placeholder */}
            <div className="text-emerald-500 font-bold">OA</div>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-emerald-400">Orus-quiro</h1>
            <p className="text-xs text-slate-500 font-medium mt-0.5">Command Center</p>
          </div>
        </div>

        <div className="flex-1 py-6 flex flex-col gap-1 overflow-y-auto no-scrollbar">
          <NavItem to="/dashboard" icon={LayoutDashboard} label="Dashboard" />
          <NavItem to="/chat" icon={MessageSquare} label="Inbox Chat" />
          <NavItem to="/calendar" icon={LineChart} label="Calendar" />
          <NavItem to="/logs" icon={Terminal} label="System Logs" />
          <NavItem to="/biometria" icon={FileImage} label="Biometría" />
          <NavItem to="/network" icon={Network} label="Network" disabled />
          <NavItem to="/settings" icon={Settings} label="Settings" disabled />
        </div>

        <div className="p-6 border-t border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full border border-slate-700 bg-slate-800 flex items-center justify-center text-slate-300">
               <CircleUserRound size={20} />
            </div>
            <div className="flex flex-col">
              <span className="font-medium text-slate-200">Admin User</span>
              <span className="text-[10px] text-slate-500">Active</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content Wrapper */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="relative overflow-hidden backdrop-blur-xl h-16 border-b border-white/[0.06] flex justify-between items-center px-6 z-40 sticky top-0 shrink-0 shadow-[0_4px_20px_rgba(0,0,0,0.4)]" style={{ background: 'linear-gradient(to right, #04050a 0%, #04050a 5%, #222222 30%, #0c0e12 55%, #0c0e12f2 100%)' }}>
          {/* Top edge highlight */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/[0.08] to-transparent pointer-events-none" />

          <div className="flex items-center w-1/3 -ml-6 h-full">
            <div className="h-9 flex items-center pl-10 w-[760px] bg-gradient-to-r from-[#1a1a1a] via-[#0c0e12] via-80% to-transparent">
              <h2 className="text-sm font-medium text-[#d4a017] tracking-widest whitespace-nowrap">Camino del Escultor</h2>
            </div>
          </div>
          
          <div className="flex flex-1 max-w-md justify-center">
            <div className="relative w-full group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-emerald-400 transition-colors z-10" size={16} />
              <input 
                type="text" 
                placeholder="Buscar registros, módulos..." 
                className="w-full bg-white/[0.06] backdrop-blur-md border border-white/[0.1] rounded-full py-2 pl-10 pr-5 text-slate-200 text-sm focus:outline-none focus:border-emerald-500/50 focus:bg-white/[0.1] focus:shadow-[0_0_20px_rgba(16,185,129,0.15),inset_0_1px_0_rgba(255,255,255,0.08)] transition-all duration-300 placeholder:text-slate-500 shadow-[inset_0_1px_0_rgba(255,255,255,0.06),0_1px_3px_rgba(0,0,0,0.3)]"
              />
              {/* Frosted glass shimmer */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/[0.03] to-transparent pointer-events-none" />
            </div>
          </div>

          <div className="flex items-center gap-1 w-1/3 justify-end">
            <button className="p-2.5 text-slate-400 hover:text-emerald-400 transition-all rounded-full hover:bg-white/[0.06] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] relative">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full shadow-[0_0_6px_rgba(239,68,68,0.7)]"></span>
            </button>
            <button className="p-2.5 text-slate-400 hover:text-emerald-400 transition-all rounded-full hover:bg-white/[0.06] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <WifiHigh size={20} />
            </button>
            <button className="p-2.5 text-slate-400 hover:text-emerald-400 transition-all rounded-full hover:bg-white/[0.06] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <CircleUserRound size={20} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-hidden bg-slate-900 relative flex flex-col">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function NavItem({ to, icon: Icon, label, disabled }) {
  if (disabled) {
    return (
      <div className="px-6 py-3 flex items-center gap-3 text-slate-600 cursor-not-allowed opacity-50">
        <Icon size={20} />
        <span>{label}</span>
      </div>
    );
  }

  return (
    <NavLink
      to={to}
      className={({ isActive }) => clsx(
        "px-6 py-3 flex items-center gap-3 transition-colors duration-200",
        isActive 
          ? "bg-slate-900 text-emerald-400 border-r-2 border-emerald-400 font-semibold opacity-100" 
          : "text-slate-500 hover:text-slate-200 hover:bg-slate-900 opacity-80"
      )}
    >
      <Icon size={20} />
      <span>{label}</span>
    </NavLink>
  );
}

export default AppLayout;
