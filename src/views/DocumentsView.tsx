import React, { useState } from 'react';
import { User } from '../types';
import { store } from '../store/sheffieldStore';
import { PageHead, StatusBadge, EmptyState } from '../components/CommonUI';
import { Modal } from '../components/Modal';

interface DocumentsViewProps {
  user: User;
  onToast: (msg: string, isError?: boolean) => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({ user, onToast }) => {
  const docs = store.getDocuments(user);
  const allUsers = store.getState().users;
  const isHR = ['hr', 'admin'].includes(user.role);
  const isAdmin = user.role === 'admin';

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [targetEmpId, setTargetEmpId] = useState<number>(user.id);
  const [docType, setDocType] = useState('Signed declaration');
  const [retentionUntil, setRetentionUntil] = useState('2033-12-31');
  const [fileName, setFileName] = useState('');
  const [fileContent, setFileContent] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = () => {
        setFileContent(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileName) {
      onToast('Please select a file to upload', true);
      return;
    }
    try {
      store.uploadDocument(user, targetEmpId, fileName, docType, retentionUntil, fileContent);
      onToast('Document saved with retention rules');
      setIsUploadOpen(false);
      setFileName('');
      setFileContent('');
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handleArchive = (id: number) => {
    if (!window.confirm('Archive this document?')) return;
    try {
      store.archiveDocument(id, user);
      onToast('Document archived');
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handleSimulateExpiry = (id: number) => {
    if (
      !window.confirm(
        'Set this ARCHIVED demo record retention to yesterday for retention-purge demonstration? No production retention rules will be changed.'
      )
    )
      return;
    try {
      store.simulateDocumentExpiry(id, user);
      onToast('Demo retention expiry simulated; run eligible purge');
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handlePurge = () => {
    if (!window.confirm('Purge archived documents whose retention dates have passed?')) return;
    try {
      const count = store.purgeDocuments(user);
      onToast(`${count} eligible documents purged`);
    } catch (err: any) {
      onToast(err.message, true);
    }
  };

  const handleDownload = (doc: any) => {
    // Generate simple blob download
    const blob = new Blob([doc.file_content || 'Sheffield City Council - Confidential Document Record'], {
      type: 'text/plain',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = doc.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    onToast(`Downloaded: ${doc.name}`);
  };

  const selectableEmployees = isHR ? allUsers : allUsers.filter((u) => u.id === user.id);

  return (
    <div>
      <PageHead
        title="Employee document records"
        kicker="USE CASE 04 / DOCUMENT GOVERNANCE"
        desc="Controlled upload, classified records, employee visibility, retention and scheduled archive/purge."
        actions={
          <button className="btn primary" onClick={() => setIsUploadOpen(true)} type="button">
            + Upload document
          </button>
        }
      />

      <div className="grid two">
        <div className="card">
          <div className="eyebrow">SAFE RECORD STORAGE</div>
          <h3>Confidential employee files</h3>
          <p className="small muted">
            Only employees and authorised People Services can access documents. Every view and upload is audited.
          </p>
        </div>

        <div className="card">
          <div className="eyebrow">RETENTION CONTROL</div>
          <h3>Archive before eligible purge</h3>
          <p className="small muted">
            Purge requires both expiry of the retention date and archive status, with a recorded audit event.
          </p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <div className="section-top">
          <h2>Document register</h2>
          {isHR && (
            <button className="btn small ghost" onClick={handlePurge} type="button">
              Run eligible purge
            </button>
          )}
        </div>

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>File / employee</th>
                <th>Type</th>
                <th>Retention until</th>
                <th>Record state</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.length ? (
                docs.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <button
                        className="btn subtle small"
                        style={{ padding: 0, fontWeight: 800, textAlign: 'left' }}
                        onClick={() => handleDownload(a)}
                        type="button"
                      >
                        {a.name}
                      </button>
                      <div className="micro muted">{a.employee}</div>
                    </td>
                    <td>{a.doc_type}</td>
                    <td>{a.retention_until}</td>
                    <td>
                      <StatusBadge value={a.archived ? 'Archived' : 'Active'} />
                    </td>
                    <td>
                      {isHR && !a.archived ? (
                        <button
                          className="btn ghost small"
                          onClick={() => handleArchive(a.id)}
                          type="button"
                        >
                          Archive
                        </button>
                      ) : isAdmin && a.archived ? (
                        <button
                          className="btn light small"
                          onClick={() => handleSimulateExpiry(a.id)}
                          type="button"
                        >
                          Simulate expiry
                        </button>
                      ) : (
                        '--'
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>
                    <EmptyState message="No documents stored yet. Upload a sample document with '+ Upload document'." />
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="note" style={{ marginTop: 15 }}>
        This prototype enforces role-based file access and retention transitions locally. Formal GDPR compliance,
        legal holds, production encryption, and retention policy validation require a deployed implementation.
      </div>

      <Modal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        title="Upload employee document"
        intro="Files are private, classified and governed by a retention date. Maximum 5 MB."
      >
        <form onSubmit={handleUploadSubmit} className="form-stack">
          <label>
            Employee
            <select
              value={targetEmpId}
              onChange={(e) => setTargetEmpId(Number(e.target.value))}
            >
              {selectableEmployees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} ({e.job})
                </option>
              ))}
            </select>
          </label>

          <label>
            Document classification
            <select value={docType} onChange={(e) => setDocType(e.target.value)}>
              <option value="Employment">Employment</option>
              <option value="Signed declaration">Signed declaration</option>
              <option value="Identity verification">Identity verification</option>
              <option value="Learning certificate">Learning certificate</option>
              <option value="Payroll document">Payroll document</option>
            </select>
          </label>

          <label>
            Retention until
            <input
              type="date"
              value={retentionUntil}
              onChange={(e) => setRetentionUntil(e.target.value)}
              required
            />
          </label>

          <label>
            File (PDF, DOCX, TXT, PNG, JPEG)
            <input
              type="file"
              accept=".pdf,.txt,.docx,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              required
            />
          </label>

          <div className="form-actions">
            <button className="btn ghost" type="button" onClick={() => setIsUploadOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn primary">
              Upload document
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
