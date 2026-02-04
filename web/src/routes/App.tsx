import React from 'react';
import { Routes, Route, useLocation, Navigate, Link } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAuth } from '../auth';
import { toggleTheme } from '../theme';

import LoginPage from './LoginPage';
import ForceChangePassword from './ForceChangePassword';
import CompaniesPage from './CompaniesPage';
import CompanyTasksPage from './CompanyTasksPage';
import TaskDetailPage from './TaskDetailPage';
import AdminHome from './admin/AdminHome';
import AdminUsers from './admin/AdminUsers';
import AdminSignUp from './admin/AdminSignUp';
import AdminTasks from './admin/AdminTasks';
import AdminCompanies from './admin/AdminCompanies';
import StatsHome from './stats/StatsHome';

function Shell({ children }: { children: React.ReactNode }) {
  const { me, logout } = useAuth();
  return (
    <div className="container">
      <div className="nav">
        <div className="row" style={{gap:12}}>
          <div className="brand"><Link to="/">Salkhorian Design Task Scheduler</Link></div>
          {me && (me.role === 'admin' || me.role === 'super_admin') && (
            <div className="row" style={{gap:8}}>
              <Link className="badge" to="/administrator">Admin</Link>
              <Link className="badge" to="/stats">Stats</Link>
            </div>
          )}
        </div>
        <div className="right">
          <button className="btn" onClick={toggleTheme}>Theme</button>
          {me ? (
            <>
              <span className="muted" style={{fontSize: 13}}>{me.username} · {me.role}</span>
              <button className="btn" onClick={logout}>Logout</button>
            </>
          ) : (
            <Link className="btn" to="/login">Login</Link>
          )}
        </div>
      </div>
      <div style={{height: 14}} />
      {children}
    </div>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  if (loading) return <Shell><div className="card">Loading...</div></Shell>;
  if (!me) return <Navigate to="/login" replace />;
  if (me.must_change_password) return <Navigate to="/force_change_password" replace />;
  return <Shell>{children}</Shell>;
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  if (loading) return <Shell><div className="card">Loading...</div></Shell>;
  if (!me) return <Navigate to="/login" replace />;
  if (me.must_change_password) return <Navigate to="/force_change_password" replace />;
  if (!(me.role === 'admin' || me.role === 'super_admin')) return <Shell><div className="card">Forbidden</div></Shell>;
  return <Shell>{children}</Shell>;
}

export default function App() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/login" element={<Shell><LoginPage /></Shell>} />
        <Route path="/force_change_password" element={<Shell><ForceChangePassword /></Shell>} />

        <Route path="/" element={<RequireAuth><Page><CompaniesPage /></Page></RequireAuth>} />
        <Route path="/company/:companySlug" element={<RequireAuth><Page><CompanyTasksPage /></Page></RequireAuth>} />
        <Route path="/company/:companySlug/tasks/:taskCode" element={<RequireAuth><Page><TaskDetailPage /></Page></RequireAuth>} />

        <Route path="/administrator" element={<RequireAdmin><Page><AdminHome /></Page></RequireAdmin>} />
        <Route path="/administrator/users" element={<RequireAdmin><Page><AdminUsers /></Page></RequireAdmin>} />
        <Route path="/administrator/sign_up" element={<RequireAdmin><Page><AdminSignUp /></Page></RequireAdmin>} />
        <Route path="/administrator/tasks" element={<RequireAdmin><Page><AdminTasks /></Page></RequireAdmin>} />
        <Route path="/administrator/companies" element={<RequireAdmin><Page><AdminCompanies /></Page></RequireAdmin>} />

        <Route path="/stats" element={<RequireAdmin><Page><StatsHome /></Page></RequireAdmin>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

function Page({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.18 }}
    >
      {children}
    </motion.div>
  );
}
