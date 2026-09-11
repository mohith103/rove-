# ROVE — Multi-Agent Mars Rover Simulation & Research Platform

**A full-stack AI research platform for autonomous rover decision-making.**

ROVE is a Mars rover simulation in which an autonomous AI commander navigates a 20×20 terrain grid, collects scientific samples, manages limited resources (energy, oxygen, water, food, battery, health), and returns safely to base while dealing with dynamic weather and random equipment failures.

The project ships with **four distinct AI architectures** — Random, Rule-Based, PPO (reinforcement learning), and a Multi-Agent Committee of four specialists — all sharing a common `act(state) -> int` interface, enabling direct comparison on real, reproducible metrics.

Beyond the live simulation, ROVE includes a **complete research platform**: mission replay with frame-by-frame scrubbing, analytics dashboards, counterfactual analysis ("what if the rover had returned earlier?"), automatic failure analysis, and a batch experiment lab for agent benchmarking.

Built on a **deterministic simulation core** (seeded NumPy generators ensure byte-identical results for the same seed), the system streams live state updates over WebSockets to a React + TypeScript mission-control dashboard. The backend is FastAPI; the frontend uses Vite, Tailwind CSS v4, and Recharts. Reinforcement learning uses PyTorch and Stable-Baselines3 with a Gymnasium-compatible environment.

> **Research / educational simulation.** Not affiliated with NASA. This is a portfolio-grade demonstration of reinforcement learning, multi-agent systems, explainable AI, and full-stack engineering — not flight software.

---

## Table of Contents

