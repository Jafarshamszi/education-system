#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111', cursor_factory=RealDictCursor)
cur = conn.cursor()

print("=== FINDING CORRECT TABLE NAMES ===")

# Find education/language tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND (table_name LIKE '%education%' OR table_name LIKE '%lang%') ORDER BY table_name;")
tables = cur.fetchall()
print("Education/Language tables:")
for table in tables:
    print(f"- {table['table_name']}")

cur.close()
conn.close()

# New connection
conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111', cursor_factory=RealDictCursor)
cur = conn.cursor()

print("\nEducation dictionary tables:")
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%dic%' AND table_name LIKE '%edu%' ORDER BY table_name;")
tables = cur.fetchall()
for table in tables:
    print(f"- {table['table_name']}")

cur.close()
conn.close()