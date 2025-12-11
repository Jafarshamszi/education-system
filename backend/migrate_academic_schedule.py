#!/usr/bin/env python3
"""
Academic Schedule Data Migration Script
Migrates academic schedule events from old database (edu) to new database (lms)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

# Database connections
OLD_DB = {
    'host': 'localhost',
    'database': 'edu',
    'user': 'postgres',
    'password': '1111'
}

NEW_DB = {
    'host': 'localhost',
    'database': 'lms',
    'user': 'postgres',
    'password': '1111'
}

# Event type mapping from old to new
EVENT_TYPE_MAPPING = {
    110000245: 'academic',  # First day of fall semester
    110000246: 'academic',  # 
    110000247: 'academic',  # 
    110000248: 'academic',  # 
    110000249: 'academic',  # Last day of fall semester
    110000250: 'exam',      # First day of fall exam session
    110000251: 'exam',      # Last day of fall exam session
    110000252: 'exam',      # First day of fall re-exam session
    110000253: 'exam',      # Last day of fall re-exam session
    110000254: 'academic',  # First day of spring semester
    110000255: 'academic',  # 
    110000256: 'academic',  # 
    110000257: 'academic',  # 
    110000258: 'academic',  # Last day of spring semester
    110000259: 'exam',      # First day of spring exam session
    110000260: 'exam',      # Last day of spring exam session
    110000261: 'exam',      # First day of spring re-exam session
    110000262: 'exam',      # Last day of spring re-exam session
}


def parse_date(date_str):
    """Parse date string in DD/MM/YYYY format"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except:
        return None


def get_term_type_from_type_id(type_id):
    """Determine if event is for fall or spring semester"""
    # 110000245-110000253 are fall semester events
    # 110000254-110000262 are spring semester events
    if 110000245 <= type_id <= 110000253:
        return 'fall'
    elif 110000254 <= type_id <= 110000262:
        return 'spring'
    return None


