#!/usr/bin/env python3
"""
Database Manager for the Onboarder system.

Handles SQLite database operations for persistent storage of onboarding data.
Replaces the JSON-based state management system.
"""

import os
import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for onboarding processes."""
    
    def __init__(self, db_path: str = "onboarding.db"):
        """
        Initialize the DatabaseManager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create onboarding records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS onboarding_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT UNIQUE NOT NULL,
                    onboarding_id TEXT UNIQUE NOT NULL,
                    new_hire_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    current_phase TEXT NOT NULL DEFAULT 'PRE_BOARDING',
                    completed_phases TEXT,
                    start_time TEXT,
                    last_updated TEXT NOT NULL,
                    end_time TEXT,
                    process_log TEXT,
                    errors TEXT,
                    results TEXT,
                    onboarding_context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create phase results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phase_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    onboarding_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    results TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (onboarding_id) REFERENCES onboarding_records (onboarding_id)
                )
            ''')
            
            # Create employee sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    employee_name TEXT NOT NULL,
                    onboarding_id TEXT,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (onboarding_id) REFERENCES onboarding_records (onboarding_id)
                )
            ''')
            
            # Create session notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES employee_sessions (session_id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_onboarding_status ON onboarding_records (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_onboarding_phase ON onboarding_records (current_phase)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_phase_results_onboarding ON phase_results (onboarding_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON employee_sessions (status)')
            
            # Add new columns if they don't exist (migration for existing databases)
            try:
                cursor.execute('ALTER TABLE onboarding_records ADD COLUMN employee_id TEXT')
                logger.info("Added employee_id column to onboarding_records table")
            except sqlite3.OperationalError:
                # Column already exists, ignore
                pass
            
            try:
                cursor.execute('ALTER TABLE onboarding_records ADD COLUMN onboarding_context TEXT')
                logger.info("Added onboarding_context column to onboarding_records table")
            except sqlite3.OperationalError:
                # Column already exists, ignore
                pass
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def create_onboarding_record(self, new_hire_data: Dict[str, str], employee_id: str = None) -> str:
        """
        Create a new onboarding record.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            employee_id: Optional employee ID, if not provided will be auto-generated
            
        Returns:
            str: Unique onboarding ID
        """
        try:
            # Always generate employee ID automatically if not provided
            if not employee_id:
                # Create a clean employee ID from name and timestamp
                name_clean = new_hire_data.get('full_name', 'unknown').lower().replace(' ', '_').replace('-', '_')
                # Remove special characters
                name_clean = ''.join(c for c in name_clean if c.isalnum() or c == '_')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                employee_id = f"emp_{name_clean}_{timestamp}"
            
            # Generate unique onboarding ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_clean = new_hire_data.get('full_name', 'unknown').lower().replace(' ', '_').replace('-', '_')
            name_clean = ''.join(c for c in name_clean if c.isalnum() or c == '_')
            onboarding_id = f"onboard_{name_clean}_{timestamp}"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO onboarding_records 
                    (employee_id, onboarding_id, new_hire_data, status, current_phase, completed_phases, 
                     start_time, last_updated, process_log, errors, results, onboarding_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id,
                    onboarding_id,
                    json.dumps(new_hire_data),
                    'PENDING',
                    'PRE_BOARDING',
                    json.dumps([]),
                    None,  # start_time will be set when onboarding begins
                    datetime.now().isoformat(),
                    json.dumps([]),
                    json.dumps([]),
                    json.dumps({}),
                    json.dumps({})  # onboarding_context for storing markdown templates
                ))
                
                conn.commit()
                logger.info(f"Created onboarding record: {onboarding_id}")
                return onboarding_id
                
        except Exception as e:
            logger.error(f"Failed to create onboarding record: {e}")
            return ""
    
    def update_onboarding_record(self, onboarding_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing onboarding record.
        
        Args:
            onboarding_id: Unique onboarding ID
            updates: Dictionary of updates to apply
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['new_hire_data', 'completed_phases', 'process_log', 'errors', 'results', 'onboarding_context']:
                        set_clauses.append(f"{key} = ?")
                        values.append(json.dumps(value))
                    else:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                set_clauses.append("last_updated = ?")
                values.append(datetime.now().isoformat())
                values.append(onboarding_id)
                
                query = f"UPDATE onboarding_records SET {', '.join(set_clauses)} WHERE onboarding_id = ?"
                cursor.execute(query, values)
                
                if cursor.rowcount == 0:
                    logger.error(f"Onboarding ID {onboarding_id} not found")
                    return False
                
                conn.commit()
                logger.debug(f"Updated onboarding record: {onboarding_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update onboarding record: {e}")
            return False
    
    def get_onboarding_record(self, onboarding_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an onboarding record by ID.
        
        Args:
            onboarding_id: Unique onboarding ID
            
        Returns:
            Dict[str, Any]: Onboarding record or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM onboarding_records WHERE onboarding_id = ?
                ''', (onboarding_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get onboarding record: {e}")
            return None
    
    def get_onboarding_by_employee_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an onboarding record by employee ID.
        
        Args:
            employee_id: Unique employee ID
            
        Returns:
            Dict[str, Any]: Onboarding record or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM onboarding_records WHERE employee_id = ?
                ''', (employee_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get onboarding record by employee_id: {e}")
            return None
    
    def get_all_onboarding_records(self) -> List[Dict[str, Any]]:
        """
        Get all onboarding records.
        
        Returns:
            List[Dict[str, Any]]: List of all onboarding records
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM onboarding_records ORDER BY created_at DESC
                ''')
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all onboarding records: {e}")
            return []
    
    def get_onboarding_records_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get onboarding records by status.
        
        Args:
            status: Status to filter by (IN_PROGRESS, COMPLETED, FAILED)
            
        Returns:
            List[Dict[str, Any]]: List of matching onboarding records
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM onboarding_records WHERE status = ? ORDER BY created_at DESC
                ''', (status,))
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get onboarding records by status: {e}")
            return []
    
    def add_phase_result(self, onboarding_id: str, phase: str, agent: str, 
                        status: str, results: Dict[str, Any] = None, 
                        error_message: str = None) -> bool:
        """
        Add a phase result to the database.
        
        Args:
            onboarding_id: Unique onboarding ID
            phase: Phase name (PRE_BOARDING, DAY1_SETUP, FIRST_WEEK_INTEGRATION)
            agent: Agent name that processed the phase
            status: Result status (SUCCESS, FAILED, IN_PROGRESS)
            results: Results data
            error_message: Error message if failed
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO phase_results 
                    (onboarding_id, phase, agent, status, results, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    onboarding_id,
                    phase,
                    agent,
                    status,
                    json.dumps(results) if results else None,
                    error_message
                ))
                
                conn.commit()
                logger.debug(f"Added phase result for {onboarding_id}: {phase}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add phase result: {e}")
            return False
    
    def get_phase_results(self, onboarding_id: str) -> List[Dict[str, Any]]:
        """
        Get all phase results for an onboarding record.
        
        Args:
            onboarding_id: Unique onboarding ID
            
        Returns:
            List[Dict[str, Any]]: List of phase results
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM phase_results 
                    WHERE onboarding_id = ? 
                    ORDER BY created_at ASC
                ''', (onboarding_id,))
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get phase results: {e}")
            return []
    
    def create_employee_session(self, employee_name: str, onboarding_id: str = None) -> str:
        """
        Create a new employee session.
        
        Args:
            employee_name: Name of the employee
            onboarding_id: Associated onboarding ID (optional)
            
        Returns:
            str: Unique session ID
        """
        try:
            session_id = f"session_{employee_name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO employee_sessions 
                    (session_id, employee_name, onboarding_id, status)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, employee_name, onboarding_id, 'ACTIVE'))
                
                conn.commit()
                logger.info(f"Created employee session: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"Failed to create employee session: {e}")
            return ""
    
    def add_session_notification(self, session_id: str, message: str, 
                               notification_type: str = "INFO") -> bool:
        """
        Add a notification to an employee session.
        
        Args:
            session_id: Session ID
            message: Notification message
            notification_type: Type of notification (INFO, SUCCESS, ERROR, WARNING)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO session_notifications 
                    (session_id, message, notification_type)
                    VALUES (?, ?, ?)
                ''', (session_id, message, notification_type))
                
                # Update last activity
                cursor.execute('''
                    UPDATE employee_sessions 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_id = ?
                ''', (session_id,))
                
                conn.commit()
                logger.debug(f"Added notification to session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add session notification: {e}")
            return False
    
    def get_session_notifications(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all notifications for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[Dict[str, Any]]: List of notifications
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM session_notifications 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC
                ''', (session_id,))
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get session notifications: {e}")
            return []
    
    def get_onboarding_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all onboarding processes.
        
        Returns:
            Dict[str, Any]: Summary statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get counts by status
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM onboarding_records 
                    GROUP BY status
                ''')
                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Get counts by phase
                cursor.execute('''
                    SELECT current_phase, COUNT(*) as count 
                    FROM onboarding_records 
                    GROUP BY current_phase
                ''')
                phase_counts = {row['current_phase']: row['count'] for row in cursor.fetchall()}
                
                # Get total count
                cursor.execute('SELECT COUNT(*) as total FROM onboarding_records')
                total_count = cursor.fetchone()['total']
                
                return {
                    'total_onboardings': total_count,
                    'status_counts': status_counts,
                    'phase_counts': phase_counts,
                    'active_sessions': self._get_active_session_count()
                }
                
        except Exception as e:
            logger.error(f"Failed to get onboarding summary: {e}")
            return {}
    
    def _get_active_session_count(self) -> int:
        """Get count of active sessions."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM employee_sessions WHERE status = "ACTIVE"')
                return cursor.fetchone()['count']
        except Exception:
            return 0
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        result = dict(row)
        
        # Parse JSON fields
        json_fields = ['new_hire_data', 'completed_phases', 'process_log', 'errors', 'results', 'onboarding_context']
        for field in json_fields:
            if field in result and result[field]:
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return result
    
    def migrate_from_json(self, json_file_path: str) -> bool:
        """
        Migrate data from JSON state file to SQLite database.
        
        Args:
            json_file_path: Path to the JSON state file
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            json_path = Path(json_file_path)
            if not json_path.exists():
                logger.error(f"JSON file not found: {json_file_path}")
                return False
            
            with open(json_path, 'r') as f:
                states = json.load(f)
            
            migrated_count = 0
            for onboarding_id, state_data in states.items():
                try:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Insert onboarding record
                        cursor.execute('''
                            INSERT OR REPLACE INTO onboarding_records 
                            (onboarding_id, new_hire_data, status, current_phase, completed_phases, 
                             start_time, last_updated, end_time, process_log, errors)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            onboarding_id,
                            json.dumps(state_data.get('new_hire_data', {})),
                            state_data.get('status', 'IN_PROGRESS'),
                            state_data.get('current_phase', 'PRE_BOARDING'),
                            json.dumps(state_data.get('completed_phases', [])),
                            state_data.get('start_time', datetime.now().isoformat()),
                            state_data.get('last_updated', datetime.now().isoformat()),
                            state_data.get('end_time'),
                            json.dumps(state_data.get('process_log', [])),
                            json.dumps(state_data.get('errors', []))
                        ))
                        
                        # Migrate phase results if they exist
                        results = state_data.get('results', {})
                        for phase, phase_data in results.items():
                            for agent, agent_data in phase_data.items():
                                cursor.execute('''
                                    INSERT INTO phase_results 
                                    (onboarding_id, phase, agent, status, results)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (
                                    onboarding_id,
                                    phase.upper(),
                                    agent,
                                    agent_data.get('status', 'SUCCESS'),
                                    json.dumps(agent_data)
                                ))
                        
                        conn.commit()
                        migrated_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to migrate record {onboarding_id}: {e}")
                    continue
            
            logger.info(f"Successfully migrated {migrated_count} records from JSON to SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate from JSON: {e}")
            return False
    
    def backup_database(self, backup_path: str = None) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for backup file (optional)
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"onboarding_backup_{timestamp}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def clear_database(self) -> bool:
        """
        Clear all data from the database (reset to empty state).
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear all tables
                cursor.execute('DELETE FROM session_notifications')
                cursor.execute('DELETE FROM employee_sessions')
                cursor.execute('DELETE FROM phase_results')
                cursor.execute('DELETE FROM onboarding_records')
                
                # Reset auto-increment counters
                cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("onboarding_records", "phase_results", "employee_sessions", "session_notifications")')
                
                conn.commit()
                logger.info("Database cleared successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
    
    def reset_database(self) -> bool:
        """
        Reset the database by clearing all data and reinitializing schema.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clear existing data
            self.clear_database()
            
            # Reinitialize schema
            self._init_database()
            
            logger.info("Database reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False
