#!/usr/bin/env python3
"""
Complete Database Comparison Script
Analyzes OLD (edu) vs NEW (lms) databases
Identifies ALL unmigrated tables with detailed analysis
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# Database connections
OLD_DB = {
    'dbname': 'edu',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': 5432
}

NEW_DB = {
    'dbname': 'lms',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': 5432
}

def get_connection(db_config):
    """Create database connection"""
    return psycopg2.connect(**db_config, cursor_factory=RealDictCursor)

def get_all_tables_info(conn):
    """Get detailed information about all tables"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                t.tablename,
                pg_size_pretty(pg_total_relation_size('public.' || t.tablename)) as size,
                pg_total_relation_size('public.' || t.tablename) as size_bytes,
                (SELECT COUNT(*) 
                 FROM information_schema.columns 
                 WHERE table_schema = 'public' AND table_name = t.tablename) as column_count,
                obj_description(('public.' || t.tablename)::regclass, 'pg_class') as description
            FROM pg_tables t
            WHERE t.schemaname = 'public'
            ORDER BY pg_total_relation_size('public.' || t.tablename) DESC
        """)
        return cur.fetchall()

def get_table_row_count(conn, table_name):
    """Get row count for a table"""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            result = cur.fetchone()
            return result['count'] if result else 0
    except Exception as e:
        return f"Error: {str(e)}"

def get_table_columns(conn, table_name):
    """Get column information for a table"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        return cur.fetchall()

def get_foreign_keys(conn, table_name):
    """Get foreign key information"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name = %s
        """, (table_name,))
        return cur.fetchall()

