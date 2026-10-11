# 🚀 Quick Start Guide - Onboarder Multi-Agent System

Get up and running with the Onboarder system in 5 minutes!

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
python3 -m pip install -r requirements-minimal.txt
```

### 2. Get Your Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 3. Configure Environment
```bash
cp env.example .env
# Edit .env and paste your API key
```

### 4. Initialize Database and Run the Demo
```bash
# Initialize SQLite database, show status and run a demo onboarding
python3 setup.py

# Or run individual commands
python3 setup.py --init      # Initialize database
python3 setup.py --demo      # Run onboarding demo
python3 setup.py --status    # Show system status
```

### 5. Start the API Server
```bash
python3 main.py
```

Open http://127.0.0.1:8050/docs for the interactive API documentation.

### 6. Migrate Existing Data (if needed)
```bash
# Migrate from an old JSON state file
python3 setup.py --migrate --json-file onboarding_state/onboarding_states.json
```

## 🎯 What You'll See

The demo will show you:
- ✅ Welcome email generation
- 📄 Contract creation
- 💻 IT account provisioning
- 📅 Meeting scheduling
- 🤝 Buddy assignment
- 📚 Training enrollment
- 📋 30-60-90 day planning
- 💾 SQLite database persistence

Emails, calendar invites, e-signatures and account provisioning are simulated.

## 🔧 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Make sure you've created a `.env` file
- Check that your API key is correctly set

**"Import failed"**
- Run `python3 -m pip install -r requirements-minimal.txt` again
- Make sure you're using Python 3.9+

**"Database initialization failed"**
- Check file permissions in the Onboarder directory
- Try a different location: `python3 setup.py --init --db-path /tmp/onboarding.db`

**"Migration from JSON failed"**
- Check if the JSON file exists: `ls onboarding_state/onboarding_states.json`
- Check the log output for the records that could not be migrated

## 📚 Next Steps

1. **Read the full README.md** for detailed documentation
2. **Customize the agents** for your specific needs
3. **Integrate with real APIs** for production use
4. **Add your company branding** to emails and documents

## 🆘 Need Help?

- Check the `README.md` for comprehensive documentation
- See `SETUP.md` for configuration options
- Check system status with: `python3 setup.py --status`

---

**Ready to onboard your first employee?** 🎉
