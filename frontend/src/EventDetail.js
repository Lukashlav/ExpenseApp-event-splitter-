import React, { useEffect, useState } from 'react';
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
        if (!res.ok) {
          throw new Error('Failed to delete expense');
        }
        setEvent(prevEvent => ({
          ...prevEvent,
          expenses: prevEvent.expenses.filter(exp => exp.id !== expenseId),
        }));
      })
      .catch(error => console.error(error));
  };

  const handleDeleteEvent = () => {
    fetch(`/api/events/${id}/`, {
      method: 'DELETE',
    })
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to delete event');
        }
        navigate('/');
      })
      .catch(error => console.error(error));
  };

  useEffect(() => {
    fetch(`/api/events/${id}/`)
      .then(res => res.json())
      .then(data => setEvent(data));

    fetch(`/api/events/${id}/settlement/`)
      .then(res => res.json())
      .then(data => setSettlements(data));
  }, [id]);

  const handleAddParticipant = (e) => {
    e.preventDefault();
    fetch(`/api/events/${id}/add_participant/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, email }),
    })
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to add participant');
        }
        return res.json();
      })
      .then(newParticipant => {
        setEvent(prevEvent => ({
          ...prevEvent,
          participants: [...prevEvent.participants, newParticipant],
        }));
        setName('');
        setEmail('');
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleDeleteParticipant = (participantId) => {
    fetch(`/api/participants/${participantId}/`, {
      method: 'DELETE',
    })
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to delete participant');
        }
        setEvent(prevEvent => ({
          ...prevEvent,
          participants: prevEvent.participants.filter(p => p.id !== participantId),
        }));
      })
      .catch(error => console.error(error));
  };

  if (!event) return <div>Načítám data eventu...</div>;

  return (
    <div>
      <h2>{event.title}</h2>
      <button onClick={handleDeleteEvent}>Smazat event</button>
      <p>{event.description}</p>

      <h3>Účastníci:</h3>
      <ul>
        {event.participants?.map(p => (
          <li key={p.id}>
            {p?.name || 'Neznámý účastník'} ({p?.email || 'bez emailu'})
            <button onClick={() => handleDeleteParticipant(p.id)}>Smazat</button>
          </li>
        ))}
      </ul>

      <form onSubmit={handleAddParticipant}>
        <input
          type="text"
          placeholder="Jméno"
          value={name}
          onChange={e => setName(e.target.value)}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
        <button type="submit">Přidat účastníka</button>
      </form>

      <h3>Výdaje:</h3>
      <ul>
        {event.expenses?.map(e => (
          <li key={e.id}>
            {e.description}: {e.amount} Kč, zaplatil {e.payer?.name || 'neznámý'}{' '}
            <button onClick={() => handleDeleteExpense(e.id)}>Smazat</button>
          </li>
        ))}
      </ul>
      <Link to={`/events/${id}/add-expense`}>+ Přidat výdaj</Link>

      <h3>Kdo komu dluží:</h3>
      {settlements && settlements.length > 0 ? (
        <ul>
          {settlements.map((s, index) => (
            <li key={index}>
              {s.from} dluží {s.to} {s.amount.toFixed(2)} Kč
            </li>
          ))}
        </ul>
      ) : (
        <p>Žádné dluhy k vyrovnání.</p>
      )}

      <Link to="/">← Zpět na seznam eventů</Link>
    </div>
  );
}

export default EventDetail;