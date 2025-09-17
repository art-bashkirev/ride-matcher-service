# Ride Matcher Service

A service for matching ride requests with train schedules using the Yandex Schedules API.

## Configuration

This project uses a production-ready configuration system. See [CONFIG.md](CONFIG.md) for detailed documentation.

### Quick Start

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your API key:
   ```bash
   YANDEX_SCHEDULES_API_KEY=your_api_key_here
   ```

3. Use the config in your code:
   ```python
   from config import get_config
   
   config = get_config()
   api_key = config.yandex_schedules_api_key
   timezone = config.result_timezone
   ```

### Running

```bash
python main.py
```

### Testing Configuration

```bash
python test_config.py
python demo_config.py
```

## Features

- Production-ready environment configuration
- Type-safe configuration management
- Support for development and production environments
- Comprehensive validation and error handling
- Backward compatibility with existing code