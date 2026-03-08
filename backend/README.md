# Krishi Backend

Prototype backend for Krishi, the agricultural decision copilot.

## Architecture
- **Framework**: FastAPI (Python 3.11)
- **Services**:
  - `WeatherService`: Uses Open-Meteo API (Free, No Key)
  - `PriceService`: Mock implementation mimicking AP/Telangana Mandi prices (e-NAM style)
  - `ScenarioEngine`: Rule-based logic for "Sell vs Wait" decision support

## Conversational Co-Pilot (Voice & Chat)

The backend now supports a conversational interface with memory retention.

### Features
- **Voice Interaction**: Uses browser SpeechRecognition for input and gTTS for output.
- **Context Retention**: Maintains the last 10 turns of conversation for follow-up questions.
- **Multi-modal Input**: Supports both voice and text input via `/api/v1/voice/interact` and `/api/v1/voice/interact_text`.
- **Offline Fallback**: Automatically switches to rule-based responses if the local LLM (Ollama) is unavailable.
- **Barge-in Support**: Allows users to interrupt the assistant with short commands (stop, wait, etc.).

### API Usage

#### POST /api/v1/voice/interact_text
Submit text with optional conversation history.

**Request Body:**
```json
{
  "text": "What is the price of tomato?",
  "language": "en",
  "context": {
    "history": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi! How can I help?"}
    ]
  }
}
```

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation
Once running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

## Endpoints

### POST /api/v1/harvest/decision
Submit harvest details to get selling advice.

**Request Body:**
```json
{
  "crop": "Tomato",
  "quantity": 50,
  "location": "Madanapalle",
  "latitude": 13.55,
  "longitude": 78.50,
  "harvest_date": "2023-10-27",
  "storage_condition": "open"
}
```

**Response:**
Returns scenarios (Sell Now, Wait 24h, Wait 48h) with risk assessments and revenue projections.

## Local Deployment Script

Run the full application in local-only mode (no AWS dependencies):

```bash
./scripts/deploy-local.sh start
```

Backend-only mode:

```bash
./scripts/deploy-local.sh start --backend-only
```

Validate running local services:

```bash
./scripts/deploy-local.sh validate
```

Stop services started by the script:

```bash
./scripts/deploy-local.sh stop
```

## Local Prerequisites

- Python 3
- Node.js and npm
- curl
- Access to create virtual environments and local files under `backend/`

## Local Service Mapping

- S3 → local filesystem (`backend/uploads`)
- DynamoDB → SQLite (`backend/data/krishi_local.db`)
- Lambda → local Uvicorn process
- Cognito → local auth mode (`AUTH_PROVIDER=local`, `MOCK_COGNITO=true`)

## Troubleshooting

- Backend health check fails: inspect `.run/logs/backend.log`, then confirm no process already uses the backend port.
- Frontend does not load: inspect `.run/logs/frontend.log`, then run `npm install` in `frontend`.
- AI responses fallback unexpectedly: start Ollama on `localhost:11434` or continue with fallback mode.
- Port conflicts: rerun using `--backend-port <port>` and `--frontend-port <port>`.
- Dependency installation issues: run `./scripts/deploy-local.sh start` without `--no-install`.