1. [What Is ROVE?](#1-what-is-rove)
2. [Key Features](#2-key-features)
3. [AI Architectures](#3-ai-architectures)
4. [Detailed Architecture](#4-detailed-architecture)
5. [Quickstart — Docker (Easiest)](#5-quickstart--docker-easiest)
6. [Quickstart — Local Development (Full Walkthrough)](#6-quickstart--local-development-full-walkthrough)
7. [Run Commands — Copy & Paste](#7--run-commands--copy--paste)
8. [Complete End-to-End Execution Guide](#8-complete-end-to-end-execution-guide)
9. [Using the App — Step by Step](#9-using-the-app--step-by-step)
10. [Configuration](#10-configuration)
11. [Project Structure](#11-project-structure)
12. [Testing & Verification](#12-testing--verification)
13. [API Reference](#13-api-reference)
14. [Design Principles](#14-design-principles)
15. [Debugging Stories](#15-debugging-stories)
16. [Limitations & Honest Notes](#16-limitations--honest-notes)
17. [Roadmap / Future Work](#17-roadmap--future-work)
18. [FAQ](#18-faq)
19. [License](#19-license)

---

## 1. What Is ROVE?

ROVE is a **Mars rover simulation** with a **mission-control dashboard** and **four different AI architectures** you can compare side by side.

The idea:

- A rover sits on a 20×20 grid of Mars terrain.
- There are science sites to visit, resources to manage (energy, oxygen, water, food, battery, health), and random events like dust storms and wheel failures.
- An AI commander decides what the rover should do every step.
- Goal: **collect 3 samples and return safely to base** before resources run out or time expires.

The project ships with four AI commanders:

| Architecture | What it is |
|--------------|------------|
| **Random** | Baseline — picks actions randomly |
| **Rule-Based** | Hand-crafted IF-THEN rules with BFS pathfinding |
| **PPO** | Trained reinforcement-learning agent (PyTorch) |
| **Multi-Agent** | 4 specialists (Navigation / Science / Safety / Resource) voting |

Plus **research tools**:

- **Mission Replay** — scrub through any past mission
- **Analytics** — charts of every resource over time
- **Counterfactual Analysis** — "What if the rover had returned earlier?"
- **Failure Analysis** — automatic root-cause reports
- **Experiment Lab** — run batches of missions and compare agents

---

## 2. Key Features

### Live Mission Control
- Interactive SVG Mars map with pan/zoom/hover
- Rover trail that fades with age
- Resource bars (energy, oxygen, water, food, battery, health, comms)
- AI Commander panel with reasoning, confidence, risk
- Specialist votes visible in multi-agent mode
- Event log with SOL timestamps
- Pause / resume / speed controls (1× to 10×)

### Research Platform
- Mission replay with frame-by-frame scrubbing
- Analytics charts + automatic failure analysis
- Counterfactual analysis with side-by-side timeline comparison
- Experiment Lab for batch runs and agent comparison

### Under the Hood
- Deterministic simulation (same seed → byte-identical results)
- Weather system with 5 states
- 7 equipment failure types
- 4 difficulty tiers
- BFS pathfinding
- Post-hoc explainability
- WebSocket streaming every ~0.5s

---

## 3. AI Architectures

All four agents implement the same `act(state) -> int` interface, so they're directly swappable.

### Random Agent
Picks a uniformly random action. Baseline. ~0% success.

### Rule-Based Agent
Priority-ordered IF-THEN rules:

1. If oxygen < 25% → return to base
2. If energy < 20% → return to base (or recharge if there)
3. If health < 40% → repair
4. If at base + energy < 80% → recharge
5. If on an uncollected science site → collect
6. If cargo full → return to base
7. If enough samples → head home
8. Otherwise → **BFS move toward nearest uncollected site**

### PPO Agent
| Property | Value |
|----------|-------|
| Observation | 66 floats |
| Action | Discrete(11) |
| Algorithm | PPO with 4 parallel environments |
| Network | 64×64 MLP |
| Training | 200,000 timesteps (~30 min CPU) |

### Multi-Agent Committee
Four specialists propose actions each step. A meta-commander combines votes:

```
score[action] = Σ (mode_weight[specialist] × proposal_weight)
```

| Mode | Navigation | Science | Safety | Resource |
|------|-----------:|--------:|-------:|---------:|
| Science | 0.7 | **1.5** | 0.8 | 0.7 |
| Survival | 0.8 | 0.5 | **1.8** | **1.5** |
| Exploration | **1.5** | 0.8 | 0.9 | 0.9 |
| Balanced | 1.0 | 1.0 | 1.0 | 1.0 |

---

## 4. Detailed Architecture

### 4.1 — System Overview

```
                                  ┌───────────────────────────────────────┐
                                  │           USER (Browser)              │
                                  │  Opens http://localhost:5173          │
                                  └───────────────────┬───────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND  ·  React 18 + TypeScript                        │
│  Built with Vite  ·  Styled with Tailwind CSS v4  ·  Charts with Recharts    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Pages                                                                 │ │
│  │  ├── MissionControl   → setup screen + live dashboard                  │ │
│  │  ├── ReplayPage       → frame-by-frame scrubbing                       │ │
│  │  ├── AnalyticsPage    → charts + failure analysis                      │ │
│  │  └── ExperimentLabPage → batch runs and comparison                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Components                                                            │ │
│  │  ├── TopBar                (status, SOL, pause/resume, speed)          │ │
│  │  ├── MarsMap               (SVG grid + pan/zoom)                       │ │
│  │  │   ├── TerrainCell       (colored rect per cell)                     │ │
│  │  │   ├── RoverMarker       (pulsing halo)                              │ │
│  │  │   ├── RoverTrail        (fading polyline)                           │ │
│  │  │   ├── ScienceMarker     (diamond + pulse)                           │ │
│  │  │   └── MapLegend         (terrain key)                               │ │
│  │  ├── ResourcePanel         (7 resource bars + position)                │ │
│  │  ├── CommanderPanel        (AI reasoning + specialist votes)           │ │
│  │  ├── EventFeed             (auto-scrolling log)                        │ │
│  │  ├── MissionSetup          (config screen)                             │ │
│  │  ├── MissionCompleteOverlay                                            │ │
│  │  ├── CounterfactualPanel   (what-if comparison)                        │ │
│  │  ├── FailureAnalysisPanel  (root-cause report)                         │ │
│  │  └── analytics/experiments (charts, tables, bars)                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Hooks & Services                                                      │ │
│  │  ├── useMissionStream    → WebSocket + REST backfill hook              │ │
│  │  ├── api.ts              → typed REST client                           │ │
│  │  └── websocket.ts        → native WebSocket wrapper                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  │  HTTP  +  WebSocket
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND  ·  FastAPI  (Python 3.11)                        │
│  Served by Uvicorn  ·  Pydantic schemas for all I/O                          │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  REST Endpoints                                                        │ │
│  │  ├── GET    /health             → health check                         │ │
│  │  ├── GET    /models             → list of available agents             │ │
│  │  ├── POST   /missions           → create + start a mission             │ │
│  │  ├── GET    /missions           → list all missions                    │ │
│  │  ├── GET    /missions/{id}      → full mission detail + state          │ │
│  │  ├── POST   /missions/{id}/pause                                       │ │
│  │  ├── POST   /missions/{id}/resume                                      │ │
│  │  ├── POST   /missions/{id}/action                                      │ │
│  │  ├── GET    /missions/{id}/actions                                     │ │
│  │  ├── GET    /missions/{id}/replay   → frame-by-frame history           │ │
│  │  ├── POST   /experiments            → run batch                        │ │
│  │  ├── POST   /counterfactual/{id}    → fork a completed mission         │ │
│  │  └── GET    /analysis/{id}          → failure analysis                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WebSocket                                                             │ │
│  │  └── /missions/{id}/stream   → state snapshot every ~0.5s              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Service Layer                                                         │ │
│  │  ├── MissionService         → thread-safe in-memory registry           │ │
│  │  ├── MissionRunner          → background thread per mission            │ │
│  │  ├── ExperimentService      → runs batches of missions                 │ │
│  │  ├── CounterfactualService  → replays decisions + forks timeline       │ │
│  │  └── FailureAnalysisService → parses frames + events for root cause    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  │  Python imports
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SIMULATION  ·  Pure Python (no AI, no HTTP)               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  MarsEnvironment                                                       │ │
│  │  ├── terrain      → 20×20 NumPy grid of TerrainType                    │ │
│  │  ├── rover        → position + 8 resource fields                       │ │
│  │  ├── base         → recharge point at (0,0)                            │ │
│  │  ├── science_sites → 5 randomly placed targets                         │ │
│  │  ├── weather      → 5 states, transitions every ~50 steps              │ │
│  │  ├── events       → 7 failure types, ~1% chance per step               │ │
│  │  └── reward       → tuned signal for RL                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Determinism                                                           │ │
│  │  ├── reset(seed)          → numpy Generator, seed offset per subsystem │ │
│  │  ├── same seed → byte-identical terrain, sites, weather, events        │ │
│  │  └── enables counterfactual analysis + reproducible experiments        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Action Space (11 actions)                                             │ │
│  │  0 MOVE_NORTH   1 MOVE_SOUTH   2 MOVE_EAST    3 MOVE_WEST              │ │
│  │  4 COLLECT      5 ANALYZE      6 RETURN       7 RECHARGE               │ │
│  │  8 REPAIR       9 COMMUNICATE  10 WAIT                                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  │  .act(state) → int
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AGENTS  ·  All share the same interface                │
│                                                                              │
│  ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐  │
│  │  RandomAgent        │   │  RuleBasedAgent     │   │  PPO (SB3)       │  │
│  │  ───────            │   │  ───────            │   │  ───────         │  │
│  │  • uniform random   │   │  • priority rules   │   │  • 66-float obs  │  │
│  │  • baseline only    │   │  • BFS pathfinding  │   │  • 64×64 MLP     │  │
│  │                     │   │  • hysteresis-free  │   │  • trained 200k  │  │
│  └─────────────────────┘   └─────────────────────┘   └──────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  MultiAgentCommander                                                   │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │ │
│  │  │ Navigation   │ │ Science      │ │ Safety       │ │ Resource     │  │ │
│  │  │ Specialist   │ │ Specialist   │ │ Specialist   │ │ Specialist   │  │ │
│  │  │ ───────────  │ │ ───────────  │ │ ───────────  │ │ ───────────  │  │ │
│  │  │ BFS target   │ │ collect on   │ │ return when  │ │ efficiency,  │  │ │
│  │  │ routing      │ │ site, cargo  │ │ critical,    │ │ avoid costly │  │ │
│  │  │              │ │ full → home  │ │ repair,      │ │ terrain      │  │ │
│  │  │              │ │              │ │ recharge     │ │              │  │ │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘  │ │
│  │         │                │                │                │          │ │
│  │         └────────────────┴────────┬───────┴────────────────┘          │ │
│  │                                   ▼                                    │ │
│  │                    Weighted vote by mode weights                       │ │
│  │                    score[a] = Σ w[mode][specialist] × w[proposal]      │ │
│  │                                   │                                    │ │
│  │                                   ▼                                    │ │
│  │                          Final action chosen                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Wrappers                                                              │ │
│  │  ├── Commander            → policy + planner + explainer (single-agent)│ │
│  │  ├── Planner              → evaluates short-horizon plans              │ │
│  │  ├── Explainer            → post-hoc reason + confidence + risk        │ │
│  │  └── Pathfinding (BFS)    → routes around mountains                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  │  Persistence (frame history)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STORAGE  ·  In-memory (per-mission)                      │
│                                                                              │
│  ├── frames[]        → snapshot after every step (up to 2000)                │
│  ├── decisions[]     → AI decision log (used for replay + counterfactual)    │
│  ├── events[]        → full mission log                                      │
│  └── terrain         → the original grid                                     │
│                                                                              │
│  → Feeds: replay, analytics, counterfactual, failure analysis                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 — Data Flow: Creating a Mission

```
1. User clicks "Launch Mission" in the browser
        │
        ▼
2. Frontend POSTs /missions with config JSON
        │
        ▼
3. Backend MissionService.create_mission()
        │
        ├── load_config_for_difficulty()      → read YAML + Pydantic validation
        ├── MarsEnvironment(cfg)              → instantiate simulation
        ├── env.reset(seed)                   → deterministic world
        ├── _build_policy(agent)              → construct AI
        └── Mission(...)                      → store in registry
        │
        ▼
4. MissionRunner.start() in background thread
        │
        ▼
5. Every step: commander.decide(state)
        │
        ├── policy.act(state)              → proposal
        ├── planner.choose(state)          → alternative plans
        ├── safety layer                    → hard overrides if critical
        └── explainer.explain()             → reason + confidence + risk
        │
        ▼
6. env.step(action) → new state + reward
        │
        ├── Append snapshot to frames[]
        ├── Append decision to decisions[]
        └── Append any events to events[]
        │
        ▼
7. WebSocket broadcasts state every ~0.5s
        │
        ▼
8. Frontend receives, updates UI live
```

### 4.3 — Data Flow: Counterfactual Analysis

```
1. User opens Replay, scrubs to SOL N, clicks "Ask: What if?"
        │
        ▼
2. Frontend POSTs /counterfactual/{id} with override config
        │
        ▼
3. CounterfactualService.run_counterfactual()
        │
        ├── Rebuild ACTUAL timeline from stored frames[]
        │
        └── Run COUNTERFACTUAL:
            ├── Reset env with same seed           (deterministic)
            ├── Replay decisions 1..N              (reproduces exact state at fork)
            ├── Apply override policy for K steps  (diverge)
            ├── Resume original policy             (run to completion)
            └── Capture new frames[]
        │
        ▼
4. Compare two timelines → generate verdict
        │
        ▼
5. Return both timelines → UI shows side-by-side
```

### 4.4 — Component Dependency Graph (Backend)

```
backend/app/main.py
├── api/missions.py         ─► services/mission_service.py
│                              ├── simulation/environment.py
│                              ├── simulation/config.py
│                              ├── agents/commander.py
│                              ├── agents/planner.py
│                              ├── agents/random_agent.py
│                              ├── agents/rule_based.py
│                              └── agents/specialists/commander.py
├── api/models.py
├── api/experiments.py      ─► services/experiment_service.py
├── api/counterfactual.py   ─► services/counterfactual_service.py
├── api/analysis.py         ─► services/failure_analysis_service.py
└── websocket/stream.py     ─► api/missions.py (shares MissionService singleton)
```

### 4.5 — Component Dependency Graph (Frontend)

```
src/App.tsx
└── pages/MissionControl.tsx
    ├── components/MissionSetup.tsx
    ├── components/TopBar.tsx
    ├── components/MarsMap.tsx
    │   └── components/mars/{MarsGrid, MapLegend, usePanZoom}
    ├── components/CommanderPanel.tsx
    ├── components/ResourcePanel.tsx
    ├── components/EventFeed.tsx
    ├── components/MissionCompleteOverlay.tsx
    │   ├── pages/ReplayPage.tsx        (on Replay)
    │   │   └── components/counterfactual/CounterfactualPanel.tsx
    │   └── pages/AnalyticsPage.tsx     (on View Analytics)
    │       ├── components/analytics/{MetricCard, ResourceChart, RiskChart}
    │       └── components/analysis/FailureAnalysisPanel.tsx
    ├── pages/ExperimentLabPage.tsx     (on Experiment Lab tab)
    │   └── components/experiments/{AgentBar, ResultsTable}
    └── hooks/useMissionStream.ts       (WebSocket + REST backfill)
```

### 4.6 — Determinism Guarantee

Every random source uses a seeded `numpy.random.Generator`:

| Subsystem | Seed Offset |
|-----------|-------------|
| Terrain generation | `seed` |
| Science site placement | `seed` |
| Weather transitions | `seed + 1` |
| Event rolls | `seed + 2` |

**Consequence:** Two missions with the same seed produce **byte-identical** results. This is the foundation of counterfactual analysis and reproducible experiments.

---

## 5. Quickstart — Docker (Easiest)

**Prerequisites:** Docker Desktop installed and running.

```bash
git clone <your-repo-url>
cd rove
docker compose up --build
```

When it finishes:

- **Frontend:** http://localhost:5173
- **Backend API docs:** http://localhost:8000/docs

Stop with `Ctrl + C`, then `docker compose down`.

---

## 6. Quickstart — Local Development (Full Walkthrough)

**Prerequisites:** Python 3.11+, Node.js 18+, Git.

### Backend (Terminal 1)

```bash
git clone <your-repo-url>
cd rove
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install "fastapi>=0.110.0" "uvicorn[standard]>=0.29.0" "httpx>=0.27.0" "websockets>=12.0"
pip install "torch>=2.2.0" "stable-baselines3>=2.2.0" "tensorboard>=2.15.0"
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

**Leave this running.** Verify with: `curl http://127.0.0.1:8000/health`

### Frontend (Terminal 2)

```bash
cd ~/Desktop/rove/frontend
npm install
npm run dev
```

**Leave this running.** Open http://localhost:5173

---

## 7. ⚡ Run Commands — Copy & Paste

**Everything you need to run this project, in order. Just commands.**

### 7.1 — One-Time Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd rove

# Backend setup
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install "fastapi>=0.110.0" "uvicorn[standard]>=0.29.0" "httpx>=0.27.0" "websockets>=12.0"
pip install "torch>=2.2.0" "stable-baselines3>=2.2.0" "tensorboard>=2.15.0"

# Frontend setup
cd frontend
npm install
cd ..
```

### 7.2 — Start Backend (Terminal 1)

```bash
cd ~/Desktop/rove
source .venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 7.3 — Start Frontend (Terminal 2)

```bash
cd ~/Desktop/rove/frontend
npm run dev
```

### 7.4 — Open the App

```
http://localhost:5173
```

### 7.5 — Run Tests

```bash
# Backend tests (Terminal 3)
cd ~/Desktop/rove
source .venv/bin/activate
pytest -v

# Frontend lint
cd ~/Desktop/rove/frontend
npm run lint
```

### 7.6 — Run Headless Demo

```bash
cd ~/Desktop/rove
source .venv/bin/activate
python scripts/demo.py --agent multi_agent --difficulty hard
```

### 7.7 — Train PPO Model

```bash
cd ~/Desktop/rove
source .venv/bin/activate
python -m reinforcement_learning.train --timesteps 200000 --run-name full_run
```

### 7.8 — Evaluate PPO Model

```bash
cd ~/Desktop/rove
source .venv/bin/activate
python -m reinforcement_learning.evaluate --episodes 20
```

### 7.9 — View Training Curves

```bash
cd ~/Desktop/rove
source .venv/bin/activate
tensorboard --logdir reinforcement_learning/logs/tensorboard
# Open http://localhost:6006
```

### 7.10 — Run with Docker

```bash
cd ~/Desktop/rove
docker compose up --build
# Open http://localhost:5173

# Stop
docker compose down
```

### 7.11 — Stop Everything

```bash
pkill -f uvicorn
pkill -f vite
```

### 7.12 — Quick Command Reference

| Task | Command |
|------|---------|
| Activate venv | `source .venv/bin/activate` |
| Start backend | `cd ~/Desktop/rove && source .venv/bin/activate && uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` |
| Start frontend | `cd ~/Desktop/rove/frontend && npm run dev` |
| Kill both | `pkill -f uvicorn && pkill -f vite` |
| Run backend tests | `cd ~/Desktop/rove && source .venv/bin/activate && pytest -v` |
| Run frontend lint | `cd ~/Desktop/rove/frontend && npm run lint` |
| Headless demo | `python scripts/demo.py` |
| Train PPO | `python -m reinforcement_learning.train --timesteps 200000` |
| Evaluate PPO | `python -m reinforcement_learning.evaluate --episodes 20` |
| TensorBoard | `tensorboard --logdir reinforcement_learning/logs/tensorboard` |
| Docker up | `docker compose up --build` |
| Docker down | `docker compose down` |
| Backend health | `curl http://127.0.0.1:8000/health` |
| API docs | `http://127.0.0.1:8000/docs` |
| Dashboard | `http://localhost:5173` |

---

## 8. Complete End-to-End Execution Guide

### 8.1 — Verify Installation

```bash
curl http://127.0.0.1:8000/health
# → {"status":"ok","version":"0.1.0"}

curl http://127.0.0.1:8000/models
# → {"agents":[{"name":"random",...},{"name":"rule_based",...},{"name":"ppo",...}]}
```

### 8.2 — Run Backend Tests

```bash
cd ~/Desktop/rove
source .venv/bin/activate
pytest -v
```

Expected: 52 tests passing, ~5 seconds.

### 8.3 — Run Frontend Lint

```bash
cd ~/Desktop/rove/frontend
npm run lint
```

Expected: zero errors, zero warnings.

### 8.4 — Run the Headless Demo

```bash
cd ~/Desktop/rove
source .venv/bin/activate
python scripts/demo.py --agent multi_agent --difficulty hard --max-steps 40 --speed 0
```

Runs a full mission in the terminal and prints step-by-step output plus a summary.

### 8.5 — Launch a Mission from the Browser

1. Open http://localhost:5173
2. Configure: Difficulty = Medium, Agent = Rule-Based, Mode = Balanced, Architecture = Single Agent
3. Click **Launch Mission**
4. Watch the live dashboard

### 8.6 — Try Multi-Agent Mode

1. Click **New Mission**
2. Choose **Multi-Agent (4 specialists)**
3. Launch
4. Watch specialist votes in the AI Commander panel

### 8.7 — Test Replay

1. Let a mission finish
2. Click **Replay** in the completion overlay
3. Scrub, play, pause, speed up

### 8.8 — Test Counterfactual Analysis

1. Open a replay
2. Scrub to any SOL
3. Click **Ask: What if?**
4. Choose override policy (Return to base, Recharge, Repair, Wait)
5. Set duration
6. Click **Run Counterfactual**
7. See two-timeline comparison with verdict

### 8.9 — Test Experiment Lab

1. Top nav → **Experiment Lab**
2. Configure agents, difficulties, episodes
3. Click **Run Experiment**
4. See results table

### 8.10 — Test the API with curl

```bash
# Create a mission
curl -X POST http://127.0.0.1:8000/missions \
  -H "Content-Type: application/json" \
  -d '{
    "difficulty": "easy",
    "agent": "rule_based",
    "mode": "balanced",
    "seed": 1,
    "speed": 5.0,
    "multi_agent": false
  }'

# Get mission state
curl http://127.0.0.1:8000/missions/MISSION_ID | python -m json.tool

# Run a counterfactual
curl -X POST http://127.0.0.1:8000/counterfactual/MISSION_ID \
  -H "Content-Type: application/json" \
  -d '{"fork_step": 20, "override": "force_return_to_base", "override_duration": 10}'

# Run a batch experiment
curl -X POST http://127.0.0.1:8000/experiments \
  -H "Content-Type: application/json" \
  -d '{"agents":["random","rule_based"],"difficulties":["medium"],"mode":"balanced","episodes":10,"seed":42}'
```

### 8.11 — Train a PPO Model

```bash
cd ~/Desktop/rove
source .venv/bin/activate

# Quick smoke test (~2 min)
python -m reinforcement_learning.train --timesteps 20000 --run-name smoke_test

# Full training (~30 min)
python -m reinforcement_learning.train --timesteps 200000 --run-name full_run
```

### 8.12 — Evaluate PPO

```bash
python -m reinforcement_learning.evaluate --episodes 20
```

### 8.13 — Stop Everything

```bash
pkill -f uvicorn && pkill -f vite
```

### 8.14 — Troubleshooting

| Problem | Fix |
|---------|-----|
| `uvicorn: command not found` | `source .venv/bin/activate` first |
| `ModuleNotFoundError: backend` | Run from `~/Desktop/rove` |
| `Address already in use` | `pkill -f uvicorn` |
| `npm: command not found` | Install Node.js from nodejs.org |
| Blank frontend page | Hard refresh (`Cmd + Shift + R`); check backend is running |
| API 404 in frontend | Restart backend after code changes |
| WebSocket error | Backend not running, or mission already completed |
| PPO option fails | No trained model exists — use rule_based or random |

---

## 9. Using the App — Step by Step

### Step 1 — Setup Screen
Choose difficulty, agent, mode, architecture, speed, and seed. Click **Launch Mission**.

### Step 2 — Live Dashboard
Mars map on the left, AI Commander top right, resource bars bottom right, mission log at the bottom.

### Step 3 — Mission Complete
Summary card appears. Choose **Close**, **Replay**, or **View Analytics**.

### Step 4 — Replay
Scrub through the mission with play/pause/speed controls.

### Step 5 — Counterfactual
In replay, scrub to any SOL, click **Ask: What if?**, choose an override, click **Run Counterfactual**.

### Step 6 — Experiment Lab
Top nav → **Experiment Lab**. Configure a batch, run, and compare.

---

## 10. Configuration

All simulation parameters live in YAML under `configs/`.

### `configs/default.yaml` (excerpt)

```yaml
map:
  width: 20
  height: 20
  seed: 42

terrain:
  plain: 0.55
  rock: 0.15
  crater: 0.10
  mountain: 0.05
  sand: 0.15

movement_cost:
  plain: 1.0
  rock: 2.0
  crater: 2.5
  mountain: 3.5
  sand: 1.5

rover:
  initial_energy: 100.0
  initial_water: 80.0
  initial_oxygen: 90.0
  initial_food: 100.0
  initial_battery_health: 100.0
  initial_rover_health: 100.0
  cargo_capacity: 5

consumption:
  water_per_tick: 0.05
  oxygen_per_tick: 0.03
  food_per_tick: 0.02
  battery_degradation_per_tick: 0.02
  rover_health_degradation_per_tick: 0.01

base:
  x: 0
  y: 0
  recharge_rate: 10.0

science:
  num_sites: 5
  min_value: 50
  max_value: 200
  min_difficulty: 1
  max_difficulty: 5

mission:
  max_steps: 400
  success_samples_required: 3

weather:
  change_probability: 0.02
  probabilities:
    clear: 0.55
    dusty: 0.20
    dust_storm: 0.15
    cold_snap: 0.07
    extreme_cold: 0.03

events:
  base_probability: 0.01
  probabilities:
    solar_panel_failure: 0.15    wheel_failure: 0.20
    battery_degradation: 0.10
    communication_loss: 0.15
    navigation_sensor_failure: 0.10
    water_leak: 0.15
    rover_overheating: 0.15

reward:
  per_step_penalty: -0.05
  move_penalty: -0.1
  blocked_move_penalty: -0.5
  collect_base_reward: 100.0
  collect_value_multiplier: 0.5
  analyze_reward: 5.0
  invalid_action_penalty: -1.0
  mission_success_reward: 500.0
  mission_failure_penalty: -1000.0

training:
  timesteps: 200000
  seed: 42
  n_envs: 4
  learning_rate: 0.0003
  net_arch: [64, 64]
```

### Difficulty Presets

| Difficulty | Max Steps | Event Prob | Dust Storm Prob |
|-----------|----------:|-----------:|----------------:|
| Easy | 500 | 0.003 | 0.04 |
| Medium | 400 | 0.01 | 0.15 |
| Hard | 300 | 0.02 | 0.25 |
| Extreme | 200 | 0.04 | 0.35 |

---

## 11. Project Structure

```
rove/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── api/
│       ├── schemas/
│       ├── services/
│       └── websocket/
│
├── simulation/
│   ├── environment.py
│   ├── rover.py
│   ├── terrain.py
│   ├── weather.py
│   ├── events.py
│   ├── base.py
│   ├── state.py
│   └── config.py
│
├── agents/
│   ├── base_agent.py
│   ├── random_agent.py
│   ├── rule_based.py
│   ├── pathfinding.py
│   ├── explainer.py
│   ├── planner.py
│   ├── commander.py
│   └── specialists/
│       ├── base.py
│       ├── navigation.py
│       ├── science.py
│       ├── safety.py
│       ├── resource.py
│       └── commander.py
│
├── reinforcement_learning/
│   ├── env.py
│   ├── train.py
│   ├── evaluate.py
│   ├── callbacks.py
│   ├── models/
│   └── logs/
│
├── experiments/
│   ├── baseline.py
│   ├── robustness.py
│   ├── peek_observation.py
│   ├── explain_demo.py
│   ├── plan_demo.py
│   └── results/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── theme.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.production
│
├── configs/
│   ├── default.yaml
│   ├── easy.yaml
│   ├── medium.yaml
│   ├── hard.yaml
│   └── extreme.yaml
│
├── scripts/
│   └── demo.py
│
├── tests/
│   └── (52+ test files)
│
├── docs/
│   └── ARCHITECTURE.md
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 12. Testing & Verification

### Backend — 52+ tests

```bash
cd ~/Desktop/rove
source .venv/bin/activate
pytest -v
```

| Module | Tests |
|--------|------:|
| `test_agents.py` | 6 |
| `test_commander.py` | 5 |
| `test_environment.py` | 6 |
| `test_event.py` | 4 |
| `test_explainer.py` | 6 |
| `test_planner.py` | 5 |
| `test_rl_env.py` | 7 |
| `test_rl_training.py` | 2 |
| `test_weather.py` | 4 |
| `test_api.py` | 6 |

### Frontend — Lint

```bash
cd ~/Desktop/rove/frontend
npm run lint
```

### Headless End-to-End

```bash
python scripts/demo.py --max-steps 40
```

---

## 13. API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/models` | List available agents |
| POST | `/missions` | Create and start a mission |
| GET | `/missions` | List all missions |
| GET | `/missions/{id}` | Full mission detail |
| POST | `/missions/{id}/pause` | Pause |
| POST | `/missions/{id}/resume` | Resume |
| POST | `/missions/{id}/action` | Apply manual action |
| GET | `/missions/{id}/actions` | List action names |
| GET | `/missions/{id}/replay` | Frame history |
| POST | `/experiments` | Run a batch |
| POST | `/counterfactual/{id}` | Fork a mission |
| GET | `/analysis/{id}` | Failure analysis |
| WS | `/missions/{id}/stream` | Live streaming |

---

## 14. Design Principles

1. **Separation of concerns** — Simulation, agents, backend, frontend are independent
2. **Determinism** — Same seed → byte-identical results
3. **Explainability first** — Every decision has reason, confidence, risk
4. **No fabricated results** — All metrics from real runs
5. **Reproducibility** — Seeds, configs, versions recorded
6. **Clean interfaces** — Shared `.act(state) -> int` protocol

---

## 15. Debugging Stories

Real bugs found and fixed:

1. **`self.events` name collision** — log list vs. event engine → renamed log to `self.event_log`
2. **Event log gaps** — backend sent only last 50 events; frontend replaced instead of accumulating → client-side deduplication
3. **Rover stuck on mountains** — greedy movement → BFS pathfinding
4. **Cursor misalignment in SVG** — `getBoundingClientRect()` → `svg.getScreenCTM().inverse()`
5. **`setState` inside `useEffect`** — moved to callbacks + `useMemo`
6. **Commander override dead code** — risk threshold → plan margin check
7. **Counterfactual 404** — uvicorn cached old app → restart

---

## 16. Limitations & Honest Notes

**What ROVE is not:**
- Not flight-grade simulation
- Not affiliated with NASA
- Not production-ready
- Not built on a pretrained foundation model

**Known limitations:**
- PPO trained on medium difficulty only
- Rule-based uses simple BFS
- Weather/event probabilities are approximations
- 20×20 grid is a toy scale
- In-memory mission storage
- No authentication
- Explanations are post-hoc

**Performance:**
- Simulation: ~200 steps/second
- Backend: ~10 API requests/second
- Frontend: 60 fps SVG
- PPO training: 200k timesteps in ~30 min CPU

---

## 17. Roadmap / Future Work

- Persistence (PostgreSQL)
- Authentication
- More specialists
- Continuous training
- Map size selector
- Real Mars data integration
- Multiplayer

---

## 18. FAQ

**Do I need Docker?** No.
**Do I need a GPU?** No.
**How long is a mission?** 1–2 min at 3× speed.
**Change difficulty in UI?** Yes.
**PPO fails?** Use rule_based or random.
**Stop servers?** `pkill -f uvicorn && pkill -f vite`
**Reproduce exactly?** Same seed.
**Add my own agent?** Implement `BaseAgent.act(state) -> int`, register in `mission_service.py`.
**Where are models?** `reinforcement_learning/models/best/best_model.zip`
**Training curves?** `tensorboard --logdir reinforcement_learning/logs/tensorboard`

---

## 19. License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgements

- Potential-based reward shaping (Ng, Harada, Russell 1999)
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) + [Gymnasium](https://gymnasium.farama.org/)
- Visual design inspired by NASA mission-control interfaces

---

## Author

MOHITH PANCHATCHARAM

**Status:** ✅ Complete · **Version:** 1.0.0 · **Tests:** 52+ passing · **Lines of Code:** ~8,500