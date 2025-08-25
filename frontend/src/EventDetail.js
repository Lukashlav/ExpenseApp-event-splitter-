import React, { useEffect, useState } from 'react';
import './EventDetail.css';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { apiFetch, api } from './api';

/* Small hook to know if user is authenticated via session */
function useAuth() {
  const [isAuthed, setIsAuthed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await api.me();
        if (mounted) setIsAuthed(!!data?.authenticated);
      } catch {
        if (mounted) setIsAuthed(false);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const logout = async () => {
    try {
      await api.logout();
      setIsAuthed(false);
    } catch { /* noop */ }
  };

  return { isAuthed, loading, logout };
}

function EventDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthed, loading: authLoading, logout } = useAuth();

  const [event, setEvent] = useState(null);
  const [settlements, setSettlements] = useState(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const handleDeleteExpense = async (expenseId) => {
    try {
      await apiFetch(`/api/expenses/${expenseId}/`, { method: 'DELETE' });
      setEvent(prev => ({ ...prev, expenses: prev.expenses.filter(e => e.id !== expenseId) }));
    } catch (e) {
      if (e && (e.status === 401 || e.status === 403)) {
        navigate('/login');
        return;
      }
      console.error(e);
      alert('Nepodařilo se smazat výdaj.');
    }
  };

  const handleDeleteParticipant = async (participantId) => {
    try {
      // Prefer DELETE, fallback to POST if backend expects it
      try {
        await apiFetch(`/api/participants/${participantId}/delete/`, { method: 'DELETE' });
      } catch (err) {
        if (err && err.status === 405) {
          await apiFetch(`/api/participants/${participantId}/delete/`, { method: 'POST' });
        } else {
          throw err;
        }
      }
      setEvent(prev => ({
        ...prev,
        participants: (prev.participants || []).filter(p => p.id !== participantId),
      }));
    } catch (e) {
      if (e && (e.status === 401 || e.status === 403)) {
        navigate('/login');
        return;
      }
      console.error(e);
      alert('Nepodařilo se smazat účastníka.');
    }
  };

  const handleDeleteEvent = async () => {
    try {
      await apiFetch(`/api/events/${id}/`, { method: 'DELETE' });
      navigate('/');
    } catch (e) {
      if (e && (e.status === 401 || e.status === 403)) {
        navigate('/login');
        return;
      }
      console.error(e);
      alert('Nepodařilo se smazat event.');
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const dataEvent = await apiFetch(`/api/events/${id}/`);
        setEvent(dataEvent);
        const dataSet = await apiFetch(`/api/events/${id}/settlement/`);
        setSettlements(dataSet);
      } catch (e) {
        if (e && (e.status === 401 || e.status === 403)) {
          navigate('/login');
          return;
        }
        console.error(e);
      }
    })();
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAddParticipant = async (e) => {
    e.preventDefault();
    try {
      const newParticipant = await apiFetch(`/api/events/${id}/add_participant/`, {
        method: 'POST',
        body: { name, email },
      });
      setEvent(prev => ({ ...prev, participants: [...(prev.participants || []), newParticipant] }));
      setName(''); setEmail('');
    } catch (err) {
      if (err && (err.status === 401 || err.status === 403)) {
        navigate('/login');
        return;
      }
      console.error(err);
      alert('Nepodařilo se přidat účastníka.');
    }
  };

  if (authLoading || !event) {
    return <div>Načítám data…</div>;
  }

  return (
    <div className="event-detail-container">
      {/* App header */}
      <header className="app-header">
        <Link to="/" className="brand">ExpenseApp</Link>
        <nav className="header-actions">
          {isAuthed ? (
            <button className="btn" onClick={logout}>Odhlásit</button>
          ) : (
            <>
              <Link className="btn" to="/login">Přihlásit</Link>
              <Link className="btn" to="/signup">Registrovat</Link>
            </>
          )}
        </nav>
      </header>

      <h2>{event.title}</h2>
      <p>{event.description}</p>

      <h3>Účastníci:</h3>
      <ul className="participants-list">
        {event.participants?.map(p => (
          <li key={p.id} className="participant-row">
            <div className="participant-info">
              {p?.name || 'Neznámý účastník'} ({p?.email || 'bez emailu'})
            </div>
            <button className="btn" onClick={() => handleDeleteParticipant(p.id)}>Smazat</button>
          </li>
        ))}
      </ul>

      <form className="participant-form" onSubmit={handleAddParticipant}>
        <div className="form-row">
          <label>
            Jméno
            <input type="text" placeholder="Např. Karel" value={name} onChange={e => setName(e.target.value)} required />
          </label>
          <label className="inline-label">
            <span className="label-title">Email <span className="muted">(volitelné)</span></span>
            <input type="email" placeholder="napr. karel@example.com" value={email} onChange={e => setEmail(e.target.value)} />
          </label>
          <div className="form-actions">
            <button className="btn primary" type="submit">+ Přidat</button>
          </div>
        </div>
        <p className="form-hint">Účastníky můžeš přidat i bez emailu a doplnit později.</p>
      </form>

      <h3>Výdaje</h3>
      <div className="table-container">
        <table className="event-table">
          <thead>
            <tr>
              <th className="th-description">Popis</th>
              <th className="th-amount">Částka (Kč)</th>
              <th className="th-payer">Zaplatil</th>
              <th className="th-recipients">Komu</th>
              <th className="th-category">Kategorie</th>
              <th className="th-actions">Akce</th>
            </tr>
          </thead>
          <tbody>
            {event.expenses?.map(exp => (
              <tr key={exp.id}>
                <td className="description">{exp.description}</td>
                <td className="amount">{exp.amount}</td>
                <td className="payer">{exp.payer?.name || 'Neznámý'}</td>
                <td className="recipients">
                  {Array.isArray(exp.split_between) && exp.split_between.length > 0
                    ? exp.split_between.map(p => p.name).join(', ')
                    : 'Nikomu'}
                </td>
                <td className="category">{exp.category?.name || 'Neznámá'}</td>
                <td className="actions">
                  <button className="btn" onClick={() => handleDeleteExpense(exp.id)}>Smazat</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Link className="add-expense-link btn" to={`/events/${id}/add-expense`}>+ Přidat výdaj</Link>

      <h3>Kdo komu dluží:</h3>
      {settlements && settlements.length > 0 ? (
        <ul className="settlements-list">
          {settlements.map((s, i) => (
            <li key={i}>{s.from} dluží {s.to} {Number(s.amount).toFixed(2)} Kč</li>
          ))}
        </ul>
      ) : (
        <p>Žádné dluhy k vyrovnání.</p>
      )}

      <br />
      <button className="btn delete-event-btn" onClick={handleDeleteEvent}>Smazat event</button>
      <br />
      <Link className="back-link btn" to="/">← Zpět na seznam eventů</Link>
    </div>
  );
}

export default EventDetail;