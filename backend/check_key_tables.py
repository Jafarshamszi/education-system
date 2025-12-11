#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    conn = psycopg2.connect(
        host='localhost', 
        database='edu', 
        user='postgres', 
        password='1111', 
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()

    print("=== KEY DATABASE TABLES ANALYSIS ===")
    
    # 1. Check education_group table
    print("\n1. EDUCATION_GROUP TABLE:")
    try:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'education_group' ORDER BY ordinal_position;")
        cols = cur.fetchall()
        for col in cols:
            print(f"- {col['column_name']}")
        
        cur.execute("SELECT * FROM education_group LIMIT 3;")
        samples = cur.fetchall()
        print("Sample data:")
        for sample in samples:
            print(sample)
    except Exception as e:
        print(f"Error: {e}")
    
    cur.close()
    conn.close()

    # New connection for each section to avoid transaction issues
    conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111', cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # 2. Check students table structure
    print("\n2. STUDENTS TABLE STRUCTURE:")
    try:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'students' ORDER BY ordinal_position;")
        cols = cur.fetchall()
        for col in cols[:15]:  # First 15 columns
            print(f"- {col['column_name']}")
    except Exception as e:
        print(f"Error: {e}")
    
    cur.close()
    conn.close()

    # 3. Check course table for semester references
    conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111', cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    print("\n3. COURSE TABLE COLUMNS:")
    try:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'course' ORDER BY ordinal_position;")
        cols = cur.fetchall()
        for col in cols:
            print(f"- {col['column_name']}")
    except Exception as e:
        print(f"Error: {e}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()