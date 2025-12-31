# Car Appointment Assistant

An AI-powered assistant for booking car dealership appointments, built with LangGraph, GraphQL, and Groq.

## Tech Stack

- **LangGraph** - Agent orchestration framework
- **Groq (Llama 3.3)** - LLM provider
- **Strawberry** - GraphQL API
- **FastAPI** - Web framework
- **uv** - Package manager

## Project Structure

```
car-appointment-assistant/
├── main.py                 # Entry point (FastAPI server)
├── src/
│   ├── agent/graph.py      # LangGraph agent
│   ├── api/schema.py       # GraphQL schema
│   ├── mcp/tools.py        # Agent tools
│   └── data/mock_data.py   # Mock dealerships data
└── debug_agent.py          # Debug script
```

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create `.env` file with your Groq API key:
```
GROQ_API_KEY=your-api-key-here
```

3. Run the server:
```bash
.venv/Scripts/python main.py   # Windows
.venv/bin/python main.py       # Linux/Mac
```

4. Open GraphQL Playground: http://localhost:8000/graphql

## Usage Examples

### Query: List all dealerships

```graphql
{
  dealerships {
    id
    name
    location
    services
    phone
  }
}
```

### Query: Filter by location

```graphql
{
  dealerships(location: "Brooklyn") {
    name
    services
  }
}
```

### Query: Check availability

```graphql
{
  availability(dealershipId: "dealer_001") {
    date
    time
  }
}
```

### Mutation: Chat with the AI assistant

```graphql
mutation {
  chat(message: "I need an oil change in Manhattan") {
    message
    success
  }
}
```

### Mutation: Book an appointment

```graphql
mutation {
  chat(message: "Book an oil change at dealer_001 on 2026-01-15 at 10:00, confirm") {
    message
    success
  }
}
```

## Available Services

- Oil change
- Tire rotation
- Brake inspection
- General review
- State inspection
- Air conditioning
- Battery check

## Architecture

```
User Request
     │
     ▼
┌─────────────┐
│  GraphQL    │  ← Strawberry + FastAPI
│    API      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  LangGraph  │  ← Agent orchestration
│    Agent    │
└──────┬──────┘
       │
   ┌───┴───┐
   ▼       ▼
┌─────┐ ┌───────┐
│Groq │ │ Tools │  ← search, availability, book
│ LLM │ └───┬───┘
└─────┘     │
            ▼
      ┌──────────┐
      │Mock Data │
      └──────────┘
```

## Debug

Run the debug script to see agent decisions step by step:

```bash
.venv/Scripts/python debug_agent.py
```

Output:
```
============================================================
USER: I need an oil change in Manhattan
============================================================

--- Step 1 ---
Node: agent
  [AIMessage] LLM wants to call tools:
    -> search_dealerships({'location': 'Manhattan', 'service': 'oil change'})

--- Step 2 ---
Node: tools
  [ToolMessage] Tool result:
    Found 1 dealership(s):
    - Downtown Auto Service (Manhattan)
    ...

--- Step 3 ---
Node: agent
  [AIMessage] I found Downtown Auto Service in Manhattan...
```
