import psycopg2
from psycopg2.extras import RealDictCursor

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    database='edu',
    user='postgres',
    password='1111',
    cursor_factory=RealDictCursor
)

cursor = conn.cursor()

print('=== ANALYZING TABLES FOR TEACHER-DEPARTMENT RELATIONSHIPS ===\n')

# First, let's see all tables in the database
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
all_tables = [row['table_name'] for row in cursor.fetchall()]

# Look for tables that might contain teacher/department info
relevant_tables = []
keywords = ['teacher', 'person', 'department', 'organization', 'faculty', 'staff', 'employee']

for table in all_tables:
    for keyword in keywords:
        if keyword in table.lower():
            relevant_tables.append(table)
            break

print("Tables that might contain teacher/department information:")
for table in relevant_tables:
    print(f"- {table}")

print(f"\nTotal tables found: {len(relevant_tables)}\n")

# Analyze each relevant table
for table in relevant_tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"=== {table.upper()} ===")
        print(f"Records: {count}")
        
        # Get column info
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """, (table,))
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            print(f"  - {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # Sample a few records to understand the data
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            sample_data = cursor.fetchall()
            print("\nSample data:")
            for i, row in enumerate(sample_data, 1):
                print(f"  Record {i}: {dict(row)}")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"Error analyzing table {table}: {e}")
        print()

conn.close()