# Redis Setup Guide for PlatePal

This guide provides detailed instructions for installing and configuring Redis on different operating systems for the PlatePal project.

## What is Redis Used For in PlatePal?

Redis is used in PlatePal for:
- **WebSocket Channels**: Real-time communication for order tracking and notifications
- **Caching**: Performance optimization for frequently accessed data
- **Celery Task Queue**: Background job processing (if configured)

## Installation Methods

### Option 1: Windows

#### Method A: Using WSL (Windows Subsystem for Linux) - Recommended

1. Install WSL if not already installed:
   ```powershell
   wsl --install
   ```

2. Install Redis in WSL (Ubuntu):
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

3. Start Redis in WSL:
   ```bash
   sudo service redis-server start
   ```

4. Verify Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

#### Method B: Using Memurai (Windows Native)

1. Download Memurai from: https://www.memurai.com/get-memurai

2. Install Memurai (follow the installer)

3. Memurai will start automatically as a Windows service

4. Verify Redis is running:
   ```powershell
   redis-cli ping
   # Should return: PONG
   ```

#### Method C: Using Docker

1. Install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop

2. Run Redis container:
   ```powershell
   docker run -d -p 6379:6379 --name platepal-redis redis:latest
   ```

3. Verify Redis is running:
   ```powershell
   docker ps
   # Check that platepal-redis container is running
   ```

4. Test Redis connection:
   ```powershell
   docker exec -it platepal-redis redis-cli ping
   # Should return: PONG
   ```

### Option 2: macOS

#### Method A: Using Homebrew (Recommended)

1. Install Homebrew if not already installed:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Redis:
   ```bash
   brew install redis
   ```

3. Start Redis:
   ```bash
   # Start Redis manually (one-time)
   redis-server
   
   # OR start Redis as a background service
   brew services start redis
   ```

4. Verify Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

#### Method B: Using Docker

1. Install Docker Desktop for Mac: https://www.docker.com/products/docker-desktop

2. Run Redis container:
   ```bash
   docker run -d -p 6379:6379 --name platepal-redis redis:latest
   ```

3. Verify Redis is running:
   ```bash
   docker ps
   docker exec -it platepal-redis redis-cli ping
   ```

### Option 3: Linux (Ubuntu/Debian)

1. Update package list:
   ```bash
   sudo apt update
   ```

2. Install Redis:
   ```bash
   sudo apt install redis-server
   ```

3. Start Redis service:
   ```bash
   sudo systemctl start redis-server
   ```

4. Enable Redis to start on boot:
   ```bash
   sudo systemctl enable redis-server
   ```

5. Verify Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

## Configuration

### 1. Backend Environment Variables

Create or update the `.env` file in the `backend` directory:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. Verify Redis Connection

Test the Redis connection from Python:

```bash
cd backend
python manage.py shell
```

Then in the Python shell:
```python
from django.core.cache import cache
cache.set('test_key', 'test_value', 30)
result = cache.get('test_key')
print(result)  # Should print: test_value
```

Or test with redis-cli:
```bash
redis-cli
> PING
PONG
> SET test_key "Hello Redis"
OK
> GET test_key
"Hello Redis"
> EXIT
```

## Redis Configuration in Django

The PlatePal project uses Redis in three ways:

### 1. Channels (WebSocket)
Located in `backend/platepal/settings.py`:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(env('REDIS_HOST', default='localhost'), env.int('REDIS_PORT', default=6379))],
        },
    },
}
```

### 2. Django Cache
Located in `backend/platepal/settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{env('REDIS_HOST', default='localhost')}:{env.int('REDIS_PORT', default=6379)}/1",
    }
}
```

### 3. Celery (Task Queue)
Located in `backend/platepal/settings.py`:
```python
CELERY_BROKER_URL = f"redis://{env('REDIS_HOST', default='localhost')}:{env.int('REDIS_PORT', default=6379)}/0"
CELERY_RESULT_BACKEND = f"redis://{env('REDIS_HOST', default='localhost')}:{env.int('REDIS_PORT', default=6379)}/0"
```

Note: Different Redis databases (0, 1) are used to separate Celery, Channels, and Cache data.

## Starting Redis

### Windows (WSL)
```bash
sudo service redis-server start
```

### Windows (Memurai)
- Automatically starts as a Windows service
- Or start manually from Services

### macOS (Homebrew)
```bash
# One-time start
redis-server

