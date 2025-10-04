#!/usr/bin/env python3
"""
Onboarder Setup Script

A single file that initializes the SQLite database and runs the Onboarder system.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Add the onboarder package to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def initialize_database(db_path: str = "onboarding.db") -> bool:
    """
    Initialize the SQLite database.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from onboarder.database_manager import DatabaseManager
        
        print("📊 Initializing SQLite database...")
        db_manager = DatabaseManager(db_path)
        
        # Test database connection
        summary = db_manager.get_onboarding_summary()
        print(f"✅ Database initialized successfully")
        print(f"   Database file: {os.path.abspath(db_path)}")
        print(f"   Current records: {summary.get('total_onboardings', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def migrate_from_json(json_file: str = "onboarding_state/onboarding_states.json") -> bool:
    """
    Migrate data from JSON file to SQLite database.
    
    Args:
        json_file: Path to the JSON state file
        
    Returns:
        bool: True if migration successful, False otherwise
    """
    try:
        if not os.path.exists(json_file):
            print(f"⚠️  JSON file not found: {json_file}")
            print("   No migration needed.")
            return True
        
        from onboarder.database_manager import DatabaseManager
        
        print(f"🔄 Migrating data from {json_file}...")
        db_manager = DatabaseManager()
        
        success = db_manager.migrate_from_json(json_file)
        
        if success:
            summary = db_manager.get_onboarding_summary()
            print(f"✅ Migration completed successfully!")
            print(f"   Migrated {summary.get('total_onboardings', 0)} records")
            
            # Ask if user wants to remove the JSON file
            response = input("Remove the old JSON state file? (y/N): ").strip().lower()
            if response == 'y':
                os.remove(json_file)
                print("🗑️  JSON state file removed")
            
            return True
        else:
            print("❌ Migration failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False


def run_demo() -> bool:
    """
    Run the onboarding demo.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("🚀 Running onboarding demo...")
        
        from onboarder.coordinator_agent import CoordinatorAgent
        
        # Initialize coordinator
        coordinator = CoordinatorAgent()
        
        # Demo new hire data
        demo_data = {
            'full_name': 'Demo Employee',
            'personal_email': 'demo@example.com',
            'job_title': 'Software Engineer',
            'manager_name': 'Demo Manager',
            'start_date': '2024-01-15',
            'department': 'Engineering'
        }
        
        print(f"📝 Starting onboarding for: {demo_data['full_name']}")
        
        # Execute onboarding
        result = coordinator.execute_onboarding(demo_data)
        
        if result['status'] == 'SUCCESS':
            print(f"✅ Onboarding completed successfully!")
            print(f"   Onboarding ID: {result['onboarding_id']}")
            print(f"   Duration: {result['onboarding_duration']}")
            return True
        else:
            print(f"❌ Onboarding failed: {result.get('errors', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


def show_status() -> bool:
    """
    Show the current status of the system.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from onboarder.database_manager import DatabaseManager
        
        print("📊 Onboarder System Status")
        print("=" * 40)
        
        db_manager = DatabaseManager()
        summary = db_manager.get_onboarding_summary()
        
        print(f"Database: {os.path.abspath('onboarding.db')}")
        print(f"Total onboardings: {summary.get('total_onboardings', 0)}")
        
        status_counts = summary.get('status_counts', {})
        if status_counts:
            print("\nStatus breakdown:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
        
        phase_counts = summary.get('phase_counts', {})
        if phase_counts:
            print("\nPhase breakdown:")
            for phase, count in phase_counts.items():
                print(f"  {phase}: {count}")
        
        # Show recent onboardings
        all_records = db_manager.get_all_onboarding_records()
        if all_records:
            print(f"\nRecent onboardings:")
            for record in all_records[:5]:  # Show last 5
                print(f"  {record['onboarding_id']}: {record['status']} ({record['current_phase']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to show status: {e}")
        return False


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Onboarder Setup - Initialize database and run system')
    parser.add_argument('--init', action='store_true', help='Initialize the SQLite database')
    parser.add_argument('--migrate', action='store_true', help='Migrate from JSON to SQLite')
    parser.add_argument('--demo', action='store_true', help='Run the onboarding demo')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--db-path', default='onboarding.db', help='Database file path')
    parser.add_argument('--json-file', default='onboarding_state/onboarding_states.json', help='JSON file to migrate from')
    
    args = parser.parse_args()
    
    print("🚀 Onboarder Setup")
    print("=" * 40)
    
    # Check if API key is configured
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your Gemini API key in the .env file")
        return False
    
    success = True
    
    # Initialize database
    if args.init or not any([args.migrate, args.demo, args.status]):
        success = initialize_database(args.db_path) and success
    
    # Migrate from JSON
    if args.migrate:
        success = migrate_from_json(args.json_file) and success
    
    # Show status
    if args.status:
        success = show_status() and success
    
    # Run demo
    if args.demo:
        success = run_demo() and success
    
    # If no specific action, show status and run demo
    if not any([args.init, args.migrate, args.demo, args.status]):
        print("\n🎯 No specific action requested. Showing status and running demo...")
        success = show_status() and success
        print()
        success = run_demo() and success
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python example_usage.py' to see more examples")
        print("2. Run 'python state_management_demo.py' to test state management")
        print("3. Use the CoordinatorAgent in your own code")
    else:
        print("\n❌ Setup completed with errors. Check the logs above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)