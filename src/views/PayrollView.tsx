import React, { useState } from 'react';
import { User } from '../types';
import { store, money } from '../store/sheffieldStore';
import { PageHead, StatusBadge, EmptyState } from '../components/CommonUI';
import { Modal } from '../components/Modal';

interface PayrollViewProps {
  user: User;
  onToast: (msg: string, isError?: boolean) => void;
}

export const PayrollView: React.FC<PayrollViewProps> = ({ user, onToast }) => {
  const { runs, payslips, disclaimer } = store.getPayroll(user);
  const canRunPayroll = ['payroll', 'admin'].includes(user.role);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [period, setPeriod] = useState(new Date().toISOString().slice(0, 7));

  const handleCreateRun = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = store.createPayrollRun(period, user);
      onToast(`Draft calculation: ${res.headcount} people`);
      setIsModalOpen(false);
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handleFinalise = (id: number) => {
    if (!window.confirm('Finalise this illustrative payroll and publish demo payslips?')) return;
    try {
      store.finalisePayrollRun(id, user);
      onToast('Demo payslips published');
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  return (
    <div>
      <PageHead
        title="Payroll & employee payslips"
        kicker="UK PAYROLL / EXPLAINABLE SIMULATOR"
        desc="Run an illustrative monthly calculation, finalise a period and view a connected employee payslip."
        actions={
          canRunPayroll && (
            <button className="btn primary" onClick={() => setIsModalOpen(true)} type="button">
              + Create payroll run
            </button>
          )
        }
      />

      <div className="note attention">
        <strong>Non-statutory payroll simulation:</strong> {disclaimer}
      </div>

      {runs.length > 0 && (
        <div className="card" style={{ marginTop: 17 }}>
          <h3>Payroll control centre</h3>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Period</th>
                  <th>People</th>
                  <th>Gross pay</th>
                  <th>Demo deductions</th>
                  <th>Net pay</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.period}</strong>
                    </td>
                    <td>{r.headcount}</td>
                    <td>{money(r.gross)}</td>
                    <td>{money(r.deduction)}</td>
                    <td>{money(r.net)}</td>
                    <td>
                      <StatusBadge value={r.status} />
                    </td>
                    <td>
                      {r.status === 'Draft' ? (
                        <button
                          className="btn light small"
                          onClick={() => handleFinalise(r.id)}
                          type="button"
                        >
                          Finalise
                        </button>
                      ) : (
                        '--'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: 18 }}>
        <h3>My payslips</h3>
        <p className="card-sub">Payslips become available only after the payroll administrator finalises a period.</p>

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Period</th>
                <th>Gross</th>
                <th>Demo deduction</th>
                <th>Net</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {payslips.length ? (
                payslips.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.period}</strong>
                    </td>
                    <td>{money(r.gross)}</td>
                    <td>{money(r.deduction)}</td>
                    <td>
                      <strong>{money(r.net)}</strong>
                    </td>
                    <td>
                      <StatusBadge value={r.status} />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>
                    <EmptyState message="No finalised payslips for your account yet. Switch to Oliver Reed (Payroll) to calculate and finalise a run." />
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create illustrative payroll"
        intro="A draft run calculates synthetic monthly pay. Finalisation makes payslips visible."
      >
        <form onSubmit={handleCreateRun} className="form-stack">
          <label>
            Payroll period (YYYY-MM)
            <input
              type="month"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              required
            />
          </label>

          <div className="note attention">
            Demonstration only: fixed 18% example deduction. Never use this result to pay workers or file UK statutory returns.
          </div>

          <div className="form-actions">
            <button className="btn ghost" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn primary">
              Calculate payroll
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
