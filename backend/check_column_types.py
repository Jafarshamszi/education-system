"""
Check the data types of education_plan table columns
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def check_column_types():
    """Check the actual data types of education_plan columns"""
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="edu", 
            user="postgres",
            password="1111",
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        # Check column information
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'education_plan'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("Education Plan Table Column Information:")
        print("=" * 50)
        
        for col in columns:
            print(f"Column: {col['column_name']}")
            print(f"  Type: {col['data_type']}")
            print(f"  Nullable: {col['is_nullable']}")
            print(f"  Default: {col['column_default']}")
            print()
        
        # Test query with proper type casting
        print("Testing query with type conversion:")
        cursor.execute("""
            SELECT 
                id,
                name,
                organization_id,
                education_type_id,
                education_level_id,
                status,
                active,
                create_date
            FROM education_plan 
            WHERE active = 1
            LIMIT 3
        """)
        
        plans = cursor.fetchall()
        print(f"Found {len(plans)} active plans using active = 1")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_column_types()