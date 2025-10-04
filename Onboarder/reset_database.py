#!/usr/bin/env python3
"""
Database Reset Script for Onboarder System

This script clears all data from the database and reinitializes it with a fresh schema.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from onboarder.database_manager import DatabaseManager

def main():
    """Reset the database."""
    print("🗄️  Onboarder Database Reset")
    print("=" * 40)
    
    try:
        # Initialize database manager
        print("📊 Initializing database manager...")
        db_manager = DatabaseManager()
        
        # Clear existing database
        print("🧹 Clearing existing data...")
        success = db_manager.clear_database()
        
        if success:
            print("✅ Database cleared successfully!")
        else:
            print("❌ Failed to clear database")
            return False
        
        # Reinitialize schema
        print("🔧 Reinitializing schema...")
        db_manager._init_database()
        
        print("✅ Database reset completed successfully!")
        print("\n📝 The database is now ready for fresh onboarding records.")
        print("   - All previous data has been removed")
        print("   - Schema has been reinitialized")
        print("   - Employee IDs will be auto-generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
