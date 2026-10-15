import React from 'react';
import { User, Role } from '../types';
import { SheffieldLogo } from './SheffieldLogo';

export const NAV_ITEMS = [
  { key: 'overview', title: 'Dashboard', icon: '▦' },
  { key: 'profile', title: 'My profile', icon: '👤' },
  { key: 'leave', title: 'Absence & leave', icon: '◔' },
  { key: 'time', title: 'Time & attendance', icon: '⏱' },
  { key: 'org', title: 'Organisation', icon: '☵' },
  { key: 'recruit', title: 'Recruitment & talent', icon: '▷' },
  { key: 'documents', title: 'Document records', icon: '▨' },
  { key: 'tasks', title: 'HR journeys & tasks', icon: '☑' },
  { key: 'learning', title: 'Learning hub', icon: '☆' },
  { key: 'payroll', title: 'Payroll & payslips', icon: '£' },
  { key: 'reports', title: 'Workforce insights', icon: '◕' },
  { key: 'optional', title: 'Modernisations & claims', icon: '⚙' },
  { key: 'integrations', title: 'Integration control', icon: '⇄' },
  { key: 'messages', title: 'Private messaging', icon: '✉' },
];

export const NAV_DEMO_ITEMS = [
  { key: 'guide', title: 'Demo walkthrough', icon: '▶' },
  { key: 'matrix', title: 'Requirements matrix', icon: '▥' },
  { key: 'audit', title: 'Audit evidence', icon: '≡' },
];

// Strict role-based permissions to guarantee tailored experience per persona
const PERMISSIONS: Record<string, Role[]> = {
  overview: ['employee', 'manager', 'hr', 'payroll', 'learning', 'service', 'admin', 'recruiter'],
  profile: ['employee', 'manager', 'hr', 'payroll', 'learning', 'service', 'admin', 'recruiter'],
  leave: ['employee', 'manager', 'hr', 'service', 'payroll'],
  time: ['employee', 'manager', 'payroll'],
  org: ['manager', 'hr', 'service', 'recruiter', 'admin'],
  recruit: ['recruiter', 'manager', 'hr', 'service'],
  documents: ['hr', 'recruiter', 'admin', 'payroll'],
  tasks: ['hr', 'manager', 'recruiter', 'employee'],
  learning: ['employee', 'manager', 'hr', 'learning'],
  payroll: ['payroll', 'employee'], // Payroll runs it, employees view their own payslips
  reports: ['manager', 'service', 'hr', 'payroll', 'recruiter', 'admin'],
  optional: ['hr', 'service', 'admin', 'employee'], // Expenses and Casework
  integrations: ['admin', 'hr'],
  messages: ['employee', 'manager', 'hr', 'payroll', 'learning', 'service', 'admin', 'recruiter'],
  guide: ['employee', 'manager', 'hr', 'payroll', 'learning', 'service', 'admin', 'recruiter'],
  matrix: ['manager', 'hr', 'payroll', 'service', 'admin', 'recruiter'],
  audit: ['admin', 'hr', 'service', 'payroll'],
};

export function canAccess(page: string, role?: Role): boolean {
  if (!role) return false;
  const allowed = PERMISSIONS[page];
  return !allowed || allowed.includes(role);
}

interface SidebarProps {
  user: User;
  currentPage: string;
  onNavigate: (page: string) => void;
  onSwitchPersona: () => void;
  isOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  user,
  currentPage,
  onNavigate,
  onSwitchPersona,
  isOpen,
  onCloseMobile,
}) => {
  const handleItemClick = (page: string) => {
    onNavigate(page);
    onCloseMobile();
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`} id="sidebar">
      <div className="brand" style={{ padding: '24px 20px 20px' }}>
        <SheffieldLogo size="md" variant="white" subText="Sheffield Connect" />
      </div>

      <div className="workspace-tag" style={{ margin: '0 16px 20px', background: '#0B3322', borderColor: '#17593B' }}>
        <span className="pulse" style={{ background: '#55E59C' }}></span> Connected People Platform
      </div>

      <div className="navscroll">
        <div className="nav-group-label">WORKSPACE &bull; {user.role.toUpperCase()}</div>
        <nav aria-label="Main navigation">
          {NAV_ITEMS.filter((item) => canAccess(item.key, user.role)).map((item) => (
            <button
              key={item.key}
              type="button"
              className={`navlink ${currentPage === item.key ? 'active' : ''}`}
              onClick={() => handleItemClick(item.key)}
            >
              <span className="nav-symbol">{item.icon}</span>
              {item.title}
            </button>
          ))}
        </nav>

        <div className="nav-group-label">DEMONSTRATION</div>
        <nav aria-label="Demonstration navigation">
          {NAV_DEMO_ITEMS.filter((item) => canAccess(item.key, user.role)).map((item) => (
            <button
              key={item.key}
              type="button"
              className={`navlink ${currentPage === item.key ? 'active' : ''}`}
              onClick={() => handleItemClick(item.key)}
            >
              <span className="nav-symbol">{item.icon}</span>
              {item.title}
            </button>
          ))}
        </nav>
      </div>

      <div className="sidebar-footer">
        <div className="foot-card" style={{ background: '#0D3826', borderColor: '#17593B' }}>
          <div>Sheffield City Council</div>
          <strong>HR, Payroll &amp; Learning</strong>
          <small>Reference 100113345</small>
        </div>
        <button
          className="sidebar-switch"
          onClick={onSwitchPersona}
          type="button"
        >
          ⇄ &nbsp; Change persona
        </button>
      </div>
    </aside>
  );
};
