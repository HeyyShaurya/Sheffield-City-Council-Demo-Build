import React from 'react';
import { User, Integration, IntegrationEvent, AuditEvent } from '../../types';
import { store, ago } from '../../store/sheffieldStore';
import { PageHead, StatusBadge } from '../../components/CommonUI';

interface AdminDashboardProps {
  user: User;
  onNavigate: (page: string) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ user, onNavigate }) => {
  const state = store.getState();
  const integrations: Integration[] = state.integrations;
  const events: IntegrationEvent[] = state.integration_events;
  const auditLogs: AuditEvent[] = state.audit;

  const handleTestEvent = (it: Integration) => {
    store.stageEvent(it.name, 'health-probe', it.id, { ping: 'ok', timestamp: new Date().toISOString() }, user.id);
  };

  return (
    <div className="view-container">
      <PageHead
        kicker="SYSTEM ADMINISTRATION &amp; INTEGRATION CONSOLE"
        title={`Administrator Workspace &bull; ${user.name}`}
        desc="Monitor enterprise ERP adapter health, inspect real-time transaction event streams, simulate fault handling, and review immutable audit compliance."
        actions={
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="btn primary"
              onClick={() => onNavigate('integrations')}
              type="button"
            >
              Integration Control Center
            </button>
            <button
              className="btn subtle"
              onClick={() => onNavigate('audit')}
              type="button"
            >
              Immutable Audit Evidence
            </button>
          </div>
        }
      />

      {/* Admin Metrics */}
      <div className="grid four" style={{ gap: 16, marginBottom: 24 }}>
        <div className="card" style={{ borderLeft: '4px solid #005A36' }}>
          <div className="kicker">MOCK ERP ADAPTERS</div>
          <div className="metric-huge mono" style={{ color: '#005A36' }}>
            {integrations.length} <span style={{ fontSize: 16, color: '#64748B' }}>active</span>
          </div>
          <div className="small muted" style={{ marginTop: 6 }}>
            Oracle, HMRC, Active Directory, LMS
          </div>
        </div>

        <div className="card" style={{ borderLeft: '4px solid #2D77C7' }}>
          <div className="kicker">EVENT STREAM QUEUED</div>
          <div className="metric-huge mono" style={{ color: '#2D77C7' }}>
            {events.length}
          </div>
          <div className="small muted" style={{ marginTop: 6 }}>
            Total simulated integration transactions
          </div>
        </div>

        <div className="card" style={{ borderLeft: '4px solid #D97706' }}>
          <div className="kicker">FAILED / DEAD-LETTER QUEUE</div>
          <div className="metric-huge mono" style={{ color: '#D97706' }}>
            {events.filter((e) => e.status === 'Failed').length}
          </div>
          <div className="small muted" style={{ marginTop: 6 }}>
            Retryable staging buffer
          </div>
        </div>

        <div className="card" style={{ borderLeft: '4px solid #102C50' }}>
          <div className="kicker">IMMUTABLE AUDIT LOGS</div>
          <div className="metric-huge mono" style={{ color: '#102C50' }}>
            {auditLogs.length}
          </div>
          <div className="small muted" style={{ marginTop: 6 }}>
            Continuous compliance records
          </div>
        </div>
      </div>

      {/* Main Grid: Adapter Health & Audit Feed */}
      <div className="grid two" style={{ gap: 24, marginBottom: 24 }}>
        {/* Integrations Health */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ margin: 0 }}>Enterprise Mock Adapters</h3>
            <button
              className="btn subtle small"
              onClick={() => onNavigate('integrations')}
              type="button"
            >
              Configure &rarr;
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {integrations.map((it) => (
              <div
                key={it.id}
                style={{
                  padding: 12,
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: 8,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <strong style={{ color: '#172C46' }}>{it.name}</strong>
                  <div className="micro muted" style={{ marginTop: 2 }}>
                    Method: {it.method} &bull; {it.description}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <StatusBadge value={it.status} />
                  <button
                    className="btn small subtle"
                    onClick={() => handleTestEvent(it)}
                    type="button"
                  >
                    Ping
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Audit Trail Stream */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ margin: 0 }}>Recent Audit Activity Stream</h3>
            <button
              className="btn subtle small"
              onClick={() => onNavigate('audit')}
              type="button"
            >
              Full Audit Trail &rarr;
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {auditLogs.slice(0, 5).map((log) => (
              <div
                key={log.id}
                style={{
                  padding: '10px 12px',
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: 6,
                  fontSize: 12,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong style={{ color: '#172C46' }}>{log.action}</strong>
                  <span className="micro muted">{ago(log.created)}</span>
                </div>
                <div className="micro muted" style={{ marginTop: 2 }}>
                  By: {log.actor} &bull; Target: {log.entity} #{log.entity_id} {log.detail ? `\u2022 ${log.detail}` : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
