# System Summary: Series iMessage Service Hackathon

## Overview

This is a **hackathon project** for the **Series iMessage Service**, which provides an API and real-time event system for interacting with iMessage through programmatic means.

## What the System Does

The Series iMessage Service enables developers to:

1. **Send and Receive iMessages Programmatically**:

   - Create chats and send messages via REST API
   - Receive real-time notifications of incoming messages via Kafka

2. **Real-time Event Processing**:

   - Consume Kafka events for incoming messages
   - Track typing indicators
   - Monitor message reactions and status

3. **Full iMessage Feature Support**:
   - Individual and group chats
   - Message attachments
   - Message reactions (love, like, dislike, laugh, emphasize, question)
   - Typing indicators
   - Read receipts
   - Message editing (within 15 minutes)

## Architecture Components

### 1. **REST API** (Series Service)

- **Base URL**: Provided by Series
- **Authentication**: Bearer token (API Key)
- **Endpoints**:
  - `/api/chats` - Create/list chats
  - `/api/chats/{id}/chat_messages` - Send messages
  - `/api/chat_messages/{id}/reactions` - Add reactions
  - `/api/chats/{id}/start_typing` - Show typing indicator
  - `/api/chats/{id}/stop_typing` - Hide typing indicator

### 2. **Kafka Event Stream** (Real-time)

- **Platform**: Confluent Cloud (GCP)
- **Bootstrap Server**: `pkc-619z3.us-east1.gcp.confluent.cloud:9092`
- **Topic**: Team-specific topic (e.g., `team.team.f6e0a95387f7417b90fe88a08a39caec`)
- **Event Types**:
  - `message.received` - New message arrived
  - `typing_indicator.received` - User started typing
  - `typing_indicator.removed` - User stopped typing

### 3. **Backend Service** (This Project)

- **Framework**: Flask (Python)
- **Purpose**: Consume Kafka events and process them
- **Features**:
  - Kafka consumer for real-time events
  - Event handlers for different event types
  - REST API endpoints for health checks and status

## Event Flow

1. **Incoming Message Flow**:

   ```
   iMessage → Series Service → Kafka Topic → Your Backend Consumer → Process Event
   ```

2. **Outgoing Message Flow**:
   ```
   Your Backend → Series REST API → iMessage Service → Recipient
   ```

## Kafka Event Structure

### Message Received Event

```json
{
  "api_version": "v2",
  "event_type": "message.received",
  "created_at": "2025-12-05T14:42:06-06:00",
  "data": {
    "id": "53077912",
    "chat_id": "1698665",
    "from_phone": "+19176256109",
    "text": "Message content",
    "is_read": false,
    "attachments": [],
    "chat_handles": [...]
  }
}
```

### Typing Indicator Event

```json
{
  "api_version": "v2",
  "event_type": "typing_indicator.received",
  "data": {
    "chat_id": "1698665",
    "display": true,
    "timestamp": "2025-12-05T14:41:50-06:00"
  }
}
```

## Team Information

- **Team Name**: Brooklyn 99
- **Team ID**: f6e0a953-87f7-417b-90fe-88a08a39caec
- **Sender Number**: +16463230991

## Use Cases

This system can be used to build:

1. **Chatbots**: Automated responses to iMessages
2. **Notification Systems**: Forward messages to other platforms
3. **Analytics**: Track message patterns and engagement
4. **Integration Tools**: Connect iMessage with other services
5. **Automation**: Auto-reply, message routing, etc.

## Security Notes

⚠️ **Important**:

- Keep API keys and secrets secure
- Never commit credentials to version control
- Use environment variables for sensitive data
- The Kafka API secret is sensitive and should be protected

## Next Steps for Development

1. **Add Database**: Store messages and events for persistence
2. **Implement Business Logic**: Process messages based on content
3. **Add Series API Client**: Send messages programmatically
4. **Error Handling**: Robust retry logic and error recovery
5. **Testing**: Unit tests and integration tests
6. **Deployment**: Containerize and deploy to cloud platform
