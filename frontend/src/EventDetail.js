import React, { useEffect, useState } from 'react';
import './EventDetail.css';
import { useParams, Link, useNavigate } from 'react-router-dom';

function EventDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [settlements, setSettlements] = useState(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const handleDeleteExpense = (expenseId) => {
    fetch(`/api/expenses/${expenseId}/`, {
      method: 'DELETE',
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
    fetch(`/api/events/${id}/`, { method: 'DELETE' })
      .then(res => { if (!res.ok) throw new Error('Failed to delete event'); navigate('/'); })
      .catch(console.error);
  };

  useEffect(() => {
    fetch(`/api/events/${id}/`).then(res => res.json()).then(setEvent);
    fetch(`/api/events/${id}/settlement/`).then(res => res.json()).then(setSettlements);
  }, [id]);

  const handleAddParticipant = (e) => {
    e.preventDefault();
    fetch(`/api/events/${id}/add_participant/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email }),
    })
      .then(res => { if (!res.ok) throw new Error('Failed to add participant'); return res.json(); })
      .then(newParticipant => {
        setEvent(prevEvent => ({ ...prevEvent, participants: [...prevEvent.participants, newParticipant] }));
        setName(''); setEmail('');
      })
      .catch(console.error);
  };

  const handleDeleteParticipant = (participantId) => {
    fetch(`/api/participants/${participantId}/`, { method: 'DELETE' })
      .then(res => { if (!res.ok) throw new Error('Failed to delete participant');
        setEvent(prevEvent => ({ ...prevEvent, participants: prevEvent.participants.filter(p => p.id !== participantId) }));
      })
      .catch(console.error);
  };

  if (!event) return <div>Načítám data eventu...</div>;

  return (
    <div className="event-detail-container">
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