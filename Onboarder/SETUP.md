# 🚀 Onboarder Setup Guide

## Quick Start

The easiest way to get started with Onboarder is using the new setup script:

```bash
# Start everything (web dashboard + API server) with automatic port management
python setup.py --mode web

# Start API server only
python setup.py --mode api

# Start on a specific port
python setup.py --mode web --port 8081

# Find a free port automatically
python setup.py --mode web --find-port
```

## What the Setup Script Does

1. **🔧 Checks Environment**: Verifies your Gemini API key is configured
2. **🔪 Kills Port Conflicts**: Automatically kills processes using the target port
3. **🔍 Finds Free Ports**: Optionally finds alternative ports if needed
4. **🚀 Starts Services**: Launches the API server and/or web dashboard
5. **🌐 Opens Browser**: Automatically opens the web dashboard in your browser

## Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--mode` | Launch mode: `api`, `web`, or `both` | `--mode web` |
| `--port` | Target port number | `--port 8081` |
| `--no-kill` | Skip killing processes on port | `--no-kill` |
| `--find-port` | Find free port if target is busy | `--find-port` |

## Examples

### Start Web Dashboard (Recommended)
```bash
python setup.py --mode web
```
This will:
- Kill any processes on port 8080
- Start the API server
- Start the web dashboard
- Open your browser to the dashboard

### Start API Server Only
```bash
python setup.py --mode api
```

### Use Different Port
```bash
python setup.py --mode web --port 8081
```

### Find Free Port Automatically
```bash
python setup.py --mode web --find-port
```

## Troubleshooting

### Port Conflicts
The setup script automatically handles port conflicts by killing existing processes. If you want to avoid this:

```bash
python setup.py --mode web --no-kill
```

### No Free Ports Found
If the automatic port finding fails, try a different starting port:

```bash
python setup.py --mode web --port 9000 --find-port
```

### API Key Issues
Make sure you have your Gemini API key configured:

```bash
# Copy the example file
cp env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_actual_api_key_here
```

## Alternative Methods

If you prefer more control, you can still use the individual components:

```bash
# Start server launcher (with port management)
python start_server.py --mode web

# Start integrated web server directly
python simple_web_server.py

# Start API server directly
python realtime_api.py --mode server
```

## What's New

- ✅ **Single Setup File**: One command handles everything
- ✅ **Automatic Port Management**: Kills conflicting processes automatically
- ✅ **Smart Port Finding**: Finds free ports when needed
- ✅ **Environment Validation**: Checks API key before starting
- ✅ **Browser Integration**: Automatically opens dashboard
- ✅ **Simplified Documentation**: Updated all guides to use the new setup

---

**Ready to onboard?** Run `python setup.py --mode web` and you're good to go! 🎉
