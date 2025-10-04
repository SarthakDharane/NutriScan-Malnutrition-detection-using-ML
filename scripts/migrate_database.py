#!/usr/bin/env python3
"""
Database Migration Script for Enhanced Malnutrition Analysis System
Adds new fields to the reports table for advanced reporting features
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text

def migrate_database():
    """Migrate the database to add new fields"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the new columns already exist
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('reports')]
            
            print("Existing columns:", existing_columns)
            
            # List of new columns to add
            new_columns = [
                ('skin_severity', 'VARCHAR(20)'),
                ('nail_severity', 'VARCHAR(20)'),
                ('skin_confidence', 'FLOAT'),
                ('nail_confidence', 'FLOAT'),
                ('bmi_percentile', 'FLOAT'),
                ('bmi_z_score', 'FLOAT'),
                ('bmi_category', 'VARCHAR(20)'),
                ('malnutrition_risk_score', 'INTEGER'),
                ('risk_level', 'VARCHAR(20)'),
                ('dietary_recommendations', 'TEXT'),
                ('lifestyle_recommendations', 'TEXT'),
                ('hydration_tips', 'TEXT'),
                ('professional_consultation', 'BOOLEAN')
            ]
            
            # Add new columns if they don't exist
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    print(f"Adding column: {column_name}")
                    sql = f"ALTER TABLE reports ADD COLUMN {column_name} {column_type}"
                    db.session.execute(text(sql))
                    print(f"✓ Added column: {column_name}")
                else:
                    print(f"Column already exists: {column_name}")
            
            # Commit changes
            db.session.commit()
            print("\n✓ Database migration completed successfully!")
            
            # Show final table structure
            print("\nFinal table structure:")
            final_columns = [col['name'] for col in inspector.get_columns('reports')]
            for col in final_columns:
                print(f"  - {col}")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False
    
    return True

def rollback_migration():
    """Rollback the migration by removing new columns"""
    app = create_app()
    
    with app.app_context():
        try:
            # List of columns to remove
            columns_to_remove = [
                'skin_severity',
                'nail_severity', 
                'skin_confidence',
                'nail_confidence',
                'bmi_percentile',
                'bmi_z_score',
                'bmi_category',
                'malnutrition_risk_score',
                'risk_level',
                'dietary_recommendations',
                'lifestyle_recommendations',
                'hydration_tips',
                'professional_consultation'
            ]
            
            # Remove columns
            for column_name in columns_to_remove:
                try:
                    sql = f"ALTER TABLE reports DROP COLUMN {column_name}"
                    db.session.execute(text(sql))
                    print(f"✓ Removed column: {column_name}")
                except Exception as e:
                    print(f"Column {column_name} may not exist: {e}")
            
            # Commit changes
            db.session.commit()
            print("\n✓ Rollback completed successfully!")
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration for enhanced malnutrition analysis')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    
    args = parser.parse_args()
    
    if args.rollback:
        print("Rolling back migration...")
        success = rollback_migration()
    else:
        print("Running database migration...")
        success = migrate_database()
    
    if success:
        print("\n🎉 Operation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Operation failed!")
        sys.exit(1)
