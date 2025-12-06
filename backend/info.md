Brooklyn 99

Team ID: f6e0a953-87f7-417b-90fe-88a08a39caec

Logout
Team Information
Brooklyn 99
Team ID: f6e0a953-87f7-417b-90fe-88a08a39caec

Ready
Created At

12/5/2025

Members

2

Team Members:

Iram Liu

il233@cornell.edu

+16469324962

Crystal Liang

yycliang@gmail.com

+19172156679

Kafka Credentials
Use these credentials to connect to your Kafka cluster

Bootstrap Servers
pkc-619z3.us-east1.gcp.confluent.cloud:9092
Copy
Topic Name
team.team.f6e0a95387f7417b90fe88a08a39caec
Copy
Consumer Group
team-cg-f6e0a95387f7417b90fe88a08a39caec
Copy
Client ID
team-client-f6e0a95387f7417b90fe88a08a39caec
Copy
Sender Number
+16463230991
Copy
API Key
b9f131d7-0172-4749-afdd-f01e753b664f
Copy
SASL Username
QRHNR6BCKVHD4M3U
Copy
SASL Password
••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
Copy
SASL Mechanism
PLAIN
Copy
TLS Enabled
true
Copy
TLS Insecure
false
Copy
SASL Enabled
true
Copy
👁️ Show Secret
⚠️ Security Warning: Keep your API secret secure. Never commit it to version control or share it publicly.

Quickstart Code
Get started quickly with these code examples. All credentials are pre-filled.

Python Producer
Python Consumer
Node.js Producer
Node.js Consumer
Copy

# Python Kafka Producer Example

# Install: pip install kafka-python

from kafka import KafkaProducer
import json

# Kafka Configuration

bootstrap_servers = 'pkc-619z3.us-east1.gcp.confluent.cloud:9092'
topic_name = 'team.team.f6e0a95387f7417b90fe88a08a39caec'
api_key = 'b9f131d7-0172-4749-afdd-f01e753b664f'
api_secret = 'cfltTIivf3OHq6tr9fpASLxV4pp7vzPfvnz3cwT8+NAoOAJUCZwRuxuk1sSZTK+w'

# Initialize Producer

