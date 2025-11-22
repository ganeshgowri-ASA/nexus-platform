# NEXUS Platform - WebSocket Real-Time Server

Production-ready WebSocket server for real-time communication across all NEXUS Platform modules.

## 🚀 Features

### Core Features
- ✅ **FastAPI WebSocket Integration** - Seamless integration with FastAPI
- ✅ **Connection Pooling** - Efficient connection management with automatic cleanup
- ✅ **Room/Channel Support** - Multi-room broadcasting and private channels
- ✅ **Presence Tracking** - Real-time online/offline/away/busy status
- ✅ **Heartbeat/Ping-Pong** - Automatic connection health monitoring
- ✅ **Auto-Reconnect Support** - Client-side reconnection handling
- ✅ **Message Queue** - Offline message queuing and delivery
- ✅ **Error Handling** - Comprehensive error handling and recovery

### Real-Time Communication
- 📨 **Chat Messages** - Real-time messaging with delivery confirmations
- ⌨️ **Typing Indicators** - Show when users are typing
- ✓ **Read Receipts** - Track message read status
- 📝 **Message Editing** - Edit and delete messages in real-time
- 💬 **Private Messaging** - One-on-one and group conversations

### Collaborative Editing
- 📄 **Document Collaboration** - Real-time collaborative editing
- 🎨 **Cursor Tracking** - See other users' cursors with unique colors
- 🔄 **Operation Synchronization** - CRDT-ready operation transformation
- 📊 **Version Management** - Document version tracking
- ⚠️ **Conflict Resolution** - Automatic conflict detection and resolution

### Notifications
- 🔔 **Real-Time Notifications** - Instant notification delivery
- 🎯 **Priority Routing** - Priority-based notification handling
- 📢 **Broadcasting** - Send notifications to multiple users
- 🏷️ **Notification Types** - Info, success, warning, error, alerts

## 📁 Project Structure

```
websocket/
├── __init__.py                 # Module initialization
├── server.py                   # WebSocket server core
├── connection_manager.py       # Connection pooling and management
├── events.py                   # Event types and data models
└── handlers/
    ├── __init__.py
    ├── chat_handler.py         # Chat messaging handler
    ├── document_handler.py     # Collaborative editing handler
    ├── notification_handler.py # Notification handler
    └── presence_handler.py     # Presence tracking handler
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- FastAPI
- Uvicorn

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Start the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Connect via WebSocket

**JavaScript/Browser Example:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?user_id=user123&token=your_token');

ws.onopen = () => {
    console.log('Connected to NEXUS WebSocket');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected from NEXUS WebSocket');
};
```

**Python Client Example:**

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8000/ws?user_id=user123&token=your_token"

    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        message = await websocket.recv()
        print(f"Received: {message}")

        # Send a chat message
        chat_message = {
            "event_type": "chat.message",
            "conversation_id": "conv_123",
            "content": "Hello, World!",
            "content_type": "text"
        }
        await websocket.send(json.dumps(chat_message))

        # Receive messages
        while True:
            message = await websocket.recv()
            print(f"Received: {message}")

asyncio.run(connect())
```

## 📡 Event Types

### Connection Events
- `connect` - User connected
- `disconnect` - User disconnected
- `ping` - Heartbeat ping
- `pong` - Heartbeat pong
- `error` - Error occurred

### Chat Events
- `chat.message` - New chat message
- `chat.typing` - User typing indicator
- `chat.read` - Message read receipt
- `chat.delivered` - Message delivered confirmation
- `chat.edit` - Message edited
- `chat.delete` - Message deleted

### Document Events
- `doc.open` - Document opened
- `doc.close` - Document closed
- `doc.edit` - Document edited
- `doc.cursor` - Cursor position update
- `doc.selection` - Selection update
- `doc.save` - Document saved
- `doc.conflict` - Conflict detected

### Notification Events
- `notification` - New notification
- `notification.read` - Notification read
- `notification.clear` - Notification cleared

### Presence Events
- `presence.online` - User online
- `presence.offline` - User offline
- `presence.away` - User away
- `presence.busy` - User busy
- `presence.update` - Presence updated

### Room Events
- `room.join` - Joined room
- `room.leave` - Left room
- `room.broadcast` - Room broadcast

## 💬 Usage Examples

### Send a Chat Message

```javascript
const chatMessage = {
    event_type: "chat.message",
    conversation_id: "conv_123",
    content: "Hello everyone!",
    content_type: "text",
    mentions: ["user456"],
    attachments: []
};

ws.send(JSON.stringify(chatMessage));
```

### Show Typing Indicator

```javascript
const typingEvent = {
    event_type: "chat.typing",
    conversation_id: "conv_123",
    is_typing: true,
    username: "John Doe"
};

ws.send(JSON.stringify(typingEvent));
```

### Join a Room/Channel

```javascript
const joinRoom = {
    event_type: "room.join",
    room_id: "room_general",
    username: "John Doe"
};

ws.send(JSON.stringify(joinRoom));
```

### Update Presence Status

```javascript
const presenceUpdate = {
    event_type: "presence.update",
    status: "away",
    status_message: "In a meeting",
    location: "Meeting Room"
};

ws.send(JSON.stringify(presenceUpdate));
```

### Collaborative Document Editing

```javascript
const docEdit = {
    event_type: "doc.edit",
    document_id: "doc_123",
    username: "John Doe",
    operation: "insert",
    changes: [
        {
            position: { line: 10, column: 5 },
            text: "new content"
        }
    ],
    cursor_position: { line: 10, column: 15 }
};

