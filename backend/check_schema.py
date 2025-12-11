#!/usr/bin/env python3
"""
Check database schema
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Add the app directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import sync_engine

def check_table_schema():
    """Check persons table schema"""
    
    with sync_engine.connect() as conn:
        # Check persons table id column
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'persons' AND column_name = 'id'
        """))
        print("Persons table id column:")
        for row in result:
            print(f"  {row}")
        
        # Check if there's a sequence for persons table
        result = conn.execute(text("""
            SELECT s.sequence_name, s.data_type, s.start_value, s.increment
            FROM information_schema.sequences s
            WHERE s.sequence_name LIKE '%persons%' OR s.sequence_name LIKE '%person%'
        """))
        print("\nSequences for persons:")
        for row in result:
            print(f"  {row}")
            
        # Check current max id in persons table
        result = conn.execute(text("SELECT MAX(id) as max_id FROM persons"))
        print(f"\nCurrent max id in persons: {result.fetchone()}")

if __name__ == "__main__":
    check_table_schema()