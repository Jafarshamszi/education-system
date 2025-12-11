#!/usr/bin/env python3
"""
Detailed analysis of organization-dictionary relationships to understand
why organization names aren't resolving properly.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host="localhost",
        database="edu",
        user="postgres",
        password="1111",
        cursor_factory=RealDictCursor
    )

def analyze_organization_dictionary_structure():
    """Analyze the relationship between organizations and dictionaries"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=== ORGANIZATION-DICTIONARY ANALYSIS ===\n")
    
    # Get sample organizations
    print("1. Sample Organizations:")
    cursor.execute("""
        SELECT id, name, dictionary_name_id, is_active, organization_type
        FROM organizations 
        WHERE is_active = true 
        ORDER BY id 
        LIMIT 10
    """)
    orgs = cursor.fetchall()
    
    for org in orgs:
        print(f"  • Org ID: {org['id']}")
        print(f"    Name: {org['name']}")
        print(f"    Dictionary Name ID: {org['dictionary_name_id']}")
        print(f"    Type: {org['organization_type']}")
        print(f"    Active: {org['is_active']}")
        print()
    
    # Check dictionaries table structure
    print("\n2. Dictionary Table Structure:")
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'dictionaries' ORDER BY ordinal_position")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  • {col['column_name']}: {col['data_type']}")
    
    # Get sample dictionaries
    print("\n3. Sample Dictionaries:")
    cursor.execute("""
        SELECT id, name, description, dictionary_type, is_active 
        FROM dictionaries 
        WHERE is_active = true 
        ORDER BY id 
        LIMIT 10
    """)
    dicts = cursor.fetchall()
    
    for d in dicts:
        print(f"  • Dict ID: {d['id']}")
        print(f"    Name: {d['name']}")
        print(f"    Description: {d['description']}")
        print(f"    Type: {d['dictionary_type']}")
        print(f"    Active: {d['is_active']}")
        print()
    
    # Try to match organization dictionary_name_ids with dictionary ids
    print("\n4. Trying to Match Organization Dictionary IDs:")
    for org in orgs[:5]:  # Check first 5 organizations
        if org['dictionary_name_id']:
            cursor.execute("""
                SELECT id, name, description, dictionary_type 
                FROM dictionaries 
                WHERE id = %s
            """, (org['dictionary_name_id'],))
            dict_match = cursor.fetchone()
            
            print(f"  • Organization {org['id']} (dictionary_name_id: {org['dictionary_name_id']})")
            if dict_match:
                print(f"    → Found dictionary: {dict_match['name']} ({dict_match['description']})")
            else:
                print(f"    → NO DICTIONARY FOUND for ID {org['dictionary_name_id']}")
            print()
    
    # Check if there are organization types in dictionaries
    print("\n5. Searching for Organization-related Dictionaries:")
    cursor.execute("""
        SELECT id, name, description, dictionary_type 
        FROM dictionaries 
        WHERE dictionary_type ILIKE '%org%' 
           OR name ILIKE '%kafedra%'
           OR name ILIKE '%fakultet%' 
           OR name ILIKE '%bölmə%'
           OR name ILIKE '%department%'
           OR description ILIKE '%org%'
        ORDER BY name
    """)
    org_dicts = cursor.fetchall()
    
    print(f"Found {len(org_dicts)} organization-related dictionaries:")
    for d in org_dicts:
        print(f"  • {d['name']} (ID: {d['id']}, Type: {d['dictionary_type']})")
        print(f"    Description: {d['description']}")
        print()
    
    # Check what organization types exist
    print("\n6. Organization Types in Database:")
    cursor.execute("""
        SELECT organization_type, COUNT(*) as count
        FROM organizations 
        WHERE is_active = true 
        GROUP BY organization_type 
        ORDER BY count DESC
    """)
    org_types = cursor.fetchall()
    
    for ot in org_types:
        print(f"  • {ot['organization_type']}: {ot['count']} organizations")
    
    # Check if organization names are stored directly
    print("\n7. Organizations with Direct Names (not using dictionary):")
    cursor.execute("""
        SELECT id, name, organization_type, dictionary_name_id
        FROM organizations 
        WHERE is_active = true 
          AND name IS NOT NULL 
          AND name != ''
        ORDER BY name
        LIMIT 15
    """)
    named_orgs = cursor.fetchall()
    
    for org in named_orgs:
        print(f"  • {org['name']} (ID: {org['id']}, Type: {org['organization_type']})")
        print(f"    Dictionary ID: {org['dictionary_name_id']}")
        print()
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        analyze_organization_dictionary_structure()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()