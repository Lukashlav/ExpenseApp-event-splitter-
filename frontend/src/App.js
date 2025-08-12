import React, { useEffect, useState } from 'react';

function App() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    fetch('/api/events/')
      .then(response => response.json())
      .then(data => setEvents(data.results || data));
  }, []);

  return (
    <div>
      <h1>Seznam eventů</h1>
      <ul>
        {events.map(event => (
          <li key={event.id}>{event.title}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;