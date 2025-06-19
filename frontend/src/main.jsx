import React from 'react';
import ReactDOM from 'react-dom/client';
import * as d3 from 'd3';

function App() {
  const [start, setStart] = React.useState('');
  const [end, setEnd] = React.useState('');
  const [lat, setLat] = React.useState('40.7128');
  const [lon, setLon] = React.useState('-74.0060');
  const [data, setData] = React.useState(null);
  const [error, setError] = React.useState(null);
  const svgRef = React.useRef(null);

  const BASE_URL = import.meta.env.VITE_API_URL || 'https://fantastic-space-cod-5g57gw9764p9374gr-8000.app.github.dev';

  const submit = async (e) => {
    e.preventDefault();
    const params = new URLSearchParams({ start, end, lat, lon });
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}/balas?${params}`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || 'Request failed');
      }
      setData(await res.json());
    } catch (err) {
      setData(null);
      setError(err.message);
    }
  };

  React.useEffect(() => {
    if (!data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 600;
    const height = 300;
    const margin = { top: 20, right: 30, bottom: 30, left: 40 };

    const startTime = new Date(data.start);
    const times = data.data.map((_, i) => new Date(startTime.getTime() + i * 5 * 60 * 1000));
    const components = ['uccha', 'dig', 'kala', 'cheshta', 'naisargika', 'drik'];

    const x = d3.scaleTime()
      .domain(d3.extent(times))
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(data.data, row => d3.max(components, c => row['Sun'][c]))])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const line = d3.line()
      .x((d, i) => x(times[i]))
      .y(d => y(d));

    const colors = d3.schemeCategory10;

    components.forEach((comp, idx) => {
      const values = data.data.map(row => row['Sun'][comp]);
      svg.append('path')
        .datum(values)
        .attr('fill', 'none')
        .attr('stroke', colors[idx % colors.length])
        .attr('stroke-width', 1.5)
        .attr('d', line);
    });

    svg.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x));

    svg.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y));
  }, [data]);

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
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <svg ref={svgRef} width="600" height="300"></svg>
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
