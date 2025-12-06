# Series iMessage Service Backend

A Flask backend that consumes real-time Kafka events from the Series iMessage Service.

## System Overview

This backend integrates with the **Series iMessage Service** for a hackathon project. The system enables:

1. **Real-time Message Processing**: Consumes Kafka events for incoming iMessages
2. **Event Types Handled**:

   - `message.received`: When a new iMessage is received
   - `typing_indicator.received`: When someone starts typing
   - `typing_indicator.removed`: When typing stops

3. **Kafka Integration**: Connects to Confluent Cloud Kafka cluster to receive real-time events

## Setup

1. From the project root, create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. (Optional) Create a `.env` file from `.env.example`:

```bash
cp backend/.env.example backend/.env
```

4. Run the backend:

```bash
python backend/app.py
```

The server will start on `http://localhost:5000` by default.

## API Endpoints

- `GET /`: Health check endpoint
- `GET /api/events`: Get recent events (placeholder)
- `POST /api/send-message`: Send message endpoint (placeholder - use Series API directly)

## Kafka Events

The backend automatically consumes events from the Kafka topic. Event handlers are defined for:

- **message.received**: Processes incoming messages
- **typing_indicator.received**: Handles typing indicators
- **typing_indicator.removed**: Handles typing indicator removal

## Configuration

Kafka credentials are configured in `app.py` or via environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_TOPIC`
- `KAFKA_CONSUMER_GROUP`
- `KAFKA_API_KEY`
- `KAFKA_API_SECRET`

## Next Steps

1. Add database storage for events
2. Implement business logic in event handlers
3. Add Series API integration for sending messages
4. Add authentication/authorization
5. Add error handling and retry logic
