#!/usr/bin/env python3
"""
Onboarder Setup Script

A single file that initializes the SQLite database and runs the Onboarder system.
"""

import os
import sys
import asyncio
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv

# Add the onboarder package to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def initialize_database(db_path: Optional[str] = None) -> bool:
    """
    Initialize the SQLite database.
    
    Args:
        db_path: Path to the database file (defaults to the DatabaseManager default)
        
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
        print(f"   Database file: {db_manager.db_path.resolve()}")
        print(f"   Current records: {summary.get('total_onboardings', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def migrate_from_json(json_file: str = "onboarding_state/onboarding_states.json",
                      db_path: Optional[str] = None) -> bool:
    """
    Migrate data from JSON file to SQLite database.
    
    Args:
        json_file: Path to the JSON state file
        db_path: Path to the database file (defaults to the DatabaseManager default)
        
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
        db_manager = DatabaseManager(db_path)
        
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


def run_demo(db_path: Optional[str] = None) -> bool:
    """
    Run the onboarding demo through the AgentOrchestrator (same flow as the API server).
    
    Args:
        db_path: Path to the database file (defaults to the DatabaseManager default)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("🚀 Running onboarding demo...")
        
        from onboarder.database_manager import DatabaseManager
        from onboarder.agent_orchestrator import AgentOrchestrator
        
        db_manager = DatabaseManager(db_path)
        orchestrator = AgentOrchestrator(db_manager)
        
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
        
        onboarding_id = db_manager.create_onboarding_record(demo_data)
        if not onboarding_id:
            print("❌ Failed to create onboarding record")
            return False
        
        record = db_manager.get_onboarding_record(onboarding_id)
        employee_id = record['employee_id']
        
        run_id = db_manager.claim_onboarding(onboarding_id)
        if not run_id:
            print("❌ Could not start onboarding")
            return False
        
        # Execute onboarding (all phases)
        asyncio.run(orchestrator.start_onboarding_process(employee_id, onboarding_id, run_id))
        
        result = db_manager.get_onboarding_record(onboarding_id)
        
        if result['status'] == 'COMPLETED':
            print(f"✅ Onboarding completed successfully!")
            print(f"   Employee ID: {employee_id}")
            print(f"   Onboarding ID: {onboarding_id}")
            print(f"   Completed phases: {', '.join(result['completed_phases'])}")
            return True
        else:
            print(f"❌ Onboarding ended with status {result['status']}: {result.get('errors') or 'Unknown error'}")
            return False
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


def show_status(db_path: Optional[str] = None) -> bool:
    """
    Show the current status of the system.
    
    Args:
        db_path: Path to the database file (defaults to the DatabaseManager default)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from onboarder.database_manager import DatabaseManager
        
        print("📊 Onboarder System Status")
        print("=" * 40)
        
        db_manager = DatabaseManager(db_path)
        summary = db_manager.get_onboarding_summary()
        
        print(f"Database: {db_manager.db_path.resolve()}")
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
    parser.add_argument('--db-path', default=None,
                        help='Database file path (default: ONBOARDER_DB_PATH or onboarding.db in the project directory)')
    parser.add_argument('--json-file', default='onboarding_state/onboarding_states.json', help='JSON file to migrate from')
    
    args = parser.parse_args()
    
    print("🚀 Onboarder Setup")
    print("=" * 40)
    
    no_action = not any([args.init, args.migrate, args.demo, args.status])
    
    # The demo calls Gemini, so it needs an API key
    if (args.demo or no_action) and not os.getenv('GEMINI_API_KEY'):
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your Gemini API key in the .env file")
        return False
    
    success = True
    
    # Initialize database
    if args.init or not any([args.migrate, args.demo, args.status]):
        success = initialize_database(args.db_path) and success
    
    # Migrate from JSON
    if args.migrate:
        success = migrate_from_json(args.json_file, args.db_path) and success
    
    # Show status
    if args.status:
        success = show_status(args.db_path) and success
    
    # Run demo
    if args.demo:
        success = run_demo(args.db_path) and success
    
    # If no specific action, show status and run demo
    if no_action:
        print("\n🎯 No specific action requested. Showing status and running demo...")
        success = show_status(args.db_path) and success
        print()
        success = run_demo(args.db_path) and success
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the API server with 'python main.py'")
        print("2. Open http://localhost:8050/docs to explore the API")
        print("3. Run 'python test_api_server.py' against the running server")
    else:
        print("\n❌ Setup completed with errors. Check the logs above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)