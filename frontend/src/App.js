import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import EventDetail from './EventDetail';
import NewEvent from './NewEvent';
import AddExpense from './AddExpense';

function GlobalStyles() {
  return (
    <style>{`
      /* Hide common top progress bars (NProgress, Pace) if injected anywhere */
      #nprogress, #nprogress .bar { display: none !important; }
      .pace, .pace .pace-progress, .pace .pace-activity { display: none !important; }

      /* Remove any global top borders or pseudo-elements that could render a thin bar */
      html, body { border-top: 0 !important; }
      body::before, #root::before, .app-container::before { content: none !important; }

      /* Ensure our desired background shows and isn't overridden by global styles */
      html, body, #root { background: #f2f6fc !important; }
    `}</style>
  );
}

function EventList() {
  const [events, setEvents] = React.useState([]);

  React.useEffect(() => {
    fetch('/api/events/')
      .then(res => res.json())
      .then(data => setEvents(data.results || data))
      .catch(() => setEvents([]));
  }, []);

  const styles = {
    container: {
      maxWidth: 960,
      margin: '48px auto 80px',
      padding: 24,
      background: '#ffffff',
      borderRadius: 12,
      boxShadow: '0 10px 30px rgba(0,0,0,0.06)',
      fontFamily: `'Poppins', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif`,
    },
    headerRow: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 16,
      gap: 12,
      flexWrap: 'wrap',
    },
    title: {
      margin: 0,
      fontSize: 28,
      fontWeight: 700,
      color: '#1e3a8a',
      letterSpacing: 0.2,
    },
    toolbar: {
      display: 'flex',
      gap: 12,
      alignItems: 'center',
    },
    primaryBtn: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      padding: '6px 12px',
      background: '#2563eb',
      borderRadius: 10,
      border: '1px solid #1f4ed8',
      color: '#fff',
      textDecoration: 'none',
      fontWeight: 600,
      boxShadow: '0 6px 16px rgba(37,99,235,.25)',
      transition: 'transform .06s ease, box-shadow .12s ease, background .12s ease',
      fontSize: 14,
    },
    primaryBtnHover: {
      transform: 'translateY(-1px)',
      boxShadow: '0 8px 20px rgba(37,99,235,.28)',
    },
    list: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
      gap: 16,
      margin: '16px 0 0',
      padding: 0,
      listStyle: 'none',
    },
    card: {
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: 16,
      background: '#f8fafc',
      border: '1px solid #e2e8f0',
      borderRadius: 12,
      transition: 'transform .08s ease, box-shadow .12s ease, border-color .12s ease',
    },
    cardHover: {
      transform: 'translateY(-2px)',
      boxShadow: '0 8px 20px rgba(0,0,0,.06)',
      borderColor: '#cbd5e1',
    },
    eventTitle: {
      fontSize: 18,
      fontWeight: 600,
      margin: 0,
      color: '#0f172a',
    },
    eventSubtitle: {
      marginTop: 6,
      fontSize: 13,
      color: '#64748b',
      minHeight: 18,
    },
    openLink: {
      marginTop: 12,
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      textDecoration: 'none',
      fontWeight: 600,
      color: '#2563eb',
    },
    empty: {
      padding: '24px 0 8px',
      color: '#64748b',
      fontSize: 15,
    },
  };

  // Small helpers for hover effects with React state
  const [hoveredBtn, setHoveredBtn] = React.useState(false);
  const [hoveredCard, setHoveredCard] = React.useState(null);

  return (
    <div style={styles.container}>
      <div style={styles.headerRow}>
        <h1 style={styles.title}>ExpenseApp</h1>
        <div style={styles.toolbar}>
          <Link
            to="/new-event"
            onMouseEnter={() => setHoveredBtn(true)}
            onMouseLeave={() => setHoveredBtn(false)}
            style={{ ...styles.primaryBtn, ...(hoveredBtn ? styles.primaryBtnHover : {}) }}
          >
            <span>＋</span> Přidat nový event
          </Link>
        </div>
      </div>

      {events.length === 0 ? (
        <p style={styles.empty}>
          Zatím tu nic není. Vytvoř svůj první event kliknutím na&nbsp;
          <Link to="/new-event" style={{ color: '#2563eb', fontWeight: 600 }}>„Přidat nový event“</Link>.
        </p>
      ) : (
        <ul style={styles.list}>
          {events.map((event) => (
            <li
              key={event.id}
              style={{
                ...styles.card,
                ...(hoveredCard === event.id ? styles.cardHover : {}),
              }}
              onMouseEnter={() => setHoveredCard(event.id)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div>
                <h3 style={styles.eventTitle}>{event.title}</h3>
                {event.description ? (
                  <div style={styles.eventSubtitle}>{event.description}</div>
                ) : (
                  <div style={styles.eventSubtitle}>&nbsp;</div>
                )}
              </div>
              <Link to={`/events/${event.id}`} style={styles.openLink}>
                Otevřít detail → 
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function App() {
  return (
    <div className="app-container">
      <GlobalStyles />
      <Routes>
        <Route path="/" element={<EventList />} />
        <Route path="/events/:id" element={<EventDetail />} />
        <Route path="/new-event" element={<NewEvent />} />
        <Route path="/events/:id/add-expense" element={<AddExpense />} />
      </Routes>
    </div>
  );
}

export default App;