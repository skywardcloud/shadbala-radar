import React from 'react';
import ReactDOM from 'react-dom/client';

function App() {
  const [start, setStart] = React.useState('');
  const [end, setEnd] = React.useState('');
  const [lat, setLat] = React.useState('40.7128');
  const [lon, setLon] = React.useState('-74.0060');
  const [data, setData] = React.useState(null);

  const submit = async (e) => {
    e.preventDefault();
    const params = new URLSearchParams({ start, end, lat, lon });
    const res = await fetch(`http://localhost:8000/balas?${params}`);
    setData(await res.json());
  };

  return (
    <div>
      <h1>Shadbala Radar</h1>
      <form onSubmit={submit} style={{ marginBottom: '1rem' }}>
        <label>
          Start (EST)
          <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} required />
        </label>
        <label>
          End (EST)
          <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} required />
        </label>
        <label>
          Lat
          <input type="number" step="0.0001" value={lat} onChange={(e) => setLat(e.target.value)} />
        </label>
        <label>
          Lon
          <input type="number" step="0.0001" value={lon} onChange={(e) => setLon(e.target.value)} />
        </label>
        <button type="submit">Fetch</button>
      </form>
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