# Start as service
brew services start redis

# Stop service
brew services stop redis
```

### Linux
```bash
# Start
sudo systemctl start redis-server

# Stop
sudo systemctl stop redis-server

# Restart
sudo systemctl restart redis-server

# Check status
sudo systemctl status redis-server
```

### Docker
```bash
# Start
docker start platepal-redis

# Stop
docker stop platepal-redis

# Restart
docker restart platepal-redis
```

## Troubleshooting

### Issue: "Connection refused" or "Could not connect to Redis"

**Solution 1: Check if Redis is running**
```bash
# Windows/Linux/macOS
redis-cli ping
# Should return: PONG

# Docker
docker ps | grep redis
```

**Solution 2: Check Redis port**
```bash
# Check if port 6379 is in use
# Windows
netstat -an | findstr 6379

# Linux/macOS
lsof -i :6379
# or
netstat -an | grep 6379
```

**Solution 3: Check Redis logs**
```bash
# Linux
sudo journalctl -u redis-server -f

# macOS (Homebrew)
tail -f /usr/local/var/log/redis.log

# Docker
docker logs platepal-redis
```

### Issue: "ModuleNotFoundError: No module named 'channels_redis'"

**Solution:** Install required Python packages:
```bash
cd backend
pip install channels channels-redis
```

### Issue: Redis Authentication Error

If your Redis instance has password authentication, update the configuration:

In `backend/platepal/settings.py`, update:
```python
# For Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [f"redis://:password@{env('REDIS_HOST', default='localhost')}:{env.int('REDIS_PORT', default=6379)}"],
        },
    },
}

# For Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://:password@{env('REDIS_HOST', default='localhost')}:{env.int('REDIS_PORT', default=6379)}/1",
    }
}
```

Or add to `.env`:
```env
REDIS_PASSWORD=your_password
```

### Issue: WebSocket connections not working

**Solution:** Ensure Redis is running and accessible:
```bash
# Test Redis connection
redis-cli ping

# Test from Django
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> channel_layer
# Should show RedisChannelLayer instance
```

## Redis Persistence (Production)

For production, configure Redis persistence to avoid data loss:

1. Edit Redis configuration file:
   - Linux: `/etc/redis/redis.conf`
   - macOS (Homebrew): `/usr/local/etc/redis.conf`
   - Windows (Memurai): Check Memurai documentation

2. Enable RDB persistence:
   ```conf
   save 900 1
   save 300 10
   save 60 10000
   ```

3. Enable AOF (Append Only File):
   ```conf
   appendonly yes
   appendfsync everysec
   ```

## Performance Tips

1. **Monitor Redis memory usage:**
   ```bash
   redis-cli info memory
   ```

2. **Set memory limits (production):**
   ```conf
   maxmemory 256mb
   maxmemory-policy allkeys-lru
   ```

3. **Check connected clients:**
   ```bash
   redis-cli client list
   ```

## Useful Redis Commands

```bash
# Connect to Redis CLI
redis-cli

# Ping server
PING

# Get all keys
KEYS *

# Get specific key
GET key_name

# Set a key
SET key_name "value"

# Delete a key
DEL key_name

# Get info about Redis
INFO

# Get info about memory
INFO memory

# Flush all data (use with caution!)
FLUSHALL

# Monitor commands in real-time
MONITOR
```

## Next Steps

After Redis is installed and running:

1. Verify the backend can connect to Redis (see Configuration section)
2. Test WebSocket connections by starting the Django development server
3. Verify caching is working in your Django application
4. If using Celery, test background task processing

For more information, visit:
- Redis Documentation: https://redis.io/documentation
- Django Channels: https://channels.readthedocs.io/
- Django Cache Framework: https://docs.djangoproject.com/en/stable/topics/cache/

