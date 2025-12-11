"""
Student Orders Migration Script
Migrates orders data from old edu database to new lms database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import uuid

# Database connection settings
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


def create_student_orders_tables():
    """Create student_orders tables in the new database"""
    print("Creating student_orders tables in LMS database...")
    
    conn = psycopg2.connect(**NEW_DB)
    cursor = conn.cursor()
    
    try:
        # Create student_orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_orders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_number VARCHAR(100) UNIQUE NOT NULL,
                order_type VARCHAR(50) NOT NULL,
                order_date DATE,
                status VARCHAR(50) DEFAULT 'pending',
                notes TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_student_orders_order_type 
                ON student_orders(order_type);
            CREATE INDEX IF NOT EXISTS idx_student_orders_status 
                ON student_orders(status);
            CREATE INDEX IF NOT EXISTS idx_student_orders_order_date 
                ON student_orders(order_date);
        """)
        
        # Create student_order_assignments table (links students to orders)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_order_assignments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_id UUID NOT NULL REFERENCES student_orders(id) ON DELETE CASCADE,
                student_id UUID REFERENCES students(id) ON DELETE CASCADE,
                person_id BIGINT,
                reason TEXT,
                notes TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_student_order_assignments_order_id 
                ON student_order_assignments(order_id);
            CREATE INDEX IF NOT EXISTS idx_student_order_assignments_student_id 
                ON student_order_assignments(student_id);
            CREATE INDEX IF NOT EXISTS idx_student_order_assignments_person_id 
                ON student_order_assignments(person_id);
        """)
        
        conn.commit()
        print("✓ Student orders tables created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error creating tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_order_type_mapping():
    """Get order type names from old database dictionaries"""
    print("Fetching order type mappings...")
    
    conn = psycopg2.connect(**OLD_DB, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT 
                o.type_id,
                d.name_az,
                d.name_ru,
                d.name_en
            FROM orders o
            LEFT JOIN dictionaries d ON d.id = o.type_id
            WHERE o.active = 1 AND o.type_id IS NOT NULL
            ORDER BY o.type_id
        """)
        
        type_mapping = {}
        for row in cursor.fetchall():
            type_id = row['type_id']
            # Map old type IDs to new type names
            if type_id == 110000035:
                type_name = 'admission'
            elif type_id == 110000036:
                type_name = 'dismissal'
            elif type_id == 110000037:
                type_name = 'other'
            else:
                type_name = 'other'
            
            type_mapping[type_id] = {
                'type_name': type_name,
                'names': {
                    'az': row['name_az'],
                    'ru': row['name_ru'],
                    'en': row['name_en']
                }
            }
        
        print(f"✓ Found {len(type_mapping)} order types")
        return type_mapping
        
    finally:
        cursor.close()
        conn.close()


