# Shadbala-radar

This project contains a FastAPI backend and a React frontend. The frontend uses Vite and D3 to display interactive charts.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Create a `.env` file in the `frontend` directory to configure the backend URL. It should define `VITE_API_URL`, e.g.

```bash
echo "VITE_API_URL=http://localhost:8000" > frontend/.env
```

An example file is provided at `frontend/.env.example`.

The development server will start on http://localhost:5173 and automatically reload when files change.

## Running tests

Ensure dependencies are installed (preferably inside a virtual environment):

```bash
pip install -r backend/requirements.txt
pip install pytest
```

Run the test suite with:

```bash
pytest
```

## Backend dependencies

The backend uses a small set of Python packages including FastAPI, uvicorn,
pyswisseph, pandas and httpx. Exact versions are specified in
[`backend/requirements.txt`](backend/requirements.txt). A `requirements.lock`
file with the same pinned versions is also provided for convenience.

## License

This project is licensed under the [MIT License](LICENSE).

Shadbala-radar is an experimental application to compute the *Shadbala* (six-fold strength) of planets and visualize those metrics on a radar chart. The backend exposes a simple FastAPI service that calculates the data using the Swiss Ephemeris. A small frontend will eventually request this API and render the radar visualization in the browser.

## Installation

### Backend

Use a Python 3 environment and install the backend dependencies:

```bash
pip install -r backend/requirements.txt
```

### Frontend

The frontend is a small React application that renders a D3 line chart showing the Sun's Shadbala components over time. Install its dependencies with:

```bash
npm install
```

## Running the server

Start the FastAPI application from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at `http://localhost:8000`.

The backend reads a comma-separated list of allowed CORS origins from the
`ALLOWED_ORIGINS` environment variable. If this variable is not set it
defaults to `http://localhost:5173` and `http://127.0.0.1:5173`.

When using the React frontend during development the site typically runs on
`http://localhost:5173` (or `127.0.0.1:5173`). Ensure this URL is included in
`ALLOWED_ORIGINS`; otherwise the browser may report a "Failed to fetch" error
when submitting the form. When developing in GitHub Codespaces you will need to
add the Codespaces URL for the frontend (for example
`https://5173-<yourid>.app.github.dev`). The value in `ALLOWED_ORIGINS` must
match the URL used to serve the React app. You can start the backend in a
Codespace with:

```bash
export ALLOWED_ORIGINS=https://5173-<yourid>.app.github.dev
uvicorn backend.app.main:app --reload
```

### Querying Shadbala values

`/balas` returns rows sampled every five minutes. You may provide an
`hours_ahead` value (the previous behaviour) or explicitly specify `start` and
`end` datetimes in the `America/New_York` timezone. The range may not exceed 24
hours.

Example with a custom range:

```bash
curl "http://localhost:8000/balas?start=2020-01-01T00:00&end=2020-01-01T01:00&lat=37.7749&lon=-122.4194"
```

## Project purpose

The goal is to provide an easy way to explore planetary strengths over time. The computed Shadbala values will be plotted on an interactive radar chart, allowing users to see how each component of the strength varies throughout the day for a given location.

