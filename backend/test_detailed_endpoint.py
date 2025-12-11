#!/usr/bin/env python3
import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def test_detailed_request_endpoint():
    """Test the detailed request endpoint functionality directly"""
    try:
        print("Testing detailed request endpoint logic...")
        
        from app.core.database import get_db
        from sqlalchemy import text
        from fastapi import HTTPException
        
        # Test the orders detailed query
        db = next(get_db())
        request_id = 231214475206889009  # The ID we know exists
        
        print(f"Testing orders detailed query for ID: {request_id}")
        
        result = db.execute(text("""
            SELECT o.id, o.type_id, o.serial, o.order_date, o.status,
                   o.create_date, o.note, o.form_id, o.edu_level_id,
                   po.person_id, po.student_id, po.reason_id, po.note as person_note,
                   p.firstname, p.lastname, p.pincode, p.birthdate,
                   dt.name_az as type_name, st.name_az as status_name
            FROM orders o
            LEFT JOIN person_orders po ON o.id = po.order_id AND po.active = 1
            LEFT JOIN persons p ON po.person_id = p.id
            LEFT JOIN dictionaries dt ON o.type_id = dt.id
            LEFT JOIN dictionaries st ON o.status = st.id
            WHERE o.id = :request_id AND o.active = 1
        """), {"request_id": request_id})

        order = result.fetchone()
        if not order:
            print("❌ Order not found")
            return False

        # Build the response
        response = {
            "id": order[0],
            "type_id": order[1],
            "serial": order[2],
            "order_date": order[3],
            "status": order[4],
            "create_date": order[5],
            "note": order[6],
            "form_id": order[7],
            "edu_level_id": order[8],
            "person": {
                "id": order[9],
                "student_id": order[10],
                "reason_id": order[11],
                "note": order[12],
                "firstname": order[13],
                "lastname": order[14],
                "pincode": order[15],
                "birthdate": order[16],
                "full_name": f"{order[13] or ''} {order[14] or ''}".strip() if order[13] or order[14] else None
            } if order[9] else None,
            "type_name": order[17],
            "status_name": order[18]
        }
        
        print("✅ Query executed successfully!")
        print("Response data:")
        import json
        print(json.dumps(response, indent=2, default=str))
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error in detailed request test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_detailed_request_endpoint()