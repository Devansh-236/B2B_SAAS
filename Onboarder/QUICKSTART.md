# 🚀 Quick Start Guide - Onboarder Multi-Agent System

Get up and running with the Onboarder system in 5 minutes!

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements-minimal.txt
```

### 2. Get Your Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 3. Configure Environment
```bash
cp env.example .env
# Edit .env and paste your API key
```

### 4. Test the System
```bash
python test_system.py
```

### 5. Run the Demo
```bash
python example_usage.py
```

### 6. Try State Management Demo
```bash
python state_management_demo.py
```

### 7. Try Real-time Features Demo
```bash
python realtime_demo.py
```

### 8. Initialize Database and Run System
```bash
# Initialize SQLite database and run demo
python setup.py --init --demo

# Or run individual commands
python setup.py --init      # Initialize database
python setup.py --demo      # Run onboarding demo
python setup.py --status    # Show system status
```

### 9. Migrate Existing Data (if needed)
```bash
# Migrate from old JSON state files
python migrate_to_sqlite.py

# Or use the setup script
python setup.py --migrate
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
- 🔄 Process resumption and tracking
- 📊 Comprehensive reporting and analytics
- 🗄️ Robust data management

## 🔧 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Make sure you've created a `.env` file
- Check that your API key is correctly set

**"Import failed"**
- Run `pip install -r requirements-minimal.txt` again
- Make sure you're using Python 3.8+

**"API key is still set to placeholder"**
- Update your `.env` file with your actual Gemini API key

**"Database initialization failed"**
- Check file permissions in the current directory
- Ensure SQLite is available on your system
- Try running: `python setup.py --init --db-path ./onboarding.db`

**"Migration from JSON failed"**
- Check if the JSON file exists: `ls onboarding_state/onboarding_states.json`
- Try manual migration: `python migrate_to_sqlite.py --verify`
- Use force flag if needed: `python migrate_to_sqlite.py --force`

## 📚 Next Steps

1. **Read the full README.md** for detailed documentation
2. **Customize the agents** for your specific needs
3. **Integrate with real APIs** for production use
4. **Add your company branding** to emails and documents

## 🆘 Need Help?

- Check the `README.md` for comprehensive documentation
- Run `python setup.py --init --demo` for automated setup and demo
- Review the example code in `example_usage.py`
- Check system status with: `python setup.py --status`

---

**Ready to onboard your first employee?** 🎉
