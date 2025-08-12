import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

function EventDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [settlements, setSettlements] = useState(null);

  useEffect(() => {
    fetch(`/api/events/${id}/`)
      .then(res => res.json())
      .then(data => setEvent(data));

    fetch(`/api/events/${id}/settlement/`)
      .then(res => res.json())
      .then(data => setSettlements(data));
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