# WebSocket Setup Guide

## Overview

PlatePal uses Django Channels for real-time WebSocket communication. WebSocket connections are **optional** - the application will work normally without them, but real-time features (like live order tracking) will be disabled.

## When WebSockets Are Used

- **Order Updates**: Real-time order status changes
- **Delivery Tracking**: Live rider location updates
- **Notifications**: Instant notifications for order events
- **Chat**: Real-time customer support chat
- **Menu Updates**: Live menu availability changes

## Running the ASGI Server

WebSockets require a separate ASGI server (not the standard Django development server). You have two options:

### Option 1: Use Daphne (Recommended)

```bash
cd backend
pip install daphne
daphne -b 0.0.0.0 -p 8000 platepal.asgi:application
```

### Option 2: Use Uvicorn

```bash
cd backend
pip install uvicorn[standard]
uvicorn platepal.asgi:application --host 0.0.0.0 --port 8000
```

## Development Setup

For development, you can run both the HTTP server and WebSocket server:

### Terminal 1: Django HTTP Server (for API)
```bash
cd backend
python manage.py runserver
```

### Terminal 2: ASGI Server (for WebSockets)
```bash
cd backend
daphne -b 0.0.0.0 -p 8000 platepal.asgi:application
```

Or use uvicorn:
```bash
cd backend
uvicorn platepal.asgi:application --host 0.0.0.0 --port 8000
```

## Disabling WebSockets

If you don't need real-time features, you can disable WebSocket connections:

### Frontend (Environment Variable)

Add to your `.env` file:
```
VITE_WS_ENABLED=false
```

Or in `frontend/apps/customer/.env`:
```
VITE_WS_ENABLED=false
```

## Troubleshooting

### WebSocket Connection Errors

If you see WebSocket connection errors in the console:

1. **Check if ASGI server is running**: WebSockets require a separate ASGI server (daphne/uvicorn), not just `runserver`.

2. **Check port**: Ensure the ASGI server is running on port 8000 (or the port specified in `VITE_WS_URL`).

3. **Check CORS**: Ensure CORS is properly configured in `backend/platepal/settings.py`.

4. **Check authentication**: WebSocket connections require a valid JWT token. Ensure the user is logged in.

5. **Disable if not needed**: If you don't need real-time features, disable WebSockets using `VITE_WS_ENABLED=false`.

### Common Errors

- **"WebSocket connection failed"**: ASGI server is not running. Start daphne or uvicorn.
- **"Connection refused"**: ASGI server is not running on the expected port.
- **"Unauthorized"**: Invalid or expired JWT token. User needs to log in again.

## Production Deployment

For production, use a process manager like systemd or supervisor to run both servers:

```ini
[program:platepal-http]
command=/path/to/venv/bin/gunicorn platepal.wsgi:application
directory=/path/to/backend
user=www-data

[program:platepal-ws]
command=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 platepal.asgi:application
directory=/path/to/backend
user=www-data
```

Or use a reverse proxy (nginx) to handle both HTTP and WebSocket traffic on the same port.

## Notes

- WebSocket connections are **optional** - the app works without them
- Connection failures are handled gracefully and won't break the application
- Real-time features will be disabled if WebSocket connection fails
- The app will fall back to polling for updates if WebSockets are unavailable

