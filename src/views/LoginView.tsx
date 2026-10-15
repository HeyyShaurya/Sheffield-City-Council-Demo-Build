import React, { useState } from 'react';
import { User } from '../types';
import { ROLE_LABELS } from '../store/sheffieldStore';

interface LoginViewProps {
  users: User[];
  onLogin: (userId: number, pin: string) => void;
  onExploreCareers: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ users, onLogin, onExploreCareers }) => {
  // First 10 users are primary personas as in Python backend
  const personas = users.slice(0, 10);
  const [selectedUserId, setSelectedUserId] = useState<number>(personas[0]?.id || 1);
  const [pin, setPin] = useState<string>('sheffield-demo');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      onLogin(Number(selectedUserId), pin);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="login-page">
      <div className="login-art">
        <div className="login-art-content">
          <div className="caps">PAYROLLCLOUD LIMITED / SOLUTION EXPERIENCE</div>
          <div className="hero-big">
            One connected
            <br />
            <em>employee journey.</em>
          </div>
          <p>
            Built around Sheffield City Council&apos;s six priority use cases, with visible controls, traceable decisions
            and working end-to-end flows.
          </p>
          <div className="orbit-cards">
            <span>Recruit</span>
            <span>Manage</span>
            <span>Pay</span>
            <span>Learn</span>
            <span>Analyse</span>
          </div>
          <div className="login-sub">Reference 100113345 &nbsp; | &nbsp; Private opportunity demonstration</div>
        </div>
      </div>

      <div className="login-form-wrap">
        <div className="login-form">
          <div className="logo large">
            <div className="logo-icon">SC</div>
            <div>
              <strong>Sheffield Connect</strong>
              <small>Connected people platform</small>
            </div>
          </div>
          <div className="eyebrow">INTERACTIVE SOLUTION DEMO</div>
          <h1>Welcome back</h1>
          <p className="muted">Select a demo persona to experience their permitted workplace journey.</p>

          {error && <div className="note error" style={{ marginBottom: 16 }}>{error}</div>}

          <form onSubmit={handleSubmit} className="form-stack">
            <label>
              Experience as
              <select
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(Number(e.target.value))}
                required
              >
                {personas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} - {ROLE_LABELS[p.role] || p.role} ({p.department})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Demo access code
              <input
                type="password"
                autoComplete="off"
                placeholder="Enter demo code"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                required
              />
            </label>

            <button className="btn primary full" type="submit">
              Enter workspace <span aria-hidden="true">&#8594;</span>
            </button>
          </form>

          <button
            onClick={onExploreCareers}
            className="btn subtle full"
            type="button"
            style={{ marginTop: 12 }}
          >
            Explore public careers portal
          </button>

          <div className="login-note">
            <strong>Demonstration environment</strong>
            <span>Invented people and transactions. No live Oracle, HMRC, Microsoft or email services are connected.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
