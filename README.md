# totalSimulation

Unified Multi-Scale Simulation Platform — a web-based interface for 51 scientific simulation tools across 20 research domains, from astrophysics to quantum mechanics to molecular dynamics.

Built with **FastAPI + Celery + Redis** (backend) and **React + Vite + Three.js + Plotly + MolStar** (frontend). All services containerized with Docker Compose.

## Quick Start

```bash
# Clone and start core services
git clone git@github.com:angupesa0611/totalSimulation.git
cd totalSimulation
cp .env.example .env  # or use the default .env
docker compose up -d

# Access the UI
open http://localhost:3100
```

Core services (redis, orchestrator, client) start by default. Specialized workers are opt-in via Docker Compose profiles:

```bash
# Start with molecular dynamics workers (OpenMM GPU, GROMACS, NAMD)
docker compose --profile molecular up -d

# Start with quantum chemistry workers
docker compose --profile electronic up -d

# Start multiple profiles
docker compose --profile molecular --profile continuum --profile fluids up -d
```

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Client     │────▶│   Orchestrator   │────▶│    Redis     │
│  React SPA   │     │  FastAPI + Celery │     │   Broker +   │
│  :3100       │◀────│  :8000           │◀────│   Results    │
│              │  WS │  28 built-in     │     │   :6380      │
└─────────────┘     │  tools           │     └─────────────┘
                     └────────┬─────────┘
                              │ Celery tasks
                    ┌─────────┴──────────┐
                    ▼                    ▼
             ┌────────────┐      ┌────────────┐
             │  Worker N   │ ...  │  Worker N   │
             │  (profile)  │      │  (GPU)      │
             └────────────┘      └────────────┘
```

- **Orchestrator**: FastAPI API + Celery workers for 28 lightweight tools (REBOUND, QuTiP, PySCF, SymPy, etc.)
- **Container workers**: 23 isolated Docker containers for heavy-duty tools (OpenMM, GROMACS, Psi4, FEniCS, LAMMPS, etc.)
- **Client**: React SPA with 3D visualizations (Three.js), 2D plots (Plotly), molecular views (MolStar), and video playback

## Ports

| Service | Port | Description |
|---------|------|-------------|
| Client | 3100 | React SPA (nginx) |
| Orchestrator | 8000 | FastAPI REST + WebSocket API |
| Redis | 6380 | Message broker + result backend |

## Features

### Simulation Tools (51)

Organized into 20 scientific layers:

| Layer | Tools |
|-------|-------|
| Astrophysics | REBOUND, NRPy+, Einstein Toolkit |
| Quantum | QuTiP, PennyLane, Qiskit |
| Molecular | OpenMM, GROMACS, NAMD |
| Electronic | PySCF, Psi4 |
| Analysis | MDAnalysis |
| Multiscale | QM/MM |
| Mechanics | PyBullet |
| Continuum | FEniCS, Elmer, Firedrake |
| Relativity | EinsteinPy |
| Systems Biology | BasiCO, Tellurium |
| Neuroscience | Brian2, NEST |
| Evolution | msprime, SLiM, tskit, simuPOP |
| Chemistry | RDKit, Cantera, Open Babel |
| Materials | Quantum ESPRESSO, LAMMPS |
| Mathematics | SymPy, SageMath, Lean 4, GAP |
| Circuits | Lcapy, PySpice |
| Visualization | Matplotlib, VTK, Manim |
| Fluid Dynamics | OpenFOAM, Dedalus, SU2 |
| Engineering | Pyomo, python-control, NetworkX, PhiFlow |
| Bio-Structure | AlphaFold (deferred), PyRosetta (deferred), COMSOL (deferred) |

### Platform Capabilities

- **48 presets** — one-click launch for common simulations
- **11 named pipelines** — multi-step workflows (e.g., quantum-to-organism, drug discovery)
- **153 tool couplings** — connect outputs of one tool as inputs to another
- **DAG pipeline engine** — parallel execution with dependency resolution
- **Sweep engine** — parameter sweeps with combinatorial/grid/random strategies
- **Export engine** — CSV, JSON, PDF report generation
- **Manim rendering** — animate simulation results as MP4/GIF
- **Documentation system** — built-in docs for every tool, coupling, and pipeline
- **Results browser** — search, filter, paginate, and inspect all simulation results
- **Project management** — organize results into named projects
- **Real-time updates** — WebSocket streaming for simulation/pipeline/sweep progress

### Authentication (Phase 16)

JWT-based authentication, toggleable via environment variable:

```env
# .env
AUTH_ENABLED=true
JWT_SECRET=your-secret-here
```

- **Off by default** — zero friction for local development
- When enabled: all `/api/` and WebSocket endpoints require a Bearer JWT
- User store: JSON file persisted on the results volume
- Endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/status`

