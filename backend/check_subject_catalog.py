#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111', cursor_factory=RealDictCursor)
cur = conn.cursor()

# Check subject_catalog columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'subject_catalog' ORDER BY ordinal_position;")
cols = cur.fetchall()
print('subject_catalog columns:')
for col in cols:
    print(f'- {col["column_name"]}')

# Check sample data
cur.execute("SELECT * FROM subject_catalog LIMIT 3;")
samples = cur.fetchall()
print('\nSample subject_catalog data:')
for sample in samples:
    print(sample)

cur.close()
conn.close()