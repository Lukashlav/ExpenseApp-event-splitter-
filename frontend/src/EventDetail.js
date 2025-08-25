import React, { useEffect, useState } from 'react';
import './EventDetail.css';
import { useParams, Link, useNavigate } from 'react-router-dom';

// --- auth helpers ---
const getCSRFToken = () => {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
};

const getAuthHeaders = (isJSON = false) => {
  const token = localStorage.getItem('token');
  const headers = {};
  if (token) headers['Authorization'] = `Token ${token}`; // change to `Bearer` if you switch to JWT
  if (isJSON) headers['Content-Type'] = 'application/json';
  const csrf = getCSRFToken();
  if (csrf) headers['X-CSRFToken'] = csrf;
  return headers;
};

function EventDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };
  const [event, setEvent] = useState(null);
  const [settlements, setSettlements] = useState(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const handleDeleteExpense = (expenseId) => {
    fetch(`/api/expenses/${expenseId}/`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      credentials: 'include',
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to delete expense');
        setEvent(prevEvent => ({
          ...prevEvent,
          expenses: prevEvent.expenses.filter(exp => exp.id !== expenseId),
        }));
      })
      .catch(console.error);
  };

  const handleDeleteEvent = () => {
    fetch(`/api/events/${id}/`, { method: 'DELETE', headers: getAuthHeaders(), credentials: 'include' })
      .then(res => { if (!res.ok) throw new Error('Failed to delete event'); navigate('/'); })
      .catch(console.error);
  };

  useEffect(() => {
    const load = async () => {
      try {
        const resEvent = await fetch(`/api/events/${id}/`, { headers: getAuthHeaders(), credentials: 'include' });
        if (resEvent.status === 401) { navigate('/login'); return; }
        const dataEvent = await resEvent.json();
        setEvent(dataEvent);

        const resSet = await fetch(`/api/events/${id}/settlement/`, { headers: getAuthHeaders(), credentials: 'include' });
        if (resSet.status === 401) { navigate('/login'); return; }
        const dataSet = await resSet.json();
        setSettlements(dataSet);
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, [id, navigate]);

  const handleAddParticipant = (e) => {
    e.preventDefault();
    fetch(`/api/events/${id}/add_participant/`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      credentials: 'include',
      body: JSON.stringify({ name, email }),
    })
      .then(res => {
        if (res.status === 401) { navigate('/login'); return null; }
        if (!res.ok) throw new Error('Failed to add participant');
        return res.json();
      })
      .then(newParticipant => {
        if (!newParticipant) return;
        setEvent(prevEvent => ({ ...prevEvent, participants: [...prevEvent.participants, newParticipant] }));
        setName(''); setEmail('');
      })
      .catch(console.error);
  };

  const handleDeleteParticipant = (participantId) => {
    fetch(`/api/participants/${participantId}/`, { method: 'DELETE', headers: getAuthHeaders(), credentials: 'include' })
      .then(res => { if (!res.ok) throw new Error('Failed to delete participant');
        setEvent(prevEvent => ({ ...prevEvent, participants: prevEvent.participants.filter(p => p.id !== participantId) }));
      })
      .catch(console.error);
  };

  if (!event) return <div>Načítám data eventu...</div>;

  return (
    <div className="event-detail-container">
      <div className="auth-bar" style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginBottom: '8px' }}>
        {localStorage.getItem('token') ? (
          <button className="btn" onClick={handleLogout}>Odhlásit</button>
        ) : (
          <>
            <Link className="btn" to="/login">Přihlásit</Link>
            <Link className="btn" to="/signup">Registrovat</Link>
          </>
        )}
      </div>
      <h2>{event.title}</h2>
      <p>{event.description}</p>

      <h3>Účastníci:</h3>
      <div className="participants-list">
        <ul className="participants-list">
          {event.participants?.map(p => (
            <li key={p.id}>{p?.name || 'Neznámý účastník'} ({p?.email || 'bez emailu'}) <button className="btn" onClick={() => handleDeleteParticipant(p.id)}>Smazat</button></li>
          ))}
        </ul>
      </div>

      <form className="participant-form" onSubmit={handleAddParticipant}>
        <input type="text" placeholder="Jméno" value={name} onChange={e => setName(e.target.value)} required />
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <button className="btn" type="submit">Přidat účastníka</button>
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
                <td className="payer">{exp.payer?.name || "Neznámý"}</td>
                <td className="recipients">
                  {Array.isArray(exp.split_between) && exp.split_between.length > 0
                    ? exp.split_between.map(p => p.name).join(", ")
                    : "Nikomu"}
                </td>
                <td className="category">{exp.category?.name || "Neznámá"}</td>
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
        <ul className="settlements-list">{settlements.map((s,i) => <li key={i}>{s.from} dluží {s.to} {s.amount.toFixed(2)} Kč</li>)}</ul>
      ) : (<p>Žádné dluhy k vyrovnání.</p>)}

      <br />
      <button className="btn delete-event-btn" onClick={handleDeleteEvent}>Smazat event</button>
      <br />
      <Link className="back-link btn" to="/">← Zpět na seznam eventů</Link>
    </div>
  );
}

export default EventDetail;