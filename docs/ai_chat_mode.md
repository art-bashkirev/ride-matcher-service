# AI Chat Bot Mode

This feature implements an AI chat bot mode that can be toggled on/off by admin users. When enabled, the bot will use NVIDIA's AI API to respond to user messages instead of simply echoing them.

## Features

- **Admin-only control**: Only users with `is_admin=true` can toggle AI mode
- **Persistent flag**: AI mode state is stored in Redis with no TTL (persists until changed)
- **Graceful fallback**: Falls back to echo mode if AI API is unavailable
- **Security by default**: Users are non-admin by default

## Setup

### 1. API Key Configuration

Add your NVIDIA AI API key to your environment:

```bash
# In .env file
NVIDIA_API_KEY=your_nvidia_api_key_here
```

Get your API key from: https://integrate.api.nvidia.com/

### 2. Database Migration

The `is_admin` field is automatically added to the users table. If you have an existing database, you may need to run:

```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
```

### 3. Set Admin Users

Use the admin management script to set admin users:

```bash
# Make user an admin
python /tmp/admin_manager.py 123456789 admin

# Remove admin status
python /tmp/admin_manager.py 123456789 user
```

Replace `123456789` with the actual Telegram user ID.

## Usage

### For Admin Users

- `/ai_mode` - Check current AI mode status
- `/ai_mode on` - Enable AI mode
- `/ai_mode off` - Disable AI mode

### For All Users

When AI mode is **enabled**:
- Regular messages will be processed by the AI
- The bot will respond with AI-generated content

When AI mode is **disabled**:
- Regular messages will be echoed back (original behavior)
- Station IDs still trigger schedule suggestions

## Architecture

### Components

1. **User Model** (`models/user.py`)
   - Added `is_admin` boolean field (default: False)

2. **AI Services** (`services/ai/`)
   - `nvidia_client.py`: NVIDIA AI API client using aiohttp
   - `flag_service.py`: Redis-based flag management

3. **Command Handler** (`app/telegram/handlers/commands/ai_mode.py`)
   - Admin-only command to toggle AI mode

4. **Message Handler** (`app/telegram/handlers/commands/echo_text.py`)
   - Modified to check AI flag and route accordingly

### Flow

1. User sends a message
2. Handler checks if it's a station ID → handle as before
3. Handler checks AI mode flag in Redis
4. If AI mode enabled → send to NVIDIA AI API
5. If AI mode disabled → echo the message

## Error Handling

- **No API key**: Displays configuration error message
- **API unavailable**: Falls back to error message, not echo mode
- **Redis unavailable**: Defaults to disabled (echo mode)
- **Database issues**: Handled gracefully with error messages

## Security

- Only admin users can toggle AI mode
- API keys are read from environment variables
- User admin status defaults to False
- All API calls are logged for monitoring

## Testing

Run the test script to verify functionality:

```bash
python /tmp/test_bot_functionality.py
```

This tests:
- Admin vs non-admin access to `/ai_mode` command
- AI flag persistence in Redis
- Message routing based on flag state
- Error handling for missing API keys