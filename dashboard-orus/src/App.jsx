import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import DashboardView from './pages/DashboardView';
import SystemLogsView from './pages/SystemLogsView';
import CalendarView from './pages/CalendarView';
import InboxChatView from './pages/InboxChatView';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardView />} />
          <Route path="logs" element={<SystemLogsView />} />
          <Route path="calendar" element={<CalendarView />} />
          <Route path="chat" element={<InboxChatView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
