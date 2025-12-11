import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    database='edu', 
    user='postgres', 
    password='1111', 
    port='5432'
)
cursor = conn.cursor()

# Get all table names
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name LIKE '%student%' OR table_name LIKE '%teacher%')
    ORDER BY table_name
""")

tables = cursor.fetchall()
print("Student and Teacher related tables:")
for table in tables:
    print(f"  {table[0]}")

cursor.close()
conn.close()