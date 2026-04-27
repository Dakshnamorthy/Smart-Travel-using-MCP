# Smart Travel Planner

A full-stack travel planning system built with Python, FastAPI, React, and MCP-style tool orchestration.

This project combines:
- A React frontend chat interface
- A Python FastAPI backend
- A multi-agent Python client
- A tool layer for travel data, routing, transport, budgeting, and itinerary generation
- A local RAG data store for travel knowledge


## Architecture Diagram

> Save the provided architecture diagram image into the project root as `architecture_diagram.jpg`.

![Architecture Diagram](architecture_diagram.jpg)


## What this project does

Smart Travel Planner turns natural language travel requests into structured trip plans using:
- destination and itinerary extraction
- attraction discovery
- hotel and restaurant recommendations
- route optimization
- transport and budget estimates
- formatted itinerary creation

The system is designed so tools are the source of truth and the LLM is used mainly for formatting output.


## Folder structure

```
smart_travel_mcp/
├── client/                # Python client logic and agent orchestration
├── config/                # Shared settings and location aliases
├── frontend/              # React application
├── server/                # Backend API and tool implementations
│   ├── tools/             # Travel tools and helper modules
│   └── utils/             # Logger and shared helpers
├── chroma_db/             # Local RAG vector database storage
├── saved_trips/           # Persisted trip plan JSON files
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
└── .env                   # Environment variables and API keys
```


## Core components

### Frontend

- `frontend/src/App.jsx` — main chat interface
- `frontend/src/components/MessageBubble.jsx` — chat message UI
- `frontend/src/components/SavedTrips.jsx` — saved trip management
- LocalStorage saves trip plans in the browser

### Backend

- `server/api.py` — FastAPI REST endpoint at `/chat`
- `server/server.py` — MCP server registration file
- `client/client.py` — main chat router and handler logic
- `client/agents/supervisor.py` — orchestration of planning and finance agents
- `client/agents/planner.py` — attraction, hotel, restaurant, route logic
- `client/agents/finance.py` — transport and budget logic

### Tool layer

Located under `server/tools/`:
- `weather.py` — fetches weather
- `geocode.py` — converts location names to coordinates
- `attraction.py` — finds tourist attractions
- `hotel.py` — finds hotels
- `restaurant.py` — finds restaurants
- `distance.py` — computes distance and travel duration
- `route_optimizer.py` — orders visits and builds daily plans
- `transport.py` — estimates travel mode costs and times
- `budget.py` — builds a budget breakdown
- `currency.py` — converts currencies
- `itinerary.py` — generates final formatted itinerary using LLM
- `summary.py` — creates trip summaries
- `save_trip.py` — saves trips to disk
- `knowledge_rag.py` — retrieves context from local RAG data
- `tool_wrapper.py` — safe call wrapper, fallback handling, observability
- `fallback_data.py` — cached local fallback data for reliability


## How the code works

### Frontend → Backend

1. User types a travel request into React.
2. React sends an HTTP POST to `http://localhost:8000/chat`.
3. FastAPI in `server/api.py` receives the request.
4. `server/api.py` forwards the user message to `client/client.py`.
5. `client/client.py` classifies intent, extracts entities, and routes the request.
6. The chosen handler calls tool functions and agent logic.
7. The response is returned to React and displayed in the chat.


### Backend and MCP

- `server/server.py` defines an MCP server using `FastMCP`.
- It registers all travel tools with `@mcp.tool()`.
- The tools themselves live under `server/tools/` and implement actual API calls.
- The current backend uses direct imports from `server.tools` in `client/client.py`.
- Therefore the MCP server is available as a registered component, but the present route from React to tool functions is handled by the FastAPI + Python client stack.


## Setup

### 1. Create Python environment

```powershell
cd d:\dharani\smart_travel_mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```powershell
cd frontend
npm install
```

### 3. Create `.env`

Create a `.env` file in the project root with values for:

```text
OPENWEATHER_API_KEY=your_openweather_key
OPENTRIPMAP_API_KEY=your_opentripmap_key
ORS_API_KEY=your_openrouteservice_key
EXCHANGE_API_KEY=your_exchange_rate_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```


## Running the project

### Start the backend API

```powershell
cd d:\dharani\smart_travel_mcp
.venv\Scripts\Activate.ps1
python -m server.api
```

This starts FastAPI on `http://localhost:8000`.

### Start the frontend

```powershell
cd d:\dharani\smart_travel_mcp\frontend
npm run dev
```

Open the app in your browser at `http://localhost:5173`.


## Optional: Run the MCP server

The MCP server is defined in `server/server.py` and can be started separately if you want to expose the tool registry directly.

```powershell
cd d:\dharani\smart_travel_mcp
.venv\Scripts\Activate.ps1
python -m server.server
```

That will launch the MCP service and register tools such as `weather`, `attraction`, `hotel`, `distance`, and more.


## Important notes

- The React app communicates with the FastAPI backend via `/chat`.
- The backend routes requests through the Python client logic in `client/client.py`.
- Tools are wrapped by `server/tools/tool_wrapper.py` to provide safe fallback and logging.
- The local RAG store is in `chroma_db/` and is used by `server/tools/knowledge_rag.py`.


## Code readability and comments

The project uses clear separation of concerns:
- `server/api.py` handles HTTP routing and logging
- `client/client.py` handles intent extraction and request routing
- `client/agents/` contains planner and finance orchestration
- `server/tools/` contains individual tool implementations
- `server/tools/tool_wrapper.py` centralizes reliability and fallback logic

Each module is designed to be easy to read and maintain, with comments describing purpose and flow.



## Troubleshooting

- If the app cannot reach the backend, confirm FastAPI is running on port `8000`.
- If the frontend shows network errors, verify CORS and the backend URL.
- If tools return fallback data, external APIs may be rate-limited or unavailable.
- If `GROQ_API_KEY` is missing, itinerary generation may fail.


This repository is the Smart Travel Planner project for travel planning using multi-agent coordination, travel tools, and a web chat interface.
