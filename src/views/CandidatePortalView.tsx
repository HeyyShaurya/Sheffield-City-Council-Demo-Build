import React, { useState } from 'react';
import { User, Vacancy } from '../types';
import { store, ago, isodays } from '../store/sheffieldStore';
import { PageHead, StatusBadge } from '../components/CommonUI';
import { Modal } from '../components/Modal';

interface CandidatePortalViewProps {
  user: User | null;
  onExitPublic: () => void;
  onToast: (msg: string, isError?: boolean) => void;
}

const STAGES = [
  'Applied',
  'Shortlisted',
  'Interview Scheduled',
  'Interview Completed',
  'Offered',
  'Offer Accepted',
  'Checks Complete',
  'Onboarded',
];

export const CandidatePortalView: React.FC<CandidatePortalViewProps> = ({ user, onExitPublic, onToast }) => {
  const publishedVacancies = store.getVacancies(null).filter((v) => v.status === 'Published');
  const candidateToken = store.candidateToken;
  const currentApp = candidateToken ? store.getCandidateByToken(candidateToken) : null;
  const candidateMessages = candidateToken ? store.getCandidateMessages(candidateToken) : [];

  // Apply modal
  const [applyVac, setApplyVac] = useState<Vacancy | null>(null);
  const [candidateName, setCandidateName] = useState('Maya Evans');
  const [candidateEmail, setCandidateEmail] = useState('maya.demo@example.com');
  const [candidateStatement, setCandidateStatement] = useState(
    'Experienced community support specialist committed to person-centred care, safeguarding best practices, and neighbourhood collaboration.'
  );
  const [candidateCover, setCandidateCover] = useState(
    'I am writing to express my strong enthusiasm for joining Sheffield City Council. My background in local frontline casework aligns directly with the Council’s objectives.'
  );
  const [candidateSource, setCandidateSource] = useState('Council careers');

  // Interview Schedule modal
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [interviewSlot, setInterviewSlot] = useState(`${isodays(7)}T11:00`);
  const [interviewType, setInterviewType] = useState<'Video' | 'In-person'>('Video');

  // Lookup token form
  const [lookupInput, setLookupInput] = useState(candidateToken);

  const handleApplySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!applyVac) return;
    try {
      const app = store.applyCandidate(applyVac.id, {
        name: candidateName,
        email: candidateEmail,
        statement: candidateStatement,
        cover_letter: candidateCover,
        source: candidateSource,
      });
      onToast(`Application received: #${app.id}`);
      setApplyVac(null);
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handleScheduleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!candidateToken) return;
    try {
      store.candidateScheduleInterview(candidateToken, interviewSlot, interviewType);
      onToast('Interview preference saved; calendar event queued');
      setIsScheduleOpen(false);
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handleWithdraw = () => {
    if (!window.confirm('Withdraw this application? This cannot be undone.')) return;
    try {
      store.candidateWithdraw(candidateToken);
      onToast('Application withdrawn');
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    const token = lookupInput.trim();
    if (!token) return;
    const found = store.getCandidateByToken(token);
    if (!found) {
      onToast('Application access code not found', true);
    } else {
      store.setCandidateToken(token);
      onToast(`Application found: ${found.stage}`);
    }
  };

  const handleClearCandidate = () => {
    store.setCandidateToken('');
    setLookupInput('');
    onToast('Candidate session cleared');
  };

  const currentStageIndex = currentApp ? STAGES.indexOf(currentApp.stage) : -1;

  return (
    <div>
      <PageHead
        title="Your next role starts here."
        kicker="SHEFFIELD / PUBLIC CANDIDATE EXPERIENCE"
        desc="Clear applications, transparent progress and self-selected interviews in a mobile-friendly experience."
        actions={
          <button className="btn ghost" onClick={onExitPublic} type="button">
            {user ? 'Return to workspace' : 'Staff sign in'}
          </button>
        }
      />

      <div className="hero-strip">
        <div>
          <h2>Make a difference across Sheffield.</h2>
          <p>Explore service opportunities and follow each step from application to offer.</p>
        </div>
        <span style={{ fontSize: 34, opacity: 0.7 }}>☆</span>
      </div>

      {/* Tracker Card if Candidate Token Found */}
      {currentApp && (
        <>
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="row space">
              <div>
                <div className="eyebrow">YOUR APPLICATION TRACKER</div>
                <h3>{currentApp.vacancy}</h3>
                <p className="small muted">
                  Applicant: <strong>{currentApp.name}</strong> ({currentApp.email})
                </p>
              </div>
              <StatusBadge value={currentApp.stage} />
            </div>

            <div className="steps" style={{ marginTop: 18 }}>
              {STAGES.map((s, idx) => (
                <span
                  key={s}
                  className={`step-pill ${currentStageIndex >= idx ? 'done' : ''}`}
                >
                  {s}
                </span>
              ))}
            </div>

            {['Shortlisted', 'Interview Scheduled'].includes(currentApp.stage) && (
              <div className="row wrap" style={{ marginTop: 16 }}>
                <button
                  className="btn primary small"
                  onClick={() => setIsScheduleOpen(true)}
                  type="button"
                >
                  {currentApp.interview_slot ? 'Reschedule interview' : 'Choose interview slot'}
                </button>
                <span className="small muted">
                  {currentApp.interview_slot
                    ? `${ago(currentApp.interview_slot)} / ${currentApp.interview_type}`
                    : 'Choose a future time for interview'}
                </span>
              </div>
            )}

            <div className="row wrap" style={{ marginTop: 16 }}>
              {!['Onboarded', 'Rejected', 'Withdrawn'].includes(currentApp.stage) && (
                <button
                  className="btn small danger"
                  onClick={handleWithdraw}
                  type="button"
                >
                  Withdraw application
                </button>
              )}
              <button
                className="btn small ghost"
                onClick={handleClearCandidate}
                type="button"
              >
                Track a different application
              </button>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <h3>Updates &amp; correspondence</h3>
            <p className="small muted">
              Candidate-only portal inbox; any message from a recruiter appears below without claiming external email delivery.
            </p>

            {candidateMessages.length ? (
              candidateMessages.map((m) => (
                <div
                  key={m.id}
                  style={{ padding: '12px 0', borderBottom: '1px solid #e5edf4' }}
                >
                  <div className="row space">
                    <strong>{m.title}</strong>
                    <span className="micro muted">{ago(m.created)}</span>
                  </div>
                  <p>{m.body}</p>
                </div>
              ))
            ) : (
              <p className="small muted" style={{ marginTop: 12 }}>
                No correspondence yet.
              </p>
            )}
          </div>
        </>
      )}

      {/* Vacancies List */}
      <div className="section-top">
        <h2>Open opportunities</h2>
        <span>Published roles only</span>
      </div>

      <div className="grid two">
        {publishedVacancies.length ? (
          publishedVacancies.map((v) => (
            <div key={v.id} className="card">
              <div className="row space">
                <div className="eyebrow">{v.department}</div>
                <StatusBadge value={v.status} />
              </div>
              <h2>{v.title}</h2>
              <p className="small muted">
                {v.location} &nbsp; / &nbsp; {v.grade} &nbsp; / &nbsp; {v.salary}
              </p>
              <p style={{ minHeight: 50 }}>{v.summary}</p>
              <div className="row space" style={{ marginTop: 19 }}>
                <span className="small muted">Closes {v.closing}</span>
                <button
                  className="btn primary small"
                  onClick={() => setApplyVac(v)}
                  type="button"
                >
                  Apply for role &rarr;
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="card">There are no published vacancies at this time.</div>
        )}
      </div>

      {/* Candidate Code Lookup Form */}
      <div className="card" style={{ marginTop: 20 }}>
        <h3>Already applied?</h3>
        <p className="card-sub">Enter the secure application tracking token you received after submitting.</p>
        <form onSubmit={handleLookup} className="input-row">
          <label>
            Application access code
            <input
              value={lookupInput}
              onChange={(e) => setLookupInput(e.target.value)}
              placeholder="Paste your application token"
              required
            />
          </label>
          <button className="btn light" type="submit">
            View progress
          </button>
        </form>
      </div>

      {/* Apply Modal */}
      {applyVac && (
        <Modal
          isOpen={true}
          onClose={() => setApplyVac(null)}
          title={`Apply - ${applyVac.title}`}
          intro="Submit an application, then save the token to track progress and schedule interviews."
        >
          <form onSubmit={handleApplySubmit} className="form-stack">
            <div className="field-grid">
              <label>
                Full name
                <input
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  placeholder="e.g. Maya Evans"
                  required
                />
              </label>

              <label>
                Email address
                <input
                  type="email"
                  value={candidateEmail}
                  onChange={(e) => setCandidateEmail(e.target.value)}
                  placeholder="maya@example.com"
                  required
                />
              </label>

              <label className="wide">
                Personal statement
                <textarea
                  value={candidateStatement}
                  onChange={(e) => setCandidateStatement(e.target.value)}
                  maxLength={2000}
                  placeholder="How do your skills match this role?"
                  required
                />
              </label>

              <label className="wide">
                Cover letter {applyVac.cover_required ? '(required)' : '(optional)'}
                <textarea
                  value={candidateCover}
                  onChange={(e) => setCandidateCover(e.target.value)}
                  maxLength={2000}
                  placeholder="Introduce yourself to the selection panel"
                  required={applyVac.cover_required}
                />
              </label>

              <label className="wide">
                Application source
                <select
                  value={candidateSource}
                  onChange={(e) => setCandidateSource(e.target.value)}
                >
                  <option value="Council careers">Council careers</option>
                  <option value="External job board">External job board</option>
                  <option value="Referral">Referral</option>
                </select>
              </label>
            </div>

            <div className="form-actions">
              <button className="btn ghost" type="button" onClick={() => setApplyVac(null)}>
                Cancel
              </button>
              <button type="submit" className="btn primary">
                Submit application
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Interview Slot Modal */}
      <Modal
        isOpen={isScheduleOpen}
        onClose={() => setIsScheduleOpen(false)}
        title="Choose your interview slot"
        intro="You can return and reschedule while the application is in the interview stage."
      >
        <form onSubmit={handleScheduleSubmit} className="form-stack">
          <label>
            Interview time
            <input
              type="datetime-local"
              value={interviewSlot}
              onChange={(e) => setInterviewSlot(e.target.value)}
              required
            />
          </label>

          <label>
            Interview format
            <select
              value={interviewType}
              onChange={(e) => setInterviewType(e.target.value as 'Video' | 'In-person')}
            >
              <option value="Video">Video</option>
              <option value="In-person">In-person</option>
            </select>
          </label>

          <div className="form-actions">
            <button className="btn ghost" type="button" onClick={() => setIsScheduleOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn primary">
              Confirm interview
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
