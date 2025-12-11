from app.core.database import sync_engine
from sqlalchemy import text
import base64


def check_pin(pin_code):
    conn = sync_engine.connect()
    
    # First, let's check the structure of persons table
    print("📋 Checking persons table structure...")
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'persons' ORDER BY ordinal_position"))
    columns = result.fetchall()
    print("Persons table columns:")
    for col in columns:
        print(f"  - {col[0]}")
    
    print("\n📋 Checking accounts table structure...")
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'accounts' ORDER BY ordinal_position"))
    columns = result.fetchall()
    print("Accounts table columns:")
    for col in columns:
        print(f"  - {col[0]}")
    
    # Check if PIN exists in persons table (just check persons first)
    print(f"\n🔍 Searching for PIN: {pin_code}")
    result = conn.execute(text("SELECT * FROM persons WHERE pincode = :pin_code"), {"pin_code": pin_code})
    
    person = result.fetchone()
    
    print("=" * 50)
    
    if person:
        print("✅ PIN FOUND!")
        print(f"Person data: {person}")
    else:
        print("❌ PIN NOT FOUND!")
        
        # Let's check if there are similar PINs
        print("\n🔍 Checking for similar PINs...")
        result = conn.execute(text("SELECT pincode FROM persons WHERE pincode LIKE :pattern LIMIT 10"), {"pattern": f"%{pin_code[:3]}%"})
        
        similar_pins = result.fetchall()
        if similar_pins:
            print("Similar PINs found:")
            for pin in similar_pins:
                print(f"  - {pin[0]}")
        else:
            print("No similar PINs found")
    
    conn.close()


if __name__ == "__main__":
    check_pin("6abdf0v")