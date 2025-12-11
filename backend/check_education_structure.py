#!/usr/bin/env python3
"""
Check education plan table structure
"""

from app.api.education_plan import get_db_connection

print('Checking education_plan table structure...')

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'education_plan'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print('Education Plan table columns:')
    for col in columns:
        print(f'  - {col["column_name"]} ({col["data_type"]}) - Nullable: {col["is_nullable"]}')
    
    # Get sample data
    print('\nSample education plan data:')
    cursor.execute('SELECT * FROM education_plan WHERE active = 1 LIMIT 3')
    plans = cursor.fetchall()
    
    for i, plan in enumerate(plans, 1):
        print(f'\nPlan {i}:')
        for key, value in plan.items():
            if value is not None:
                print(f'  {key}: {value}')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {str(e)}')