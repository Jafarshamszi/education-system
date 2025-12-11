#!/usr/bin/env python3
"""
Comprehensive Database Analysis Script
Analyzes the entire education system database structure, data, and relationships
"""

from sqlalchemy import create_engine, text, inspect
import json
from datetime import datetime
from collections import defaultdict

# Database connection
engine = create_engine('postgresql://postgres:1111@localhost:5432/edu')

def get_all_tables_with_counts():
    """Get all tables with row counts"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY size_bytes DESC
        """))
        
        tables = []
        for row in result:
            table_name = row[1]
            
            # Get row count
            try:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.scalar()
            except:
                row_count = 0
            
            tables.append({
                'name': table_name,
                'size': row[2],
                'size_bytes': row[3],
                'row_count': row_count
            })
        
        return tables

def get_table_structure(table_name):
    """Get detailed structure of a table"""
    with engine.connect() as conn:
        # Get columns
        columns_result = conn.execute(text(f"""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """))
        
        columns = []
        for row in columns_result:
            col_info = {
                'name': row[0],
                'type': row[1],
                'max_length': row[2],
                'nullable': row[3] == 'YES',
                'default': row[4]
            }
            columns.append(col_info)
        
        # Get indexes
        indexes_result = conn.execute(text(f"""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = '{table_name}'
        """))
        
        indexes = []
        for row in indexes_result:
            indexes.append({
                'name': row[0],
                'definition': row[1]
            })
        
        # Get constraints
        constraints_result = conn.execute(text(f"""
            SELECT
                conname,
                contype,
                pg_get_constraintdef(oid) as definition
            FROM pg_constraint
            WHERE conrelid = '{table_name}'::regclass
        """))
        
        constraints = []
        for row in constraints_result:
            constraints.append({
                'name': row[0],
                'type': row[1],
                'definition': row[2]
            })
        
        return {
            'columns': columns,
            'indexes': indexes,
            'constraints': constraints
        }