### Responsive Layout (Phase 16)

- Desktop (>1024px): full 3-column layout with sidebar, panel, and visualizer
- Tablet (768-1024px): collapsible sidebar
- Mobile (<768px): drawer-based sidebar, bottom navigation bar, full-width panels

### Public Access via Cloudflare Tunnel (Phase 16)

Optional tunnel for public exposure without opening firewall ports:

```bash
docker compose --profile tunnel up -d
```

See `containers/cloudflared/README.md` for setup instructions.

## Docker Compose Profiles

| Profile | Workers |
|---------|---------|
| `molecular` | OpenMM (GPU), GROMACS, NAMD |
| `electronic` | Psi4 |
| `continuum` | FEniCS, Elmer, Firedrake |
| `fluids` | OpenFOAM, Dedalus, SU2 |
| `materials` | Quantum ESPRESSO, LAMMPS |
| `mathematics` | SageMath, Lean 4, GAP |
| `circuits` | PySpice, Qiskit |
| `neuro` | NEST |
| `qmmm` | QM/MM |
| `visualization` | Manim |
| `astro` | Einstein Toolkit |
| `bio-population` | SLiM |
| `cheminformatics` | Open Babel |
| `tunnel` | Cloudflare Tunnel |

## API Overview

### REST Endpoints

```
GET    /health                        — Health check
GET    /api/layers                    — List all layers and tools
GET    /api/presets                   — List all presets
GET    /api/presets/:key              — Get preset parameters
POST   /api/simulate                  — Submit simulation
GET    /api/status/:jobId             — Check job status
POST   /api/simulate/:jobId/cancel    — Cancel running job
GET    /api/results                   — List/search results
GET    /api/results/:jobId            — Get result detail
DELETE /api/results/:jobId            — Delete result
POST   /api/pipeline                  — Submit pipeline
POST   /api/pipeline/dag              — Submit DAG pipeline
POST   /api/sweep/                    — Submit parameter sweep
POST   /api/export/                   — Export results
GET    /api/couplings                 — List tool couplings
GET    /api/pipelines                 — List named pipelines
GET    /api/projects                  — List projects
POST   /api/projects                  — Create project
GET    /api/metrics                   — Platform metrics
POST   /api/auth/register             — Register user (auth)
POST   /api/auth/login                — Login (auth)
GET    /api/auth/status               — Auth status
```

### WebSocket Endpoints

```
/ws/simulation/:jobId   — Real-time simulation progress
/ws/pipeline/:id        — Pipeline step progress
/ws/sweep/:id           — Sweep progress
/ws/status              — Global job tracker
```

## Development

### Backend Tests

```bash
cd orchestrator
pip install pytest PyJWT passlib[bcrypt] pydantic pydantic-settings fastapi httpx
pytest tests/ -v
```

### Frontend Tests

```bash
cd client
npm ci
npm test
```

### CI/CD

GitHub Actions runs on push/PR to `main`:
- **backend-tests**: Python 3.11, pytest (auth module tests)
- **frontend-tests**: Node 20, vitest + build check

## Project Structure

```
totalSimulation/
├── orchestrator/           # FastAPI + Celery backend
│   ├── auth.py             # JWT auth module
│   ├── auth_router.py      # Auth endpoints
│   ├── main.py             # App + middleware
│   ├── router.py           # Core simulation API
│   ├── config.py           # Settings + registries
│   ├── pipeline.py         # Pipeline engine
│   ├── pipeline_dag.py     # DAG pipeline engine
│   ├── sweep.py            # Sweep engine
│   ├── export_engine.py    # Export engine
│   ├── results.py          # Results storage
│   ├── tools/              # 28 built-in tool implementations
│   ├── models/             # Pydantic models
│   ├── websocket/          # WS connection manager
│   ├── manim_converters/   # Result-to-Manim converters
│   └── tests/              # pytest test suite
├── client/                 # React + Vite frontend
│   └── src/
│       ├── App.jsx         # Main app with auth + responsive
│       ├── api/            # Axios API client
│       ├── hooks/          # React hooks (auth, WS, simulation, etc.)
│       ├── components/     # UI components + params
│       ├── visualizers/    # 27 visualization components
│       └── docs/           # Built-in documentation
├── containers/             # 23 worker containers + cloudflared
│   ├── openmm/             # GPU molecular dynamics
│   ├── gromacs/            # High-performance MD
│   ├── cloudflared/        # Cloudflare Tunnel
│   └── ...
├── shared/                 # Presets + schemas
│   ├── examples/           # 50 preset JSON files
│   └── schemas/            # 16 input schemas
├── docker-compose.yml
├── .env
└── .github/workflows/ci.yml
```

## License

Academic use. All rights reserved.
