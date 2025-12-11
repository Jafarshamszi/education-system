import psycopg2
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111')
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Find schedule/class/course related tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND (table_name ILIKE '%schedule%' OR table_name ILIKE '%class%' OR 
             table_name ILIKE '%course%' OR table_name ILIKE '%lesson%' OR 
             table_name ILIKE '%time%' OR table_name ILIKE '%semester%')
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print('Schedule/Class/Course related tables:')
    for table in tables:
        print(f'- {table["table_name"]}')
    
    print('\n' + '='*50)
    print('ALL TABLES IN DATABASE:')
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    all_tables = cursor.fetchall()
    for table in all_tables:
        print(f'- {table["table_name"]}')
    
    conn.close()
except Exception as e:
    print(f'Error: {e}')