import psycopg2
from psycopg2.extras import RealDictCursor

def analyze_schedule_tables():
    try:
        conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Key tables to analyze
        tables = [
            'academic_schedule',
            'academic_schedule_details', 
            'course',
            'course_teacher',
            'course_student',
            'dynamic_timetable',
            'dynamic_timetable_details',
            'students',
            'teachers',
            'subject_dic'
        ]
        
        for table_name in tables:
            print(f"\n{'='*60}")
            print(f"TABLE: {table_name}")
            print(f"{'='*60}")
            
            # Get table structure
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print("COLUMNS:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} "
                      f"({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
            # Get sample data
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"\nROW COUNT: {count}")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                samples = cursor.fetchall()
                print(f"\nSAMPLE DATA:")
                for i, sample in enumerate(samples, 1):
                    print(f"  Row {i}: {dict(sample)}")
        
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    analyze_schedule_tables()