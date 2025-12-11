#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from collections import defaultdict

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='edu',
        user='postgres',
        password='1111',
        port=5432
    )

def analyze_database_structure():
    """Complete analysis of the database structure"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        analysis = {
            'tables': {},
            'foreign_keys': [],
            'indexes': [],
            'constraints': [],
            'sequences': [],
            'statistics': {}
        }
        
        print("=== DATABASE STRUCTURE ANALYSIS ===\n")
        
        # 1. Get all tables with their row counts
        print("1. TABLES AND ROW COUNTS:")
        cursor.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table['tablename']
            
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = cursor.fetchone()['count']
            except:
                row_count = 'ERROR'
            
            # Get table size
            cursor.execute("""
                SELECT pg_size_pretty(pg_total_relation_size(%s)) as size
            """, (table_name,))
            size_result = cursor.fetchone()
            table_size = size_result['size'] if size_result else 'Unknown'
            
            analysis['tables'][table_name] = {
                'row_count': row_count,
                'size': table_size,
                'columns': []
            }
            
            print(f"  {table_name}: {row_count:>8} rows ({table_size})")
        
        # 2. Get detailed column information for each table
        print("\n2. DETAILED TABLE STRUCTURES:")
        for table_name in analysis['tables'].keys():
            print(f"\nTable: {table_name}")
            print("-" * 50)
            
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default,
                    ordinal_position
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            for col in columns:
                col_info = {
                    'name': col['column_name'],
                    'type': col['data_type'],
                    'length': col['character_maximum_length'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default']
                }
                analysis['tables'][table_name]['columns'].append(col_info)
                
                length_info = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                nullable_info = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default_info = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                
                print(f"  {col['column_name']:<25} {col['data_type']}{length_info:<15} {nullable_info}{default_info}")
        
        # 3. Get foreign key relationships
        print("\n3. FOREIGN KEY RELATIONSHIPS:")
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
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
            ORDER BY tc.table_name, kcu.column_name
        """)
        
        foreign_keys = cursor.fetchall()
        for fk in foreign_keys:
            fk_info = dict(fk)
            analysis['foreign_keys'].append(fk_info)
            print(f"  {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # 4. Get indexes
        print("\n4. INDEXES:")
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        indexes = cursor.fetchall()
        current_table = None
        for idx in indexes:
            idx_info = dict(idx)
            analysis['indexes'].append(idx_info)
            
            if current_table != idx['tablename']:
                current_table = idx['tablename']
                print(f"\n  Table: {current_table}")
            
            print(f"    {idx['indexname']}: {idx['indexdef']}")
        
        # 5. Get primary keys
        print("\n5. PRIMARY KEYS:")
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            ORDER BY tc.table_name
        """)
        
        primary_keys = cursor.fetchall()
        for pk in primary_keys:
            print(f"  {pk['table_name']}.{pk['column_name']} (constraint: {pk['constraint_name']})")
        
        # 6. Check for common issues
        print("\n6. POTENTIAL ISSUES DETECTED:")
        
        # Tables without primary keys
        tables_with_pk = set(pk['table_name'] for pk in primary_keys)
        tables_without_pk = set(analysis['tables'].keys()) - tables_with_pk
        if tables_without_pk:
            print(f"  ⚠️  Tables without primary keys: {', '.join(tables_without_pk)}")
        
        # Columns that look like foreign keys but aren't defined as such
        fk_columns = set(f"{fk['table_name']}.{fk['column_name']}" for fk in foreign_keys)
        potential_fks = []
        
        for table_name, table_info in analysis['tables'].items():
            for col in table_info['columns']:
                col_name = col['name']
                if (col_name.endswith('_id') and 
                    col_name != 'id' and 
                    f"{table_name}.{col_name}" not in fk_columns):
                    potential_fks.append(f"{table_name}.{col_name}")
        
        if potential_fks:
            print(f"  ⚠️  Potential missing foreign keys: {', '.join(potential_fks[:10])}...")
        
        # 7. Save detailed analysis to file
        with open('database_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"\n✅ Complete analysis saved to 'database_analysis.json'")
        print(f"📊 Total tables: {len(analysis['tables'])}")
        print(f"🔗 Foreign key relationships: {len(analysis['foreign_keys'])}")
        print(f"📇 Indexes: {len(analysis['indexes'])}")
        
        cursor.close()
        conn.close()
        
        return analysis
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_database_structure()