def analyze_data_quality(table_name, sample_size=5):
    """Analyze data quality for a table"""
    with engine.connect() as conn:
        try:
            # Get sample data
            sample_result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {sample_size}"))
            samples = [dict(row._mapping) for row in sample_result]
            
            # Get null counts per column
            columns_result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """))
            
            null_counts = {}
            for col_row in columns_result:
                col_name = col_row[0]
                try:
                    null_result = conn.execute(text(f"""
                        SELECT COUNT(*) FROM {table_name} 
                        WHERE "{col_name}" IS NULL
                    """))
                    null_counts[col_name] = null_result.scalar()
                except:
                    null_counts[col_name] = 'error'
            
            return {
                'samples': samples,
                'null_counts': null_counts
            }
        except Exception as e:
            return {
                'error': str(e),
                'samples': [],
                'null_counts': {}
            }

def identify_table_categories():
    """Categorize tables by their purpose"""
    categories = {
        'users_auth': [],
        'students': [],
        'teachers': [],
        'courses': [],
        'education_structure': [],
        'organizations': [],
        'dictionaries': [],
        'schedules': [],
        'grades': [],
        'attendance': [],
        'backups': [],
        'other': []
    }
    
    with engine.connect() as conn:
        tables_result = conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        
        for row in tables_result:
            table_name = row[0]
            
            # Categorize based on name patterns
            if any(x in table_name for x in ['user', 'account', 'person', 'login', 'auth']):
                categories['users_auth'].append(table_name)
            elif any(x in table_name for x in ['student', 'scholar']):
                categories['students'].append(table_name)
            elif 'teacher' in table_name or 'instructor' in table_name:
                categories['teachers'].append(table_name)
            elif any(x in table_name for x in ['course', 'subject', 'lesson']):
                categories['courses'].append(table_name)
            elif any(x in table_name for x in ['education_', 'academic', 'semester', 'curriculum']):
                categories['education_structure'].append(table_name)
            elif 'organ' in table_name or 'department' in table_name or 'faculty' in table_name:
                categories['organizations'].append(table_name)
            elif 'dictionar' in table_name or '_dic' in table_name:
                categories['dictionaries'].append(table_name)
            elif any(x in table_name for x in ['schedule', 'timetable', 'calendar']):
                categories['schedules'].append(table_name)
            elif any(x in table_name for x in ['grade', 'mark', 'score', 'assessment']):
                categories['grades'].append(table_name)
            elif 'attendance' in table_name or 'present' in table_name:
                categories['attendance'].append(table_name)
            elif any(x in table_name for x in ['_bak', 'backup', '_old', '_temp', '_2']):
                categories['backups'].append(table_name)
            else:
                categories['other'].append(table_name)
    
    return categories

def analyze_relationships():
    """Infer relationships between tables based on column names"""
    relationships = []
    
    with engine.connect() as conn:
        # Get all columns that likely reference other tables
        result = conn.execute(text("""
            SELECT 
                c.table_name,
                c.column_name,
                c.data_type
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            AND (
                c.column_name LIKE '%_id'
                OR c.column_name = 'id'
            )
            ORDER BY c.table_name, c.column_name
        """))
        
        columns_by_table = defaultdict(list)
        for row in result:
            columns_by_table[row[0]].append({
                'column': row[1],
                'type': row[2]
            })
        
        # Infer relationships
        for table, columns in columns_by_table.items():
            for col in columns:
                col_name = col['column']
                
                if col_name == 'id':
                    continue
                
                # Extract referenced table name
                if col_name.endswith('_id'):
                    referenced_table = col_name[:-3]
                    
                    # Pluralize check
                    potential_tables = [
                        referenced_table,
                        referenced_table + 's',
                        referenced_table + 'es',
                        referenced_table[:-1] if referenced_table.endswith('y') else referenced_table
                    ]
                    
                    for potential in potential_tables:
                        if potential in columns_by_table:
                            relationships.append({
                                'from_table': table,
                                'from_column': col_name,
                                'to_table': potential,
                                'to_column': 'id',
                                'confidence': 'high' if potential == referenced_table + 's' else 'medium'
                            })
                            break
    
    return relationships

def analyze_organization_hierarchy():
    """Analyze the organization hierarchy structure"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                id,
                type_id,
                parent_id,
                dictionary_name_id,
                nod_level,
                active
            FROM organizations
            WHERE active = 1
            ORDER BY nod_level, parent_id
            LIMIT 100
        """))
        
        org_structure = []
        for row in result:
            org_structure.append({
                'id': row[0],
                'type_id': row[1],
                'parent_id': row[2],
                'dictionary_name_id': row[3],
                'level': row[4],
                'active': row[5]
            })
        
        # Count by level
        level_counts = conn.execute(text("""
            SELECT nod_level, COUNT(*) as count
            FROM organizations
            WHERE active = 1
            GROUP BY nod_level
            ORDER BY nod_level
        """))
        
        levels = [dict(row._mapping) for row in level_counts]
        
        return {
            'sample_structure': org_structure,
            'level_distribution': levels
        }

def main():
    """Main analysis function"""
    print("=" * 80)
    print("COMPREHENSIVE DATABASE ANALYSIS")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now()}")
    print()
    
    analysis_results = {
        'metadata': {
            'analysis_date': str(datetime.now()),
            'database': 'edu',
            'host': 'localhost:5432'
        }
    }
    
    # 1. Get all tables with counts
    print("\n[1/7] Analyzing all tables and sizes...")
    tables = get_all_tables_with_counts()
    analysis_results['tables_summary'] = {
        'total_count': len(tables),
        'tables': tables
    }
    print(f"   Found {len(tables)} tables")
    
    # 2. Categorize tables
    print("\n[2/7] Categorizing tables by function...")
    categories = identify_table_categories()
    analysis_results['categories'] = categories
    for cat, tables_list in categories.items():
        if tables_list:
            print(f"   {cat}: {len(tables_list)} tables")
    
    # 3. Analyze key tables in detail
    print("\n[3/7] Analyzing key table structures...")
    key_tables = ['users', 'accounts', 'persons', 'students', 'teachers', 
                  'course', 'education_group', 'organizations', 'dictionaries']
    
    detailed_structures = {}
    for table in key_tables:
        print(f"   Analyzing {table}...")
        try:
            structure = get_table_structure(table)
            detailed_structures[table] = structure
        except Exception as e:
            print(f"   Error analyzing {table}: {e}")
            detailed_structures[table] = {'error': str(e)}
    
    analysis_results['detailed_structures'] = detailed_structures
    
    # 4. Analyze data quality
    print("\n[4/7] Analyzing data quality...")
    data_quality = {}
    for table in key_tables:
        print(f"   Checking {table}...")
        try:
            quality = analyze_data_quality(table, sample_size=3)
            data_quality[table] = quality
        except Exception as e:
            data_quality[table] = {'error': str(e)}
    
    analysis_results['data_quality'] = data_quality
    
    # 5. Infer relationships
    print("\n[5/7] Inferring table relationships...")
    relationships = analyze_relationships()
    analysis_results['relationships'] = {
        'total_inferred': len(relationships),
        'relationships': relationships[:100]  # Limit to first 100
    }
    print(f"   Inferred {len(relationships)} relationships")
    
    # 6. Analyze organization hierarchy
    print("\n[6/7] Analyzing organization hierarchy...")
    org_analysis = analyze_organization_hierarchy()
    analysis_results['organization_hierarchy'] = org_analysis
    
    # 7. Generate statistics
    print("\n[7/7] Generating statistics...")
    with engine.connect() as conn:
        stats = {}
        
        # User statistics
        stats['users'] = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        stats['accounts'] = conn.execute(text("SELECT COUNT(*) FROM accounts")).scalar()
        stats['persons'] = conn.execute(text("SELECT COUNT(*) FROM persons")).scalar()
        stats['students'] = conn.execute(text("SELECT COUNT(*) FROM students WHERE active = 1")).scalar()
        stats['teachers'] = conn.execute(text("SELECT COUNT(*) FROM teachers WHERE active = 1")).scalar()
        stats['courses'] = conn.execute(text("SELECT COUNT(*) FROM course WHERE active = 1")).scalar()
        stats['education_groups'] = conn.execute(text("SELECT COUNT(*) FROM education_group WHERE active = 1")).scalar()
        
        analysis_results['statistics'] = stats
        print(f"   Total Users: {stats['users']}")
        print(f"   Total Students: {stats['students']}")
        print(f"   Total Teachers: {stats['teachers']}")
        print(f"   Total Courses: {stats['courses']}")
    
    # Save to JSON file
    print("\n[SAVING] Writing analysis to JSON file...")
    output_file = f'database_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"\n✓ Analysis complete! Results saved to: {output_file}")
    print("=" * 80)
    
    return analysis_results

if __name__ == '__main__':
    results = main()
