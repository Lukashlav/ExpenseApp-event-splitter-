import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

function EventDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [balance, setBalance] = useState(null);

  useEffect(() => {
    fetch(`/api/events/${id}/`)
      .then(res => res.json())
      .then(data => setEvent(data));

    fetch(`/api/events/${id}/balance/`)
      .then(res => res.json())
      .then(data => setBalance(data));
  }, [id]);

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

      <h3>Výdaje:</h3>
      <ul>
        {event.expenses.map(e => (
          <li key={e.id}>
            {e.description}: {e.amount} Kč, zaplatil {e.payer.name}
          </li>
        ))}
      </ul>

      <h3>Saldo (kdo komu dluží):</h3>
      {balance ? (
        <ul>
          {Object.entries(balance).map(([participantId, amount]) => (
            <li key={participantId}>
              {event.participants.find(p => p.id === parseInt(participantId))?.name || 'Unknown'}: {amount.toFixed(2)} Kč
            </li>
          ))}
        </ul>
      ) : (
        <p>Načítám saldo...</p>
      )}

      <Link to="/">← Zpět na seznam eventů</Link>
    </div>
  );
}

export default EventDetail;