def analyze_table_sample_data(conn, table_name, limit=5):
    """Get sample data from table"""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            return cur.fetchall()
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("=" * 100)
    print("COMPLETE DATABASE COMPARISON ANALYSIS")
    print("=" * 100)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"OLD Database: edu")
    print(f"NEW Database: lms")
    print("=" * 100)
    print()

    # Connect to both databases
    old_conn = get_connection(OLD_DB)
    new_conn = get_connection(NEW_DB)

    # Get all tables from both databases
    print("📊 Gathering table information from both databases...")
    old_tables_info = get_all_tables_info(old_conn)
    new_tables_info = get_all_tables_info(new_conn)

    old_tables = {t['tablename']: t for t in old_tables_info}
    new_tables = {t['tablename']: t for t in new_tables_info}

    print(f"   OLD Database (edu): {len(old_tables)} tables")
    print(f"   NEW Database (lms): {len(new_tables)} tables")
    print()

    # Identify migrated and unmigrated tables
    migrated_tables = []
    unmigrated_tables = []
    
    # Define migration mapping (old table -> new table)
    table_mapping = {
        'users': 'users',
        'person': 'persons',
        'student': 'students',
        'teachers': 'staff_members',
        'course': 'courses',
        'course_plan': 'course_offerings',
        'course_plan_student': 'course_enrollments',
        'course_plan_teachers': 'course_instructors',
        'journal': 'assessments',
        'journal_details': 'grades',
        'organizations': 'organization_units',
        'education_plan': 'academic_terms',
    }

    print("🔍 MIGRATION STATUS ANALYSIS")
    print("=" * 100)
    print()

    # Check each old table
    for old_name, old_info in old_tables.items():
        row_count = get_table_row_count(old_conn, old_name)
        
        # Check if migrated
        new_name = table_mapping.get(old_name, old_name)
        is_migrated = new_name in new_tables
        
        if is_migrated:
            new_count = get_table_row_count(new_conn, new_name)
            migrated_tables.append({
                'old_name': old_name,
                'new_name': new_name,
                'old_count': row_count,
                'new_count': new_count,
                'size': old_info['size'],
                'columns': old_info['column_count']
            })
        else:
            unmigrated_tables.append({
                'table_name': old_name,
                'row_count': row_count,
                'size': old_info['size'],
                'size_bytes': old_info['size_bytes'],
                'columns': old_info['column_count']
            })

    # Sort unmigrated by size
    unmigrated_tables.sort(key=lambda x: x['size_bytes'] if isinstance(x['size_bytes'], int) else 0, reverse=True)

    print(f"✅ MIGRATED TABLES: {len(migrated_tables)}")
    print(f"❌ UNMIGRATED TABLES: {len(unmigrated_tables)}")
    print()

    # Print migrated tables summary
    print("=" * 100)
    print("MIGRATED TABLES SUMMARY")
    print("=" * 100)
    for m in migrated_tables:
        print(f"✓ {m['old_name']:30s} -> {m['new_name']:30s} | Old: {str(m['old_count']).rjust(10)} | New: {str(m['new_count']).rjust(10)} | {m['size']}")
    print()

    # Detailed analysis of unmigrated tables
    print("=" * 100)
    print("UNMIGRATED TABLES DETAILED ANALYSIS")
    print("=" * 100)
    print()

    total_unmigrated_records = 0
    critical_tables = []
    operational_tables = []
    system_tables = []
    log_tables = []

    for idx, table in enumerate(unmigrated_tables, 1):
        table_name = table['table_name']
        row_count = table['row_count']
        
        if isinstance(row_count, int):
            total_unmigrated_records += row_count

        print(f"\n{'=' * 100}")
        print(f"TABLE #{idx}: {table_name}")
        print(f"{'=' * 100}")
        print(f"📊 Records: {row_count:,} | Size: {table['size']} | Columns: {table['columns']}")
        
        # Get column structure
        columns = get_table_columns(old_conn, table_name)
        print(f"\n📋 COLUMN STRUCTURE ({len(columns)} columns):")
        for col in columns[:10]:  # Show first 10 columns
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"   - {col['column_name']:30s} {col['data_type']:20s} {nullable}")
        if len(columns) > 10:
            print(f"   ... and {len(columns) - 10} more columns")
        
        # Get foreign keys
        fks = get_foreign_keys(old_conn, table_name)
        if fks:
            print(f"\n🔗 FOREIGN KEYS ({len(fks)}):")
            for fk in fks:
                print(f"   - {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # Sample data
        if isinstance(row_count, int) and row_count > 0 and row_count < 1000000:
            samples = analyze_table_sample_data(old_conn, table_name, 3)
            if isinstance(samples, list) and samples:
                print(f"\n📝 SAMPLE DATA (first 3 rows):")
                for i, sample in enumerate(samples, 1):
                    print(f"   Row {i}: {dict(list(sample.items())[:5])}")  # Show first 5 fields
        
        # Categorize table
        table_lower = table_name.lower()
        if any(x in table_lower for x in ['log', 'logs', 'action', 'error', 'transaction']):
            log_tables.append(table)
            print(f"\n🏷️  CATEGORY: LOG/AUDIT TABLE")
        elif any(x in table_lower for x in ['meeting', 'schedule', 'attendance', 'file', 'resource', 'exercise']):
            critical_tables.append(table)
            print(f"\n🏷️  CATEGORY: CRITICAL ACADEMIC DATA")
        elif any(x in table_lower for x in ['notification', 'message', 'announcement', 'news']):
            operational_tables.append(table)
            print(f"\n🏷️  CATEGORY: OPERATIONAL DATA")
        elif any(x in table_lower for x in ['session', 'token', 'cache', 'queue']):
            system_tables.append(table)
            print(f"\n🏷️  CATEGORY: SYSTEM/TEMPORARY DATA")
        else:
            # Analyze by record count and size
            if isinstance(row_count, int):
                if row_count > 10000:
                    critical_tables.append(table)
                    print(f"\n🏷️  CATEGORY: CRITICAL (Large dataset)")
                else:
                    operational_tables.append(table)
                    print(f"\n🏷️  CATEGORY: OPERATIONAL (Moderate dataset)")

    # Final Summary
    print("\n" + "=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)
    print(f"\n📊 TOTAL TABLES IN OLD DATABASE: {len(old_tables)}")
    print(f"   ✅ Migrated: {len(migrated_tables)}")
    print(f"   ❌ Unmigrated: {len(unmigrated_tables)}")
    print(f"\n📈 TOTAL UNMIGRATED RECORDS: {total_unmigrated_records:,}")
    print(f"\n📁 UNMIGRATED TABLE CATEGORIES:")
    print(f"   🎯 Critical Academic Data: {len(critical_tables)} tables")
    print(f"   ⚙️  Operational Data: {len(operational_tables)} tables")
    print(f"   🖥️  System/Temporary: {len(system_tables)} tables")
    print(f"   📋 Logs/Audit: {len(log_tables)} tables")
    
    print(f"\n🎯 CRITICAL TABLES TO MIGRATE ({len(critical_tables)}):")
    for t in critical_tables[:20]:  # Top 20
        print(f"   - {t['table_name']:40s} {str(t['row_count']).rjust(15):s} records  {t['size']}")
    
    print(f"\n⚙️  OPERATIONAL TABLES TO REVIEW ({len(operational_tables)}):")
    for t in operational_tables[:10]:  # Top 10
        print(f"   - {t['table_name']:40s} {str(t['row_count']).rjust(15):s} records  {t['size']}")

    # Save detailed report
    report = {
        'analysis_date': datetime.now().isoformat(),
        'old_database': 'edu',
        'new_database': 'lms',
        'total_old_tables': len(old_tables),
        'total_new_tables': len(new_tables),
        'migrated_count': len(migrated_tables),
        'unmigrated_count': len(unmigrated_tables),
        'total_unmigrated_records': total_unmigrated_records,
        'migrated_tables': migrated_tables,
        'unmigrated_tables': unmigrated_tables,
        'critical_tables': critical_tables,
        'operational_tables': operational_tables,
        'system_tables': system_tables,
        'log_tables': log_tables
    }

    with open('COMPLETE_MIGRATION_GAP_ANALYSIS.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: COMPLETE_MIGRATION_GAP_ANALYSIS.json")
    print("=" * 100)

    # Close connections
    old_conn.close()
    new_conn.close()

if __name__ == '__main__':
    main()
