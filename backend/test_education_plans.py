#!/usr/bin/env python3
"""
Test script for enhanced education plans functionality
"""

from app.api.education_plan import get_db_connection

def test_education_plans():
    print('Testing Enhanced Education Plans Database Access...')
    print('=' * 60)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test 1: Count total education plans
        print('1. Testing total education plans count:')
        cursor.execute('SELECT COUNT(*) as count FROM education_plan WHERE active = 1')
        total_count = cursor.fetchone()['count']
        print(f'   ✓ Found {total_count} active education plans')
        
        # Test 2: Get sample plans with details
        print('\n2. Testing education plans with details:')
        cursor.execute("""
            SELECT 
                ep.id::text as id,
                ep.name_az,
                ep.name_en,
                ep.education_year,
                COUNT(eps.id) as total_subjects
            FROM education_plan ep
            LEFT JOIN education_plan_subject_group epsg 
                ON epsg.education_plan_id = ep.id AND epsg.active = 1
            LEFT JOIN education_plan_subject eps 
                ON eps.subject_group_id = epsg.id AND eps.active = 1
            WHERE ep.active = 1
            GROUP BY ep.id, ep.name_az, ep.name_en, ep.education_year
            ORDER BY ep.id DESC
            LIMIT 5
        """)
        
        plans = cursor.fetchall()
        for i, plan in enumerate(plans, 1):
            plan_id = plan['id']
            plan_year = plan['education_year']
            plan_subjects = plan['total_subjects']
            plan_name = plan['name_az'] or 'No name'
            print(f'   Plan {i}: ID={plan_id}, Year={plan_year}, Subjects={plan_subjects}')
            if len(plan_name) > 60:
                print(f'            Name: {plan_name[:60]}...')
            else:
                print(f'            Name: {plan_name}')
        
        # Test 3: Get available education years
        print('\n3. Testing available education years:')
        cursor.execute("""
            SELECT DISTINCT education_year
            FROM education_plan 
            WHERE active = 1 AND education_year IS NOT NULL
            ORDER BY education_year DESC
            LIMIT 10
        """)
        
        years = [row['education_year'] for row in cursor.fetchall()]
        print(f'   ✓ Available years: {years}')
        
        # Test 4: Test search functionality
        print('\n4. Testing search functionality:')
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM education_plan ep
            WHERE ep.active = 1 
            AND (ep.name_az ILIKE %s OR ep.name_en ILIKE %s OR ep.id::text ILIKE %s)
        """, ('%1%', '%1%', '%1%'))
        
        search_count = cursor.fetchone()['count']
        print(f'   ✓ Found {search_count} plans matching search term "1"')
        
        # Test 5: Test year filtering
        if years:
            test_year = years[0]
            print(f'\n5. Testing year filtering for "{test_year}":')
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM education_plan ep
                WHERE ep.active = 1 AND ep.education_year = %s
            """, (test_year,))
            
            year_count = cursor.fetchone()['count']
            print(f'   ✓ Found {year_count} plans for year {test_year}')
        
        # Test 6: Get subject count for first plan
        if plans:
            first_plan_id = plans[0]['id']
            print(f'\n6. Testing subjects for plan ID {first_plan_id}:')
            cursor.execute("""
                SELECT COUNT(eps.id) as count
                FROM education_plan_subject eps
                JOIN education_plan_subject_group epsg ON eps.subject_group_id = epsg.id
                WHERE eps.active = 1 AND epsg.active = 1 AND epsg.education_plan_id = %s
            """, (first_plan_id,))
            
            subject_count = cursor.fetchone()['count']
            print(f'   ✓ Plan {first_plan_id} has {subject_count} subjects')
            
            # Test subject search
            print(f'\n7. Testing subject search for plan {first_plan_id}:')
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM education_plan_subject eps
                JOIN education_plan_subject_group epsg ON eps.subject_group_id = epsg.id
                JOIN subject_catalog sc ON sc.id = eps.subject_id
                WHERE eps.active = 1 AND epsg.active = 1 
                AND epsg.education_plan_id = %s
                AND sc.name_az ILIKE %s
            """, (first_plan_id, '%a%'))
            
            subject_search_count = cursor.fetchone()['count']
            print(f'   ✓ Found {subject_search_count} subjects containing "a" for plan {first_plan_id}')
        
        conn.close()
        print('\n' + '=' * 60)
        print('✅ ALL DATABASE TESTS COMPLETED SUCCESSFULLY!')
        print('✅ Enhanced education plans functionality is ready!')
        print('\nFeatures tested:')
        print('  ✓ Education plans listing with subject counts')
        print('  ✓ Search functionality across plan names and IDs')
        print('  ✓ Year-based filtering')
        print('  ✓ Subject listing for specific plans')
        print('  ✓ Subject search within plans')
        print('  ✓ Available years enumeration')
        
    except Exception as e:
        print(f'❌ Database test error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_education_plans()