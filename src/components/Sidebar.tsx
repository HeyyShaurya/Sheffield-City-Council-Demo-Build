import React from 'react';
import { User } from '../types';

export const NAV_ITEMS = [
  { key: 'overview', title: 'Overview', icon: '▦' },
  { key: 'profile', title: 'My profile', icon: '👤' },
  { key: 'leave', title: 'Absence & leave', icon: '◔' },
  { key: 'time', title: 'Time & attendance', icon: '⏱' },
  { key: 'org', title: 'Organisation', icon: '☵' },
  { key: 'recruit', title: 'Recruitment & onboarding', icon: '▷' },
  { key: 'documents', title: 'Document records', icon: '▨' },
  { key: 'tasks', title: 'HR journeys & tasks', icon: '☑' },
  { key: 'learning', title: 'Learning hub', icon: '☆' },
  { key: 'payroll', title: 'Payroll & payslips', icon: '£' },
  { key: 'reports', title: 'Workforce insights', icon: '◕' },
  { key: 'optional', title: 'Optional capabilities', icon: '⚙' },
  { key: 'integrations', title: 'Integration control', icon: '⇄' },
  { key: 'messages', title: 'Private messaging', icon: '✉' },
];

export const NAV_DEMO_ITEMS = [
  { key: 'guide', title: 'Demo walkthrough', icon: '▶' },
  { key: 'matrix', title: 'Requirements matrix', icon: '▥' },
  { key: 'audit', title: 'Audit evidence', icon: '≡' },
];

const PERMISSIONS: Record<string, string[]> = {
  profile: [],
  time: [],
  leave: [],
  org: [],
  recruit: [],
  documents: [],
  tasks: [],
  learning: [],
  payroll: [],
  reports: ['manager', 'service', 'hr', 'payroll', 'recruiter', 'learning', 'admin'],
  optional: [],
  integrations: ['admin', 'hr'],
  messages: [],
  guide: [],
  matrix: [],
  audit: ['admin', 'hr', 'service', 'payroll'],
};

export function canAccess(page: string, role?: string): boolean {
  if (!role) return false;
  const allowed = PERMISSIONS[page];
  return !allowed || allowed.length === 0 || allowed.includes(role);
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
      <div className="brand">
        <div className="logo-icon">SC</div>
        <div>
          <strong>Sheffield Connect</strong>
          <span>PayrollCloud Limited</span>
        </div>
      </div>

      <div className="workspace-tag">
        <span className="pulse"></span> Opportunity demonstrator
      </div>

      <div className="navscroll">
        <div className="nav-group-label">WORKSPACE</div>
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
        <div className="foot-card">
          <div>Sheffield City Council</div>
          <strong>HR &amp; Payroll modernisation</strong>
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