ws.send(JSON.stringify(docEdit));
```

### Update Cursor Position

```javascript
const cursorUpdate = {
    event_type: "doc.cursor",
    document_id: "doc_123",
    username: "John Doe",
    position: { line: 10, column: 15 },
    selection: {
        start: { line: 10, column: 15 },
        end: { line: 10, column: 25 }
    }
};

ws.send(JSON.stringify(cursorUpdate));
```

## 🔌 REST API Endpoints

### WebSocket Statistics
```
GET /api/ws/stats
```
Returns WebSocket server statistics.

### Online Users
```
GET /api/ws/online
```
Get list of currently online users.

### Room Members
```
GET /api/ws/rooms/{room_id}
```
Get members of a specific room.

### User Presence
```
GET /api/presence/{user_id}
```
Get presence information for a user.

### Send Notification
```
POST /api/notifications/send
Body: {
    "user_id": "user123",
    "title": "New Message",
    "message": "You have a new message",
    "notification_type": "info",
    "priority": "normal"
}
```

### Broadcast Notification
```
POST /api/notifications/broadcast
Body: {
    "title": "System Alert",
    "message": "Maintenance in 10 minutes",
    "notification_type": "warning",
    "priority": "high"
}
```

### Active Documents
```
GET /api/documents/active
```
Get list of documents with active editing sessions.

### Document Session
```
GET /api/documents/{document_id}/session
```
Get active editing session info for a document.

## 🔒 Security Considerations

### Authentication
The server includes a simple token-based authentication example. For production:

1. **Implement JWT Authentication**
   ```python
   from jose import jwt

   async def verify_token(token: str):
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
           return payload
       except jwt.JWTError:
           raise HTTPException(status_code=401)
   ```

2. **Validate User Permissions**
   - Check user access to rooms/channels
   - Validate document edit permissions
   - Verify chat conversation membership

3. **Rate Limiting**
   - Implement rate limiting per connection
   - Limit message frequency
   - Prevent spam and abuse

### Best Practices

1. **Use HTTPS/WSS in Production**
   ```python
   # Configure SSL
   uvicorn.run(
       "main:app",
       host="0.0.0.0",
       port=443,
       ssl_keyfile="key.pem",
       ssl_certfile="cert.pem"
   )
   ```

2. **Environment Variables**
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       secret_key: str
       websocket_heartbeat: int = 30
       max_connections_per_user: int = 5

       class Config:
           env_file = ".env"
   ```

3. **Input Validation**
   - All events are validated using Pydantic models
   - Sanitize user input
   - Validate message content length

## 📊 Performance & Scalability

### Connection Limits
- Default: No hard limit (managed by system resources)
- Recommended: 10,000 concurrent connections per instance
- Use load balancer for horizontal scaling

### Message Queue
- Max queued messages per user: 100
- Automatic cleanup of old messages
- Configurable queue size

### Memory Management
- Message cache: 1,000 messages
- Operation history: 1,000 operations per document
- Automatic cleanup of stale data

### Horizontal Scaling
For large-scale deployments, consider:

1. **Redis for State Sharing**
   ```python
   # Share state across multiple instances
   import aioredis
   redis = await aioredis.create_redis_pool('redis://localhost')
   ```

2. **Message Broker (RabbitMQ/Kafka)**
   - Distribute messages across instances
   - Ensure message delivery

3. **Load Balancer**
   - Distribute WebSocket connections
   - Health checks and failover

## 🧪 Testing

### Run Tests
```bash
pytest tests/ -v --asyncio-mode=auto
```

### WebSocket Test Example
```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.mark.asyncio
async def test_websocket_connection():
    client = TestClient(app)

    with client.websocket_connect("/ws?user_id=test_user") as websocket:
        # Receive welcome message
        data = websocket.receive_json()
        assert data["event_type"] == "system.message"

        # Send chat message
        websocket.send_json({
            "event_type": "chat.message",
            "conversation_id": "test_conv",
            "content": "Test message"
        })

        # Receive echo
        response = websocket.receive_json()
        assert response["event_type"] == "chat.message"
```

## 📝 Monitoring & Logging

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nexus.log"),
        logging.StreamHandler()
    ]
)
```

### Metrics to Monitor
- Active connections count
- Messages per second
- Average message latency
- Error rate
- Memory usage
- CPU usage

## 🔧 Configuration

### Environment Variables
```bash
# .env file
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_HEARTBEAT_TIMEOUT=60
MAX_QUEUE_SIZE=100
MAX_CACHE_SIZE=1000
LOG_LEVEL=INFO
```

### Server Configuration
```python
ws_server = WebSocketServer(
    heartbeat_interval=30,      # Ping interval in seconds
    heartbeat_timeout=60,       # Connection timeout in seconds
    enable_auto_ping=True       # Enable automatic ping/pong
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the development team
- Check the documentation

## 🎯 Roadmap

- [ ] Redis integration for distributed deployment
- [ ] Advanced CRDT implementation
- [ ] End-to-end encryption for messages
- [ ] File sharing and attachments
- [ ] Voice/video call signaling
- [ ] Advanced analytics and monitoring
- [ ] GraphQL subscription support
- [ ] Mobile SDK (iOS/Android)

---

**Built with ❤️ for the NEXUS Platform**
