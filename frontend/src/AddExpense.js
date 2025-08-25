import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
// Styles for this form are injected at the bottom of the component

// Configurable backend base URL (falls back to Django dev server)
const API_BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8000';

// Read a cookie value (for CSRF)
function getCookie(name) {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function AddExpense() {
  const { id } = useParams(); // event ID
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [paidBy, setPaidBy] = useState('');
  const [participants, setParticipants] = useState([]);
  const [selectedParticipants, setSelectedParticipants] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const headers = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Token ${token}`;

    // Load event (participants)
    fetch(`${API_BASE}/api/events/${id}/`, {
      credentials: 'include',
      headers,
    })
      .then(res => res.ok ? res.json() : Promise.reject(res))
      .then(data => setParticipants(data.participants || []))
      .catch(async (res) => {
        let msg = 'Nepodařilo se načíst účastníky.';
        try { msg = await res.text(); } catch {}
        setError(msg);
      });

    // Load categories
    fetch(`${API_BASE}/api/categories/`, {
      credentials: 'include',
      headers,
    })
      .then(res => res.ok ? res.json() : Promise.reject(res))
      .then(data => setCategories(Array.isArray(data) ? data : []))
      .catch(async (res) => {
        let msg = 'Nepodařilo se načíst kategorie.';
        try { msg = await res.text(); } catch {}
        setError(msg);
      });
  }, [id]);

  const handleCheckboxChange = (participantId) => {
    setSelectedParticipants(prev =>
      prev.includes(participantId)
        ? prev.filter(p => p !== participantId)
        : [...prev, participantId]
    );
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedParticipants([]);
    } else {
      setSelectedParticipants(participants.map(p => p.id));
    }
    setSelectAll(!selectAll);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    const payload = {
      description,
      amount: parseFloat(amount),
      payer: Number(paidBy), // backend očekává pole `payer`
      event: Number(id),
      split_between_ids: selectedParticipants.map(Number),
      category: category ? Number(category) : null,
    };

    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken') || '',
    };
    if (token) headers['Authorization'] = `Token ${token}`;

    fetch(`${API_BASE}/api/expenses/`, {
      method: 'POST',
      credentials: 'include',
      headers,
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        if (!res.ok) {
          // Hezčí hlášky pro 401/403 a JSON/text fallback
          if (res.status === 401 || res.status === 403) {
            throw new Error('Nejste přihlášen. Přihlaste se prosím a zkuste to znovu.');
          }
          try {
            const data = await res.json();
            throw new Error(JSON.stringify(data));
          } catch {
            const text = await res.text();
            throw new Error(text || 'Chyba při přidávání výdaje');
          }
        }
        return res.json();
      })
      .then(() => {
        setDescription('');
        setAmount('');
        setPaidBy('');
        setSelectedParticipants([]);
        setSelectAll(false);
        setCategory('');
        navigate(`/events/${id}`);
      })
      .catch(err => setError(err.message));
  };

  return (
    <div className="add-expense-page">
      <div className="add-expense-card">
        <h2 className="title">Přidat výdaj</h2>

        {error && (
          <div className="alert" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form">
          <div className="form-grid">
            <div className="form-field">
              <label>Popis</label>
              <input
                type="text"
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Např. Ubytování"
                required
              />
            </div>

            <div className="form-field">
              <label>Částka (Kč)</label>
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                placeholder="0.00"
                required
              />
            </div>

            <div className="form-field">
              <label>Zaplatil</label>
              <select value={paidBy} onChange={e => setPaidBy(e.target.value)} required>
                <option value="">Vyber účastníka</option>
                {participants.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Kategorie</label>
              <select value={category} onChange={e => setCategory(e.target.value)}>
                <option value="">Žádná</option>
                {categories.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="split-section">
            <div className="split-header">
              <label>Přiřadit výdaj</label>
              <label className="check-all">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={handleSelectAll}
                />
                Všem účastníkům
              </label>
            </div>

            <div className="participants-list" role="group" aria-label="Výběr účastníků">
              {participants.length === 0 && (
                <div className="muted">Žádní účastníci v eventu.</div>
              )}
              {participants.map(p => (
                <label key={p.id} className="participant-pill">
                  <input
                    type="checkbox"
                    checked={selectedParticipants.includes(p.id)}
                    onChange={() => handleCheckboxChange(p.id)}
                  />
                  <span>{p.name}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="actions">
            <button type="submit" className="primary-btn">Přidat výdaj</button>
          </div>
        </form>
      </div>

      {/* Inline styles to avoid creating a separate CSS file now */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

        .add-expense-page {
          min-height: 100dvh;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          padding: 32px 16px;
          background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
          font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        }

        .add-expense-card {
          width: 100%;
          max-width: 820px;
          background: #ffffff;
          border-radius: 14px;
          box-shadow: 0 12px 30px rgba(31, 64, 171, 0.12);
          padding: 24px;
          border: 1px solid rgba(37, 99, 235, 0.08);
        }

        .title {
          margin: 0 0 18px;
          font-size: 28px;
          font-weight: 700;
          letter-spacing: 0.2px;
          color: #1e3a8a;
        }

        .alert {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fecaca;
          padding: 10px 12px;
          border-radius: 10px;
          margin-bottom: 16px;
          font-size: 14px;
        }

        .form {
          display: block;
        }

        .form-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        .form-field label {
          display: block;
          margin-bottom: 6px;
          font-weight: 600;
          color: #1f2a44;
        }

        .form-field input,
        .form-field select {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid #cbd5e1;
          border-radius: 10px;
          font-size: 14px;
          transition: box-shadow .2s, border-color .2s;
          background: #fff;
        }

        .form-field input:focus,
        .form-field select:focus {
          outline: none;
          border-color: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18);
        }

        .split-section {
          margin-top: 18px;
          padding-top: 16px;
          border-top: 1px solid #e5e7eb;
        }

        .split-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 10px;
        }

        .check-all {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #334155;
          user-select: none;
        }

        .participants-list {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          max-height: 160px;
          overflow: auto;
          padding: 6px 2px 2px;
        }

        .participant-pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border: 1px solid #e2e8f0;
          border-radius: 9999px;
          background: #f8fafc;
          font-size: 13px;
          color: #0f172a;
          cursor: pointer;
          user-select: none;
        }

        .participant-pill input {
          accent-color: #2563eb;
          cursor: pointer;
        }

        .muted { color: #64748b; font-size: 14px; }

        .actions {
          margin-top: 18px;
          display: flex;
          justify-content: flex-end;
        }

        .primary-btn {
          appearance: none;
          border: none;
          padding: 12px 18px;
          border-radius: 12px;
          background: #2563eb;
          color: #fff;
          font-weight: 700;
          font-size: 14px;
          letter-spacing: .3px;
          cursor: pointer;
          box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
          transition: transform .04s ease, background .2s ease, box-shadow .2s ease;
        }

        .primary-btn:hover { background: #1e40af; box-shadow: 0 10px 24px rgba(30, 64, 175, 0.28); }
        .primary-btn:active { transform: translateY(1px); }

        @media (max-width: 720px) {
          .form-grid { grid-template-columns: 1fr; }
          .add-expense-card { padding: 18px; }
          .title { font-size: 24px; }
        }
      `}</style>
    </div>
  );
}

export default AddExpense;