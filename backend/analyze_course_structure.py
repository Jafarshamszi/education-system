import psycopg2
from psycopg2.extras import RealDictCursor

def analyze_course_structure():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='edu',
            user='postgres',
            password='1111'
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== COURSE TABLE STRUCTURE ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'course'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"- {col['column_name']}: {col['data_type']} ({nullable}){default}")
        
        print("\n=== SAMPLE COURSE RECORD ===")
        cursor.execute("SELECT * FROM course WHERE active = 1 LIMIT 1")
        course = cursor.fetchone()
        
        if course:
            for key, value in course.items():
                print(f"{key}: {value}")
        
        print("\n=== FOREIGN KEY CONSTRAINTS ===")
        cursor.execute("""
            SELECT
                tc.constraint_name, 
                tc.table_name, 
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
                AND tc.table_name='course';
        """)
        
        fks = cursor.fetchall()
        for fk in fks:
            print(f"- {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        print("\n=== AVAILABLE TEACHERS ===")
        cursor.execute("""
            SELECT t.id, p.firstname, p.lastname, orgn.name_az as org_name
            FROM teachers t
            JOIN persons p ON p.id = t.person_id
            LEFT JOIN organisations org ON org.id = t.organization_id
            LEFT JOIN org_names orgn ON orgn.id = org.org_name_id
            WHERE t.active = 1
            LIMIT 5
        """)
        
        teachers = cursor.fetchall()
        for teacher in teachers:
            print(f"- ID: {teacher['id']}, Name: {teacher['firstname']} {teacher['lastname']}, Org: {teacher['org_name']}")
        
        print("\n=== AVAILABLE STUDENTS ===")
        cursor.execute("""
            SELECT s.id, p.firstname, p.lastname
            FROM students s
            JOIN persons p ON p.id = s.person_id
            WHERE s.active = 1
            LIMIT 5
        """)
        
        students = cursor.fetchall()
        for student in students:
            print(f"- ID: {student['id']}, Name: {student['firstname']} {student['lastname']}")
        
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    analyze_course_structure()