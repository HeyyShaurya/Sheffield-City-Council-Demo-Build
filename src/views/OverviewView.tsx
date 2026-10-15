import React from 'react';
import { User } from '../types';
import { store, fmt, ago } from '../store/sheffieldStore';
import { PageHead } from '../components/CommonUI';

interface OverviewViewProps {
  user: User;
  onNavigate: (page: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ user, onNavigate }) => {
  const stats = store.getDashboardStats(user);
  const firstName = user.name.split(' ')[0];

  const cards = [
    { label: 'People records', num: fmt(stats.headcount), foot: 'Synthetic sample, not entire workforce' },
    { label: 'Approvals pending', num: fmt(stats.pending_leave), foot: 'Updated from leave transactions' },
    { label: 'Assigned tasks', num: fmt(stats.open_tasks), foot: 'Actionable workflow assignments' },
    { label: 'Applications', num: fmt(stats.applications), foot: 'Applicant pipeline records' },
  ];

  const ways = [
    { page: 'leave', icon: '◔', title: 'Book and approve leave', desc: 'Employee to manager approval, audit and balance' },
    { page: 'org', icon: '☵', title: 'Explore organisation', desc: 'Manager spans, position attributes and FTE' },
    { page: 'recruit', icon: '▷', title: 'Recruit a new colleague', desc: 'Vacancy, candidate, interview, offer and onboarding' },
    { page: 'documents', icon: '▨', title: 'Manage employee records', desc: 'Upload, retention policy, archive and purge' },
    { page: 'tasks', icon: '☑', title: 'Complete an HR journey', desc: 'Task ownership, exceptions and audit trail' },
    { page: 'reports', icon: '◕', title: 'Explore workforce insights', desc: 'Filters, role-aware metrics and CSV export' },
  ];

  return (
    <div>
      <PageHead
        title="Your connected workplace"
        kicker="OVERVIEW / LIVE WORKSPACE"
        desc={`Welcome, ${firstName}. Every completed demo action updates the shared data model.`}
      />

      <div className="hero-strip">
        <div>
          <div className="caps">SHEFFIELD CITY COUNCIL / REFERENCE 100113345</div>
          <h2>From first application to employee success.</h2>
          <p>One role-aware experience. Live transactions, decisions and evidence across Sheffield&apos;s six priority journeys.</p>
        </div>
        <button className="btn" onClick={() => onNavigate('guide')} type="button">
          Start guided demo &rarr;
        </button>
      </div>

      <div className="grid four">
        {cards.map((c, i) => (
          <div key={i} className="card stat">
            <div className="stat-label">{c.label}</div>
            <div className="stat-num mono">{c.num}</div>
            <div className="stat-foot">
              <span className="stat-dot"></span>
              {c.foot}
            </div>
          </div>
        ))}
      </div>

      <div className="section-top" style={{ marginTop: 29 }}>
        <h2>Explore a complete journey</h2>
        <span>Six Sheffield demonstration use cases</span>
      </div>

      <div className="path-grid">
        {ways.map((w) => (
          <button
            key={w.page}
            className="path-card"
            onClick={() => onNavigate(w.page)}
            type="button"
          >
            <span className="path-icon">{w.icon}</span>
            <strong>{w.title}</strong>
            <span>{w.desc}</span>
          </button>
        ))}
      </div>

      <div className="grid two" style={{ marginTop: 20 }}>
        <div className="card">
          <div className="section-top">
            <h2>Recent activity</h2>
            <span>Audited actions</span>
          </div>
          <div className="timeline">
            {stats.activity.length ? (
              stats.activity.map((a) => (
                <div key={a.id} className="timeline-item">
                  <div className="timeline-bullet"></div>
                  <div>
                    <strong>
                      {a.actor} {a.action.replace(/-/g, ' ')}
                    </strong>
                    <div className="small muted">
                      {a.entity} #{a.entity_id}
                      {a.detail ? ` / ${a.detail}` : ''}
                    </div>
                    <small>{ago(a.created)}</small>
                  </div>
                </div>
              ))
            ) : (
              <div className="small muted">No activity recorded yet</div>
            )}
          </div>
        </div>

        <div className="card">
          <h2>Solution evidence snapshot</h2>
          <p className="card-sub">Proposal mapping from the submitted PME response</p>
          <div className="grid two">
            <div className="metric-teaser">
              <strong style={{ fontSize: 29 }}>47</strong>
              <div className="small muted">Process requirements</div>
            </div>
            <div className="metric-teaser">
              <strong style={{ fontSize: 29 }}>43 / 4</strong>
              <div className="small muted">Base / additional cost</div>
            </div>
            <div className="metric-teaser">
              <strong style={{ fontSize: 29 }}>6</strong>
              <div className="small muted">Priority scenarios</div>
            </div>
            <div className="metric-teaser">
              <strong style={{ fontSize: 29 }}>8,000</strong>
              <div className="small muted">Pricing population baseline</div>
            </div>
          </div>
          <div className="note attention" style={{ marginTop: 16 }}>
            <span className="warning-dot"></span>
            {stats.note}
          </div>
        </div>
      </div>
    </div>
  );
};