def migrate_academic_schedule():
    """Main migration function"""
    
    old_conn = psycopg2.connect(**OLD_DB, cursor_factory=RealDictCursor)
    new_conn = psycopg2.connect(**NEW_DB, cursor_factory=RealDictCursor)
    
    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()
    
    print("=" * 80)
    print("ACADEMIC SCHEDULE DATA MIGRATION")
    print("=" * 80)
    print()
    
    # Step 1: Get event type names from dictionaries
    print("Step 1: Loading event type dictionary...")
    old_cur.execute("""
        SELECT id, name_az, name_ru, name_en 
        FROM dictionaries 
        WHERE id BETWEEN 110000245 AND 110000270
        ORDER BY id
    """)
    event_types = {row['id']: row for row in old_cur.fetchall()}
    print(f"  ✓ Loaded {len(event_types)} event type definitions")
    print()
    
    # Step 2: Get academic year mapping (old ID to new UUID)
    print("Step 2: Creating academic year mapping...")
    old_cur.execute("""
        SELECT id, name, start_date, end_date, order_by, active
        FROM edu_years
        WHERE active = 1
        ORDER BY order_by DESC
    """)
    old_years = old_cur.fetchall()
    
    year_mapping = {}  # Maps old year ID to new academic_year string
    term_mapping = {}  # Maps (academic_year, term_type) to term UUID
    
    # Get existing terms from new database
    new_cur.execute("""
        SELECT id, academic_year, term_type
        FROM academic_terms
        ORDER BY academic_year DESC, term_type
    """)
    new_terms = new_cur.fetchall()
    
    for term in new_terms:
        key = (term['academic_year'], term['term_type'])
        term_mapping[key] = term['id']
    
    # Map old year IDs to new academic year strings (convert format)
    for old_year in old_years:
        year_name = old_year['name']
        # Convert format: "2022/2023" -> "2022-2023"
        year_name_new_format = year_name.replace('/', '-')
        year_mapping[old_year['id']] = year_name_new_format
    
    print(f"  ✓ Mapped {len(year_mapping)} academic years")
    print(f"  ✓ Found {len(term_mapping)} existing terms in new database")
    print()
    
    # Step 3: Get academic schedule events from old database
    print("Step 3: Loading academic schedule events from old database...")
    old_cur.execute("""
        SELECT 
            asd.id,
            asd.type_id,
            asd.start_date,
            asd.active,
            acs.education_year_id,
            ey.name as education_year_name
        FROM academic_schedule_details asd
        LEFT JOIN academic_schedule acs ON asd.academic_schedule_id = acs.id
        LEFT JOIN edu_years ey ON acs.education_year_id = ey.id
        WHERE asd.active = 1 
        AND acs.education_year_id IS NOT NULL
        ORDER BY ey.order_by DESC, asd.type_id
    """)
    old_events = old_cur.fetchall()
    print(f"  ✓ Found {len(old_events)} active events to migrate")
    print()
    
    # Step 4: Check how many events already exist
    new_cur.execute("SELECT COUNT(*) as count FROM calendar_events")
    existing_count = new_cur.fetchone()['count']
    print(f"Step 4: Current calendar_events count: {existing_count}")
    print()
    
    # Step 5: Migrate events
    print("Step 5: Migrating events...")
    migrated = 0
    skipped = 0
    errors = 0
    
    for event in old_events:
        try:
            type_id = event['type_id']
            education_year_id = event['education_year_id']
            start_date_str = event['start_date']
            
            # Skip if no year mapping
            if education_year_id not in year_mapping:
                skipped += 1
                continue
            
            academic_year = year_mapping[education_year_id]
            term_type = get_term_type_from_type_id(type_id)
            
            # Skip if can't determine term type
            if not term_type:
                skipped += 1
                continue
            
            # Get term UUID
            term_key = (academic_year, term_type)
            if term_key not in term_mapping:
                skipped += 1
                continue
            
            term_uuid = term_mapping[term_key]
            
            # Parse date
            start_datetime = parse_date(start_date_str)
            if not start_datetime:
                skipped += 1
                continue
            
            # Get event type info
            event_info = event_types.get(type_id)
            if not event_info:
                # Use default names for unknown types
                event_info = {
                    'name_az': f'Academic Event {type_id}',
                    'name_ru': f'Академическое событие {type_id}',
                    'name_en': f'Academic Event {type_id}'
                }
            
            # Determine event type category
            event_type = EVENT_TYPE_MAPPING.get(type_id, 'academic')
            
            # Create JSONB title
            title = {
                'az': event_info['name_az'] or f'Event {type_id}',
                'ru': event_info['name_ru'] or f'Event {type_id}',
                'en': event_info['name_en'] or f'Event {type_id}'
            }
            
            # Insert into calendar_events
            new_cur.execute("""
                INSERT INTO calendar_events (
                    academic_term_id,
                    event_type,
                    title,
                    description,
                    start_datetime,
                    end_datetime,
                    is_mandatory,
                    target_audience
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                term_uuid,
                event_type,
                json.dumps(title),
                json.dumps({}),
                start_datetime,
                start_datetime,  # Use same date for end
                True,
                ['all']
            ))
            
            migrated += 1
            
            if migrated % 50 == 0:
                print(f"  ... migrated {migrated} events")
                
        except Exception as e:
            errors += 1
            print(f"  ✗ Error migrating event {event.get('id')}: {e}")
    
    # Commit changes
    new_conn.commit()
    
    print()
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"  Total events in old database: {len(old_events)}")
    print(f"  Successfully migrated:        {migrated}")
    print(f"  Skipped:                      {skipped}")
    print(f"  Errors:                       {errors}")
    print()
    
    # Verify new count
    new_cur.execute("SELECT COUNT(*) as count FROM calendar_events")
    final_count = new_cur.fetchone()['count']
    print(f"  Calendar events before: {existing_count}")
    print(f"  Calendar events after:  {final_count}")
    print(f"  New events added:       {final_count - existing_count}")
    print()
    
    # Show sample of migrated events
    print("Sample of migrated events:")
    new_cur.execute("""
        SELECT 
            ce.title->>'az' as title_az,
            ce.event_type,
            ce.start_datetime,
            at.academic_year,
            at.term_type
        FROM calendar_events ce
        JOIN academic_terms at ON ce.academic_term_id = at.id
        ORDER BY ce.created_at DESC
        LIMIT 5
    """)
    
    for row in new_cur.fetchall():
        print(f"  • {row['academic_year']} {row['term_type']}: {row['title_az']} ({row['event_type']}) - {row['start_datetime']}")
    
    print()
    print("=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    
    # Close connections
    old_cur.close()
    new_cur.close()
    old_conn.close()
    new_conn.close()


if __name__ == "__main__":
    try:
        migrate_academic_schedule()
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
