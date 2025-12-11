#!/usr/bin/env python3
"""
Database Analysis Script for Education System
"""

import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
import json
import sys

# Database connection parameters
DB_CONFIG = {
    'host': '181.238.98.177',
    'database': 'edu',
    'user': 'postgres',
    'password': 'Lkb8MBg7rlN6X3E',
    'port': 5432
}

def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        print(f"✅ Successfully connected to database: {DB_CONFIG['database']}")
        return connection
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def get_all_tables(cursor):
    """Get all tables in the database"""
    cursor.execute("""
        SELECT 
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name;
    """)
    return cursor.fetchall()

def get_table_columns(cursor, table_name, schema='public'):
    """Get column information for a specific table"""
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
    """, (schema, table_name))
    return cursor.fetchall()

def get_foreign_keys(cursor):
    """Get all foreign key relationships"""
    cursor.execute("""
        SELECT
            tc.table_schema,
            tc.table_name,
            kcu.column_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, kcu.column_name;
    """)
    return cursor.fetchall()

def get_table_row_counts(cursor, tables):
    """Get row counts for all tables"""
    row_counts = {}
    for table in tables:
        schema = table['table_schema']
        table_name = table['table_name']
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{table_name}";')
            count = cursor.fetchone()['count']
            row_counts[f"{schema}.{table_name}"] = count
        except Exception as e:
            row_counts[f"{schema}.{table_name}"] = f"Error: {e}"
    return row_counts

def analyze_authentication_tables(cursor):
    """Analyze tables related to authentication and roles"""
    auth_tables = ['accounts', 'users', 'roles', 'permissions', 'user_roles']
    
    auth_info = {}
    for table in auth_tables:
        try:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            
            if cursor.fetchone()['exists']:
                columns = get_table_columns(cursor, table)
                
                # Get sample data
                cursor.execute(f'SELECT * FROM "{table}" LIMIT 5;')
                sample_data = cursor.fetchall()
                
                auth_info[table] = {
                    'columns': columns,
                    'sample_data': sample_data
                }
        except Exception as e:
            auth_info[table] = f"Error: {e}"
    
    return auth_info

def main():
    """Main analysis function"""
    print("🔍 Starting Education Database Analysis...")
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        sys.exit(1)
    
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get basic database info
        cursor.execute("SELECT current_database(), current_user, version();")
        db_info = cursor.fetchone()
        print(f"📊 Database: {db_info['current_database']}")
        print(f"👤 User: {db_info['current_user']}")
        print(f"🐘 PostgreSQL Version: {db_info['version'].split(',')[0]}")
        
        print("\n" + "="*80)
        
        # Get all tables
        print("📋 Getting all tables...")
        tables = get_all_tables(cursor)
        print(f"Found {len(tables)} tables")
        
        # Show table summary
        print("\n🗂️  TABLE SUMMARY:")
        for table in tables:
            schema = table['table_schema']
            name = table['table_name']
            type_ = table['table_type']
            print(f"  📄 {schema}.{name} ({type_})")
        
        # Get row counts
        print("\n📊 Getting row counts...")
        row_counts = get_table_row_counts(cursor, tables)
        
        print("\n📈 ROW COUNTS:")
        for table_name, count in sorted(row_counts.items(), key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True):
            if isinstance(count, int):
                print(f"  📊 {table_name}: {count:,} rows")
            else:
                print(f"  ❌ {table_name}: {count}")
        
        # Analyze foreign keys
        print("\n🔗 Getting foreign key relationships...")
        foreign_keys = get_foreign_keys(cursor)
        
        print("\n🔗 FOREIGN KEY RELATIONSHIPS:")
        for fk in foreign_keys:
            print(f"  🔗 {fk['table_name']}.{fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # Analyze authentication-related tables
        print("\n🔐 Analyzing authentication tables...")
        auth_info = analyze_authentication_tables(cursor)
        
        print("\n🔐 AUTHENTICATION TABLES:")
        for table_name, info in auth_info.items():
            if isinstance(info, dict):
                print(f"  ✅ {table_name}: {len(info['columns'])} columns, {len(info['sample_data'])} sample rows")
                for col in info['columns']:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"    📝 {col['column_name']} ({col['data_type']}) {nullable}")
            else:
                print(f"  ❌ {table_name}: {info}")
        
        # Detailed table analysis for key tables
        key_tables = ['accounts', 'students', 'teachers', 'persons', 'courses', 'groups']
        
        print("\n📊 DETAILED TABLE ANALYSIS:")
        for table_name in key_tables:
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                if cursor.fetchone()['exists']:
                    columns = get_table_columns(cursor, table_name)
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                    count = cursor.fetchone()['count']
                    
                    print(f"\n  📋 {table_name.upper()} ({count:,} rows):")
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                        print(f"    📝 {col['column_name']}: {col['data_type']}{length} {nullable}{default}")
                        
            except Exception as e:
                print(f"  ❌ Error analyzing {table_name}: {e}")
        
        print("\n✅ Database analysis completed!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()