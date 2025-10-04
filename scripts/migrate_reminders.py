#!/usr/bin/env python3
"""
Database Migration Script for Reminder System
Adds the reminders table for check-up reminders functionality
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.reminder import Reminder

def migrate_reminders():
    """Create the reminders table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the reminders table
            db.create_all()
            print("✓ Reminders table created successfully!")
            
            # Verify the table was created
            inspector = db.inspect(db.engine)
            if 'reminders' in inspector.get_table_names():
                print("✓ Reminders table verified in database")
                
                # Show table structure
                columns = inspector.get_columns('reminders')
                print("\nReminders table structure:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("❌ Reminders table not found after creation")
                return False
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    return True

def rollback_reminders():
    """Remove the reminders table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Drop the reminders table
            db.drop_all()
            print("✓ Reminders table removed successfully!")
                
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration for reminder system')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    
    args = parser.parse_args()
    
    if args.rollback:
        print("Rolling back reminder migration...")
        success = rollback_reminders()
    else:
        print("Running reminder migration...")
        success = migrate_reminders()
    
    if success:
        print("\n🎉 Operation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Operation failed!")
        sys.exit(1)