producer = KafkaProducer(
bootstrap_servers=bootstrap_servers.split(','),
security_protocol='SASL_SSL',
sasl_mechanism='PLAIN',
sasl_plain_username=api_key,
sasl_plain_password=api_secret,
value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send a message

message = {
'event': 'test_message',
'data': {
'message': 'Hello from Brooklyn 99!',
'timestamp': '2024-01-01T00:00:00Z'
}
}

try:
future = producer.send(topic_name, value=message)
record_metadata = future.get(timeout=10)
print(f"Message sent successfully!")
print(f"Topic: {record_metadata.topic}")
print(f"Partition: {record_metadata.partition}")
print(f"Offset: {record_metadata.offset}")
except Exception as e:
print(f"Error sending message: {e}")
finally:
producer.close()
Series Documentation
Browse the docs right from your dashboard.

Access API Docs
Refresh Docs
Series iMessage Service – Hackathon API
Series Documentation

Series iMessage Service – Hackathon API
hackathon-api.md
Series iMessage Service – Hackathon API
API endpoints tagged
Copy
hackathon
from
Copy
openapi.go
. All routes require
Copy
Authorization: Bearer <API_KEY>
unless noted. Paths are relative to the service base URL.

Chats
List chats
GET
Copy
/api/chats
Query params:
Copy
phone_number
(string, optional): filter by participant phone (E.164).
Copy
page
(int, default 1, min 1).
Copy
per_page
(int, default 25, max 100).
Response: 200 OK with paginated chat list.
Create chat
POST
Copy
/api/chats
Body (
Copy
application/json
, required):
Copy
send_from
(string, E.164) — phone to send from.
Copy
chat
:
Copy
phone_numbers
(string[], required, min 1) — recipients in E.164.
Copy
display_name
(string | null, optional).
Copy
message
:
Copy
text
(string, required, cannot be empty string - must have non whitespace characters).
Response: 201 Created (or 200) with created chat/message.
Examples:
Single recipient:
Copy
{
"send_from": "+13175269229",
"chat": { "phone_numbers": ["+13343284472"] },
"message": { "text": "Hello!" }
}
Group:
Copy
{
"send_from": "+13175269229",
"chat": {
"display_name": "Product Team",
"phone_numbers": ["+13343284472", "+13344713465"]
},
"message": { "text": "Standup in 5 mins" }
}
Recommended send flow
Step 1: Create chat (and initial message) with POST
Copy
/api/chats
. This returns
Copy
id
for the chat.
Step 2: Use that
Copy
chat_id
to send additional messages with POST
Copy
/api/chats/{chat_id}/chat_messages
.
Step 3: Add reactions on messages with POST
Copy
/api/chat_messages/{id}/reactions
.
Get chat
GET
Copy
/api/chats/{id}
Path params:
Copy
id
(integer) — chat ID.
Response: 200 OK with chat details.
Find chat
GET
Copy
/api/chats/find
Query params:
Copy
phone_number
(string, optional): primary phone.
Copy
phone_numbers[]
(string[], optional): additional phones to match.
Response: 200 OK with matching chat info.
Start typing indicator
POST
Copy
/api/chats/{id}/start_typing
Path params:
Copy
id
(integer) — chat ID.
Response: 200 OK.
Stop typing indicator
DELETE
Copy
/api/chats/{id}/stop_typing
Path params:
Copy
id
(integer) — chat ID.
Response: 200 OK.
Mark chat as read
PUT
Copy
/api/chats/{id}/mark_as_read
Path params:
Copy
id
(integer) — chat ID.
Response: 204 No Content (success) or 422 if failed.
Chat Messages
List chat messages
GET
Copy
/api/chats/{chat_id}/chat_messages
Path params:
Copy
chat_id
(integer) — chat ID.
Response: 200 OK with messages.
Create chat message
POST
Copy
/api/chats/{chat_id}/chat_messages
Path params:
Copy
chat_id
(integer) — chat ID.
Body (
Copy
application/json
, required):
Copy
message
:
Copy
text
(string, required)
Copy
attachments
(optional array):
Copy
filename
(string)
Copy
mime_type
(string)
Copy
data_base64
(string, base64 file data, no data URI prefix)
Response: 201 Created (or 200) with created message.
Get chat message
GET
Copy
/api/chats/{chat_id}/chat_messages/{message_id}
Path params:
Copy
chat_id
(integer),
Copy
message_id
(integer).
Response: 200 OK with message.
Delete chat message
DELETE
Copy
/api/chats/{chat_id}/chat_messages/{message_id}
Path params:
Copy
chat_id
(integer),
Copy
message_id
(integer).
Response: 200 OK on delete.
Edit chat message
POST
Copy
/api/chats/{chat_id}/chat_messages/{message_id}/edit
Path params:
Copy
chat_id
(integer),
Copy
message_id
(integer).
Body (
Copy
application/json
, required):
Copy
text
(string)
Response: 200 OK after edit (allowed within 15 minutes of creation).
Message Reactions
React to message
POST
Copy
/api/chat_messages/{id}/reactions
Path params:
Copy
id
(integer) — message ID.
Body (
Copy
application/json
, required):
Copy
operation
(string, enum:
Copy
add
|
Copy
remove
)
Copy
type
(string, enum:
Copy
love
|
Copy
like
|
Copy
dislike
|
Copy
laugh
|
Copy
emphasize
|
Copy
question
)
Response: 201 Created (or 200) with reaction result.
Get reaction
GET
Copy
/api/chat_message_reactions/{id}
Path params:
Copy
id
(integer) — reaction ID.
Response: 200 OK with reaction details.
Kafka events (per team topic)
Use Kafka IO to observe your team’s topic for real-time events.
Incoming message (
Copy
message.received
)
Copy
{
"api_version": "v2",
"created_at": "2025-12-05T14:42:06-06:00",
"data": {
"attachments": [],
"chat_handles": [
{ "display_name": "You", "identifier": "+16463458837", "is_me": true },
{ "display_name": "+1 (917) 625-6109", "identifier": "+19176256109", "is_me": false }
],
"chat_id": "1698665",
"from_phone": "+19176256109",
"id": "53077912",
"is_read": false,
"reaction_id": null,
"sent_at": "2025-12-05 14:42:05 -0600",
"service": "iMessage",
"text": "Fianko just posted."
},
"event_id": "a9fd569f-59a4-4f0e-ab35-ac6acf92eb0b",
"event_type": "message.received"
}
Typing indicator received (
Copy
typing_indicator.received
)
Copy
{
"api_version": "v2",
"created_at": "2025-12-05T14:41:50-06:00",
"data": {
"chat_handles": [
{ "display_name": "You", "identifier": "+16463458837", "is_me": true },
{ "display_name": "+1 (917) 625-6109", "identifier": "+19176256109", "is_me": false }
],
"chat_id": "1698665",
"display": true,
"timestamp": "2025-12-05T14:41:50-06:00"
},
"event_id": "f1800df2-004f-4faf-bee8-0e3b1b1d202f",
"event_type": "typing_indicator.received"
}
Typing indicator stopped (
Copy
typing_indicator.removed
)
Copy
{
"api_version": "v2",
"created_at": "2025-12-05T14:42:05-06:00",
"data": {
"chat_handles": [
{ "display_name": "You", "identifier": "+16463458837", "is_me": true },
{ "display_name": "+1 (917) 625-6109", "identifier": "+19176256109", "is_me": false }
],
"chat_id": "1698665",
"display": false,
"timestamp": "2025-12-05T14:42:05-06:00"
},
"event_id": "7dc7fdf2-ac08-4feb-b88a-1f3d381dd35f",
"event_type": "typing_indicator.removed"
}
iMessage Availability
Check availability
POST
Copy
/api/i_message_availability/check
Body (
Copy
application/json
, required):
Copy
phone_number
(string) — number to check.
Response: 200 OK with availability info.