def get_status_mapping():
    """Get status names from old database"""
    print("Fetching status mappings...")
    
    conn = psycopg2.connect(**OLD_DB, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT 
                o.status,
                d.name_az,
                d.name_ru,
                d.name_en
            FROM orders o
            LEFT JOIN dictionaries d ON d.id = o.status
            WHERE o.active = 1 AND o.status IS NOT NULL
            ORDER BY o.status
        """)
        
        status_mapping = {}
        for row in cursor.fetchall():
            status_id = row['status']
            # Map old status IDs to new status names
            if status_id == 110000058:  # Təsdiq edilib (Approved)
                status_name = 'approved'
            elif status_id == 110000059:  # Gözləmədə (Pending)
                status_name = 'pending'
            elif status_id == 110000060:  # Ləğv edilib (Cancelled)
                status_name = 'cancelled'
            else:
                status_name = 'pending'
            
            status_mapping[status_id] = {
                'status_name': status_name,
                'names': {
                    'az': row['name_az'],
                    'ru': row['name_ru'],
                    'en': row['name_en']
                }
            }
        
        print(f"✓ Found {len(status_mapping)} status types")
        return status_mapping
        
    finally:
        cursor.close()
        conn.close()


def parse_date(date_str):
    """Parse date string in DD/MM/YYYY format"""
    if not date_str or date_str == '':
        return None
    
    try:
        # Try DD/MM/YYYY format
        day, month, year = date_str.split('/')
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        return None


def migrate_orders():
    """Migrate orders from old database to new database"""
    print("\n" + "="*60)
    print("Starting Student Orders Migration")
    print("="*60)
    
    type_mapping = get_order_type_mapping()
    status_mapping = get_status_mapping()
    
    old_conn = psycopg2.connect(**OLD_DB, cursor_factory=RealDictCursor)
    new_conn = psycopg2.connect(**NEW_DB, cursor_factory=RealDictCursor)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Fetch all active orders from old database
        print("\nFetching orders from old database...")
        old_cursor.execute("""
            SELECT 
                id,
                type_id,
                serial,
                order_date,
                status,
                note,
                create_date,
                create_user_id
            FROM orders
            WHERE active = 1
            ORDER BY create_date DESC
        """)
        
        orders = old_cursor.fetchall()
        print(f"Found {len(orders)} active orders to migrate")
        
        # Migrate each order
        print("\nMigrating orders...")
        for order in orders:
            try:
                # Generate new UUID
                new_id = str(uuid.uuid4())
                
                # Get order type
                type_info = type_mapping.get(order['type_id'], {})
                order_type = type_info.get('type_name', 'other')
                
                # Get status
                status_info = status_mapping.get(order['status'], {})
                status = status_info.get('status_name', 'pending')
                
                # Parse order date
                order_date = parse_date(order['order_date'])
                
                # Create metadata with original IDs and multilingual names
                metadata = {
                    'old_id': str(order['id']),
                    'old_type_id': str(order['type_id']),
                    'old_status_id': str(order['status']) if order['status'] else None,
                    'type_names': type_info.get('names', {}),
                    'status_names': status_info.get('names', {}),
                    'create_user_id': str(order['create_user_id']) if order['create_user_id'] else None
                }
                
                # Insert into new database
                new_cursor.execute("""
                    INSERT INTO student_orders 
                    (id, order_number, order_type, order_date, status, notes, metadata, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (order_number) DO NOTHING
                    RETURNING id
                """, (
                    new_id,
                    order['serial'] or f"ORDER-{order['id']}",
                    order_type,
                    order_date,
                    status,
                    order['note'],
                    json.dumps(metadata),
                    order['create_date'],
                    order['create_date']
                ))
                
                result = new_cursor.fetchone()
                if result:
                    migrated_count += 1
                    if migrated_count % 100 == 0:
                        print(f"  Migrated {migrated_count} orders...")
                        new_conn.commit()
                else:
                    skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error migrating order {order['id']}: {e}")
                continue
        
        # Commit remaining changes
        new_conn.commit()
        
        print(f"\n✓ Orders migration completed:")
        print(f"  - Migrated: {migrated_count}")
        print(f"  - Skipped (duplicates): {skipped_count}")
        print(f"  - Errors: {error_count}")
        
    except Exception as e:
        new_conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        old_cursor.close()
        new_cursor.close()
        old_conn.close()
        new_conn.close()


def migrate_person_orders():
    """Migrate person_orders (student-order relationships)"""
    print("\n" + "="*60)
    print("Migrating Student-Order Assignments")
    print("="*60)
    
    old_conn = psycopg2.connect(**OLD_DB, cursor_factory=RealDictCursor)
    new_conn = psycopg2.connect(**NEW_DB, cursor_factory=RealDictCursor)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    migrated_count = 0
    skipped_count = 0
    
    try:
        # Fetch all active person_orders
        print("Fetching student-order relationships...")
        old_cursor.execute("""
            SELECT 
                po.id,
                po.person_id,
                po.order_id,
                po.student_id,
                po.reason_id,
                po.note,
                po.create_date
            FROM person_orders po
            WHERE po.active = 1
            ORDER BY po.create_date DESC
        """)
        
        person_orders = old_cursor.fetchall()
        print(f"Found {len(person_orders)} student-order assignments to migrate")
        
        # Create a mapping of old order IDs to new order UUIDs
        new_cursor.execute("SELECT metadata->>'old_id' as old_id, id FROM student_orders")
        order_mapping = {row['old_id']: row['id'] for row in new_cursor.fetchall()}
        
        print(f"\nMigrating assignments...")
        for po in person_orders:
            try:
                # Find corresponding new order UUID
                old_order_id = str(po['order_id'])
                new_order_id = order_mapping.get(old_order_id)
                
                if not new_order_id:
                    skipped_count += 1
                    continue
                
                # Create metadata
                metadata = {
                    'old_id': str(po['id']),
                    'old_person_id': str(po['person_id']) if po['person_id'] else None,
                    'old_student_id': str(po['student_id']) if po['student_id'] else None,
                    'old_reason_id': str(po['reason_id']) if po['reason_id'] else None
                }
                
                # Insert assignment
                new_cursor.execute("""
                    INSERT INTO student_order_assignments 
                    (order_id, person_id, notes, metadata, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    new_order_id,
                    po['person_id'],
                    po['note'],
                    json.dumps(metadata),
                    po['create_date'],
                    po['create_date']
                ))
                
                migrated_count += 1
                if migrated_count % 500 == 0:
                    print(f"  Migrated {migrated_count} assignments...")
                    new_conn.commit()
                    
            except Exception as e:
                print(f"  ✗ Error migrating assignment {po['id']}: {e}")
                continue
        
        new_conn.commit()
        
        print(f"\n✓ Assignments migration completed:")
        print(f"  - Migrated: {migrated_count}")
        print(f"  - Skipped (no matching order): {skipped_count}")
        
    except Exception as e:
        new_conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        old_cursor.close()
        new_cursor.close()
        old_conn.close()
        new_conn.close()


def verify_migration():
    """Verify the migration results"""
    print("\n" + "="*60)
    print("Verifying Migration")
    print("="*60)
    
    conn = psycopg2.connect(**NEW_DB, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    try:
        # Count orders by type
        cursor.execute("""
            SELECT 
                order_type,
                status,
                COUNT(*) as count
            FROM student_orders
            GROUP BY order_type, status
            ORDER BY order_type, status
        """)
        
        print("\nOrders by type and status:")
        for row in cursor.fetchall():
            print(f"  {row['order_type']:15s} | {row['status']:10s} | {row['count']:4d} orders")
        
        # Total counts
        cursor.execute("SELECT COUNT(*) as total FROM student_orders")
        total_orders = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM student_order_assignments")
        total_assignments = cursor.fetchone()['total']
        
        print(f"\nTotal Summary:")
        print(f"  - Total orders: {total_orders}")
        print(f"  - Total student assignments: {total_assignments}")
        
        # Sample data
        print("\nSample migrated orders:")
        cursor.execute("""
            SELECT 
                order_number,
                order_type,
                order_date,
                status,
                metadata->>'type_names' as type_names
            FROM student_orders
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            print(f"  - {row['order_number']:15s} | {row['order_type']:10s} | {row['order_date']} | {row['status']}")
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("STUDENT ORDERS MIGRATION SCRIPT")
        print("="*60)
        print("\nThis script will:")
        print("1. Create student_orders tables in LMS database")
        print("2. Migrate 629 orders from EDU database")
        print("3. Migrate 3,628 student-order assignments")
        print("4. Verify the migration")
        
        input("\nPress Enter to continue or Ctrl+C to cancel...")
        
        # Step 1: Create tables
        create_student_orders_tables()
        
        # Step 2: Migrate orders
        migrate_orders()
        
        # Step 3: Migrate person_orders
        migrate_person_orders()
        
        # Step 4: Verify
        verify_migration()
        
        print("\n" + "="*60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
    except Exception as e:
        print(f"\n\nMigration failed with error: {e}")
        raise
