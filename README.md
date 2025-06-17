# Shadbala-radar
<<<<< codex/define-project-metadata-and-dependencies

This project contains a FastAPI backend and a React frontend. The frontend uses Vite and D3 to display interactive charts.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

The development server will start on <http://localhost:5173> and automatically reload when files change.
=======
<<<<<< codex/add-license-file-and-mention-in-readme
Shadbala-radar

<<<<< codex/create-tests-for-row-function-and-/balas-endpoint
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
=======
<<<<< codex/specify-exact-versions-for-dependencies
## Backend dependencies

The backend uses a small set of Python packages. Exact versions are
specified in [`backend/requirements.txt`](backend/requirements.txt). A
`requirements.lock` file with the same pinned versions is also provided
for convenience.
=======
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

A placeholder `frontend` directory is provided. Once the JavaScript application is implemented, install its dependencies with:

```bash
npm install
```

## Running the server

Start the FastAPI application from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at `http://localhost:8000`. A GET request to `/balas` returns Shadbala data for a series of timestamps. Example:

```bash
curl "http://localhost:8000/balas?hours_ahead=1&lat=37.7749&lon=-122.4194"
```

## Project purpose

The goal is to provide an easy way to explore planetary strengths over time. The computed Shadbala values will be plotted on an interactive radar chart, allowing users to see how each component of the strength varies throughout the day for a given location.
