import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

function EventDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [settlements, setSettlements] = useState(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

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

  if (!event) return <div>Načítám data eventu...</div>;

  return (
    <div>
      <h2>{event.title}</h2>
      <p>{event.description}</p>

      <h3>Účastníci:</h3>
      <ul>
        {event.participants.map(p => (
          <li key={p.id}>{p.name} ({p.email || 'bez emailu'})</li>
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
        {event.expenses.map(e => (
          <li key={e.id}>
            {e.description}: {e.amount} Kč, zaplatil {e.payer.name}
          </li>
        ))}
      </ul>

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