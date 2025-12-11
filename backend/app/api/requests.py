from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ..core.database import get_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class SampleRequest(BaseModel):
    id: str  # String to preserve large integer precision in JavaScript
    table_name: str
    description: str
    person_name: Optional[str] = None
    created_date: Optional[datetime] = None
    status: Optional[str] = None

class RequestStats(BaseModel):
    total: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    reserved: int = 0
    taken: int = 0
    returned: int = 0

class RequestType(BaseModel):
    id: str
    name: str
    description: str
    category: str
    table_name: str
    total_count: int
    recent_count: int = 0
    stats: Optional[RequestStats] = None
    sample_requests: Optional[List[SampleRequest]] = None

class RequestSummary(BaseModel):
    categories: List[dict]
    total_requests: int
    total_categories: int

def get_sample_requests(db: Session, table_name: str, limit: int = 3) -> List[SampleRequest]:
    """Get sample requests from a specific table"""
    try:
        if table_name == "orders":
            result = db.execute(text(f"""
                SELECT o.id, o.serial, o.order_date 
                FROM {table_name} o 
                WHERE o.active = 1 
                ORDER BY o.order_date DESC 
                LIMIT {limit}
            """))
        elif table_name == "resource_request":
            result = db.execute(text(f"""
                SELECT rr.id, rr.reservation_date
                FROM {table_name} rr 
                WHERE rr.active = 1 
                ORDER BY rr.reservation_date DESC 
                LIMIT {limit}
            """))
        elif table_name == "teacher_request":
            result = db.execute(text(f"""
                SELECT tr.id, tr.request_date
                FROM {table_name} tr 
                WHERE tr.active = 1 
                ORDER BY tr.request_date DESC 
                LIMIT {limit}
            """))
        else:
            result = db.execute(text(f"""
                SELECT id FROM {table_name} 
                WHERE active = 1 
                ORDER BY id DESC 
                LIMIT {limit}
            """))

        requests = []
        for row in result:
            requests.append(SampleRequest(
                id=row[0],
                table_name=table_name,
                description=f"Request from {table_name}",
                created_date=row[1] if len(row) > 1 else None
            ))
        
        return requests
    except Exception as e:
        logger.error(f"Error getting sample requests from {table_name}: {e}")
        return []

@router.get("/summary", response_model=RequestSummary)
def get_requests_summary(db: Session = Depends(get_db)):
    """
    Get a comprehensive summary of all request types and categories
    Uses new database structure with transcript_requests table
    """
    try:
        categories = []
        total_requests = 0

        # 1. Document Services - Transcript Requests
        document_services = []
        document_total = 0

        try:
            result = db.execute(text("""
                SELECT COUNT(*) FROM transcript_requests
            """))
            transcript_count = result.scalar() or 0
            
            if transcript_count > 0:
                # Get status breakdown
                status_result = db.execute(text("""
                    SELECT status, COUNT(*) as count
                    FROM transcript_requests
                    GROUP BY status
                """))
                status_counts = {row[0]: row[1] for row in status_result}
                
                document_services.append({
                    "id": "transcript_requests",
                    "name": "Transcript Requests",
                    "description": "Official and unofficial transcript requests",
                    "category": "document_services",
                    "table_name": "transcript_requests",
                    "total_count": transcript_count,
                    "recent_count": transcript_count,
                    "stats": {
                        "pending": status_counts.get('pending', 0),
                        "processing": status_counts.get('processing', 0),
                        "approved": status_counts.get('approved', 0),
                        "completed": status_counts.get('completed', 0),
                        "rejected": status_counts.get('rejected', 0),
                        "cancelled": status_counts.get('cancelled', 0)
                    }
                })
                document_total += transcript_count
        except Exception as e:
            logger.error(f"Error counting transcript requests: {e}")

        if document_services:
            categories.append({
                "id": "document_services",
                "name": "Document Services",
                "description": "Academic transcripts and official documents",
                "icon": "FileText",
                "requests": document_services,
                "total_count": document_total
            })
            total_requests += document_total

        # Note: Old database tables (orders, resource_request, teacher_request)
        # are not migrated yet. This endpoint will show empty categories until
        # migration is complete or new request types are added to the new system.

        # Commit the read transaction to avoid ROLLBACK warning
        db.commit()

        return RequestSummary(
            categories=categories,
            total_requests=total_requests,
            total_categories=len(categories)
        )

    except Exception as e:
        logger.error(f"Error in get_requests_summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch requests summary: {str(e)}"
        )

@router.get("/category/{category_id}")
def get_requests_by_category(
    category_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=500)
):
    """Get detailed information about requests in a specific category"""
    try:
        if category_id == "academic_documents":
            # Include person information in the category listing
            result = db.execute(text("""
                SELECT DISTINCT o.id, o.serial, o.order_date, o.status,
                       dt.name_az as type_name, st.name_az as status_name,
                       p.firstname, p.lastname, p.patronymic, p.pincode, p.birthdate,
                       COALESCE(gt.name_en, '') as gender_name,
                       COALESCE(ct.name_en, '') as citizenship_name,
                       COALESCE(nt.name_en, '') as nationality_name,
                       COALESCE(et.name_en, '') as education_type_name,
                       s.score
                FROM orders o
                LEFT JOIN person_orders po ON o.id = po.order_id AND po.active = 1
                LEFT JOIN persons p ON po.person_id = p.id
                LEFT JOIN students s ON po.student_id = s.id
                LEFT JOIN dictionaries dt ON o.type_id = dt.id
                LEFT JOIN dictionaries st ON o.status = st.id
                LEFT JOIN dictionaries gt ON p.gender_id = gt.id
                LEFT JOIN dictionaries ct ON p.citizenship_id = ct.id
                LEFT JOIN dictionaries nt ON p.nationality_id = nt.id
                LEFT JOIN dictionaries et ON s.education_type_id = et.id
                WHERE o.active = 1
                AND o.id IS NOT NULL
                ORDER BY o.order_date DESC
                LIMIT :limit
            """), {"limit": limit})

            orders = []
            for row in result:
                # Include comprehensive person information
                orders.append({
                    "id": str(row[0]),  # Convert to string to preserve precision
                    "serial": row[1], 
                    "order_date": row[2],
                    "status": row[3],
                    "type_name": row[4],
                    "status_name": row[5],
                    "firstname": row[6],
                    "lastname": row[7],
                    "patronymic": row[8],
                    "pincode": row[9],
                    "birthdate": row[10],
                    "gender_name": row[11],
                    "citizenship_name": row[12],
                    "nationality_name": row[13],
                    "education_type_name": row[14],
                    "score": row[15]
                })

            return {
                "category": "academic_documents",
                "name": "Academic Documents",
                "total_count": len(orders),
                "requests": orders
            }

        elif category_id == "student_services":
            # Get resource requests with person information
            result = db.execute(text("""
                SELECT rr.id, rr.reservation_date, rr.status, rr.person_id,
                       p.firstname, p.lastname, p.patronymic
                FROM resource_request rr
                LEFT JOIN persons p ON rr.person_id = p.id
                WHERE rr.active = 1
                ORDER BY rr.reservation_date DESC
                LIMIT :limit
            """), {"limit": limit // 2})

            requests = []
            for row in result:
                requests.append({
                    "id": str(row[0]),  # Convert to string
                    "type": "resource_request",
                    "reservation_date": row[1],
                    "status": row[2],
                    "firstname": row[4],
                    "lastname": row[5],
                    "patronymic": row[6]
                })

            # Get teacher requests with person information via user->account->person
            result = db.execute(text("""
                SELECT tr.id, tr.create_date, tr.status, tr.create_user_id,
                       p.firstname, p.lastname, p.patronymic
                FROM teacher_request tr
                LEFT JOIN users u ON tr.create_user_id = u.id
                LEFT JOIN accounts a ON u.account_id = a.id
                LEFT JOIN persons p ON a.person_id = p.id
                WHERE tr.active = 1
                ORDER BY tr.create_date DESC
                LIMIT :limit
            """), {"limit": limit // 2})

            for row in result:
                requests.append({
                    "id": str(row[0]),  # Convert to string
                    "type": "teacher_request",
                    "request_date": row[1],
                    "status": row[2],
                    "firstname": row[4],
                    "lastname": row[5],
                    "patronymic": row[6]
                })

            return {
                "category": "student_services",
                "name": "Student Services",
                "total_count": len(requests),
                "requests": requests
            }

        elif category_id == "document_services":
            requests = []

            # Get transcript requests with student and person information
            result = db.execute(text("""
                SELECT
                    tr.id,
                    tr.requested_date,
                    tr.student_id,
                    tr.request_type,
                    tr.delivery_method,
                    tr.status,
                    tr.purpose,
                    tr.copies_requested,
                    tr.fee_amount,
                    tr.payment_status,
                    p.first_name,
                    p.last_name,
                    p.middle_name,
                    s.student_number
                FROM transcript_requests tr
                LEFT JOIN students s ON tr.student_id = s.id
                LEFT JOIN users u ON s.user_id = u.id
                LEFT JOIN persons p ON u.id = p.user_id
                ORDER BY tr.requested_date DESC
                LIMIT :limit
            """), {"limit": limit})

            for row in result:
                requests.append({
                    "id": str(row[0]),  # Convert UUID to string
                    "type": "transcript_request",
                    "request_date": row[1].isoformat() if row[1] else None,
                    "student_id": str(row[2]) if row[2] else None,
                    "request_type": row[3],
                    "delivery_method": row[4],
                    "status": row[5],
                    "purpose": row[6],
                    "copies_requested": row[7],
                    "fee_amount": float(row[8]) if row[8] else 0,
                    "payment_status": row[9],
                    "firstname": row[10],
                    "lastname": row[11],
                    "patronymic": row[12],
                    "student_number": row[13],
                    "status_name": row[5].title() if row[5] else "Unknown"
                })

            return {
                "category": "document_services",
                "name": "Document Services",
                "total_count": len(requests),
                "requests": requests
            }

        else:
            raise HTTPException(status_code=404, detail="Category not found")

    except Exception as e:
        logger.error(f"Database error in get_requests_by_category: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/type/{request_type}")
def get_requests_by_type(
    request_type: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0)
):
    """Get detailed information about a specific request type"""
    try:
        if request_type == "resource_request":
            result = db.execute(text("""
                SELECT rr.id, rr.resource_edition_id, rr.reservation_date, rr.status,
                       rr.person_id, rr.take_date, rr.return_date, rr.request_code,
                       p.firstname, p.lastname, p.pincode
                FROM resource_request rr
                LEFT JOIN persons p ON rr.person_id = p.id
                WHERE rr.active = 1
                ORDER BY rr.reservation_date DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            requests = []
            for row in result:
                requests.append({
                    "id": row[0],
                    "resource_edition_id": row[1],
                    "reservation_date": row[2],
                    "status": row[3],
                    "person_id": row[4],
                    "take_date": row[5],
                    "return_date": row[6],
                    "request_code": row[7],
                    "person_name": f"{row[8] or ''} {row[9] or ''}".strip() if row[8] or row[9] else None,
                    "person_pincode": row[10]
                })

            return {
                "request_type": request_type,
                "name": "Library & Resource Requests",
                "total_count": len(requests),
                "requests": requests
            }

        elif request_type == "teacher_request":
            result = db.execute(text("""
                SELECT tr.id, tr.course_id, tr.meeting_id, tr.evaluation_id, tr.status,
                       tr.reason, tr.access_date, tr.create_date
                FROM teacher_request tr
                WHERE tr.active = 1
                ORDER BY tr.create_date DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            requests = []
            for row in result:
                requests.append({
                    "id": row[0],
                    "course_id": row[1],
                    "meeting_id": row[2],
                    "evaluation_id": row[3],
                    "status": row[4],
                    "reason": row[5],
                    "access_date": row[6],
                    "create_date": row[7]
                })

            return {
                "request_type": request_type,
                "name": "Teacher Evaluation Requests",
                "total_count": len(requests),
                "requests": requests
            }

        elif request_type == "orders":
            result = db.execute(text("""
                SELECT o.id, o.type_id, o.serial, o.order_date, o.status,
                       o.create_date, o.note,
                       po.person_id, po.student_id, po.reason_id,
                       p.firstname, p.lastname, p.pincode
                FROM orders o
                LEFT JOIN person_orders po ON o.id = po.order_id AND po.active = 1
                LEFT JOIN persons p ON po.person_id = p.id
                WHERE o.active = 1
                ORDER BY o.order_date DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            requests = []
            for row in result:
                requests.append({
                    "id": row[0],
                    "type_id": row[1],
                    "serial": row[2],
                    "order_date": row[3],
                    "status": row[4],
                    "create_date": row[5],
                    "note": row[6],
                    "person_id": row[7],
                    "student_id": row[8],
                    "reason_id": row[9],
                    "person_name": f"{row[10] or ''} {row[11] or ''}".strip() if row[10] or row[11] else None,
                    "person_pincode": row[12]
                })

            return {
                "request_type": request_type,
                "name": "Academic Orders",
                "total_count": len(requests),
                "requests": requests
            }

        elif request_type == "student_transcript":
            result = db.execute(text("""
                SELECT st.id, st.student_id, st.course_id, st.subject_name,
                       st.credit, st.end_point, st.semester, st.eps_education_year,
                       st.create_date
                FROM student_transcript st
                WHERE st.active = 1
                ORDER BY st.create_date DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            requests = []
            for row in result:
                requests.append({
                    "id": row[0],
                    "student_id": row[1],
                    "course_id": row[2],
                    "subject_name": row[3],
                    "credit": row[4],
                    "end_point": row[5],
                    "semester": row[6],
                    "education_year": row[7],
                    "create_date": row[8]
                })

            return {
                "request_type": request_type,
                "name": "Student Transcripts",
                "total_count": len(requests),
                "requests": requests
            }

        elif request_type == "documents":
            result = db.execute(text("""
                SELECT d.id, d.type_id, d.serial, d.num, d.start_date,
                       d.end_date, d.issuing_organization, d.create_date
                FROM documents d
                WHERE d.active = 1
                ORDER BY d.create_date DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            requests = []
            for row in result:
                requests.append({
                    "id": row[0],
                    "type_id": row[1],
                    "serial": row[2],
                    "num": row[3],
                    "start_date": row[4],
                    "end_date": row[5],
                    "issuing_organization": row[6],
                    "create_date": row[7]
                })

            return {
                "request_type": request_type,
                "name": "Official Documents",
                "total_count": len(requests),
                "requests": requests
            }

        else:
            raise HTTPException(status_code=404, detail="Request type not found")

    except Exception as e:
        logger.error(f"Database error in get_requests_by_type: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/detailed/{request_type}/{request_id}")
def get_request_detail(
    request_type: str,
    request_id: str,  # Changed to str to support both int and UUID
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific request"""
    try:
        if request_type == "transcript_request":
            # Use the new CRUD endpoint for transcript requests
            return get_transcript_request(request_id, db)

        elif request_type == "orders":
            result = db.execute(text("""
                SELECT o.id, o.type_id, o.serial, o.order_date, o.status,
                       o.create_date, o.note, o.form_id, o.edu_level_id,
                       po.person_id, po.student_id, po.reason_id, po.note as person_note,
                       p.firstname, p.lastname, p.patronymic, p.pincode, p.birthdate,
                       p.gender_id, p.citizenship_id, p.nationality_id,
                       s.card_number, s.education_type_id, s.education_payment_type_id, s.score, s.yearly_payment,
                       COALESCE(dt.name_en, 'Unknown Type') as type_name,
                       COALESCE(st.name_en, 'Unknown Status') as status_name,
                       COALESCE(gt.name_en, '') as gender_name,
                       COALESCE(ct.name_en, '') as citizenship_name,
                       COALESCE(nt.name_en, '') as nationality_name,
                       COALESCE(et.name_en, '') as education_type_name,
                       COALESCE(pt.name_en, '') as education_payment_type_name,
                       COALESCE(ft.name_en, '') as form_name,
                       COALESCE(lt.name_en, '') as edu_level_name
                FROM orders o
                LEFT JOIN person_orders po ON o.id = po.order_id AND po.active = 1
                LEFT JOIN persons p ON po.person_id = p.id
                LEFT JOIN students s ON po.student_id = s.id
                LEFT JOIN dictionaries dt ON o.type_id = dt.id
                LEFT JOIN dictionaries st ON o.status = st.id
                LEFT JOIN dictionaries gt ON p.gender_id = gt.id
                LEFT JOIN dictionaries ct ON p.citizenship_id = ct.id
                LEFT JOIN dictionaries nt ON p.nationality_id = nt.id
                LEFT JOIN dictionaries et ON s.education_type_id = et.id
                LEFT JOIN dictionaries pt ON s.education_payment_type_id = pt.id
                LEFT JOIN dictionaries ft ON o.form_id = ft.id
                LEFT JOIN dictionaries lt ON o.edu_level_id = lt.id
                WHERE o.id = :request_id AND o.active = 1
            """), {"request_id": request_id})

            order = result.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            return {
                "id": str(order[0]),  # Convert to string to preserve precision in JavaScript
                "type_id": order[1],
                "serial": order[2],
                "order_date": order[3],
                "status": order[4],
                "create_date": order[5],
                "note": order[6],
                "form_id": order[7],
                "edu_level_id": order[8],
                "person_id": str(order[9]) if order[9] else None,
                "student_id": str(order[10]) if order[10] else None,
                "reason_id": order[11],
                "person_note": order[12],
                "firstname": order[13],
                "lastname": order[14],
                "patronymic": order[15],
                "pincode": order[16],
                "birthdate": order[17],
                "gender_id": order[18],
                "citizenship_id": order[19],
                "nationality_id": order[20],
                "card_number": order[21],
                "education_type_id": order[22],
                "education_payment_type_id": order[23],
                "score": order[24],
                "yearly_payment": order[25],
                "type_name": order[26],
                "status_name": order[27],
                "gender_name": order[28],
                "citizenship_name": order[29],
                "nationality_name": order[30],
                "education_type_name": order[31],
                "education_payment_type_name": order[32],
                "form_name": order[33],
                "edu_level_name": order[34]
            }

        elif request_type == "teacher_request":
            result = db.execute(text("""
                SELECT tr.id, tr.course_id, tr.meeting_id, tr.evaluation_id,
                       tr.status, tr.reason, tr.access_date, tr.create_date,
                       st.name_az as status_name
                FROM teacher_request tr
                LEFT JOIN dictionaries st ON tr.status = st.id
                WHERE tr.id = :request_id AND tr.active = 1
            """), {"request_id": request_id})

            request = result.fetchone()
            if not request:
                raise HTTPException(status_code=404, detail="Teacher request not found")

            return {
                "id": str(request[0]),  # Convert to string for precision
                "course_id": request[1],
                "meeting_id": request[2],
                "evaluation_id": request[3],
                "status": request[4],
                "reason": request[5],
                "access_date": request[6],
                "create_date": request[7],
                "status_name": request[8]
            }

        elif request_type == "resource_request":
            result = db.execute(text("""
                SELECT rr.id, rr.resource_edition_id, rr.user_id, rr.person_id,
                       rr.reservation_date, rr.take_date, rr.finish_date, rr.return_date,
                       rr.request_code, rr.status, rr.penalty_price, rr.paid_penalty_price,
                       rr.penalty_reason, rr.note, rr.penalty_note, rr.create_date,
                       p.firstname, p.lastname, p.pincode,
                       st.name_az as status_name
                FROM resource_request rr
                LEFT JOIN persons p ON rr.person_id = p.id
                LEFT JOIN dictionaries st ON rr.status = st.id
                WHERE rr.id = :request_id AND rr.active = 1
            """), {"request_id": request_id})

            request = result.fetchone()
            if not request:
                raise HTTPException(status_code=404, detail="Resource request not found")

            return {
                "id": str(request[0]),  # Convert to string for precision
                "resource_edition_id": request[1],
                "user_id": request[2],
                "person_id": request[3],
                "reservation_date": request[4],
                "take_date": request[5],
                "finish_date": request[6],
                "return_date": request[7],
                "request_code": request[8],
                "status": request[9],
                "penalty_price": request[10],
                "paid_penalty_price": request[11],
                "penalty_reason": request[12],
                "note": request[13],
                "penalty_note": request[14],
                "create_date": request[15],
                "person": {
                    "firstname": request[16],
                    "lastname": request[17],
                    "pincode": request[18],
                    "full_name": f"{request[16] or ''} {request[17] or ''}".strip() if request[16] or request[17] else None
                } if request[16] or request[17] else None,
                "status_name": request[19]
            }

        elif request_type == "student_transcript":
            result = db.execute(text("""
                SELECT st.id, st.student_id, st.course_id, st.education_group_id,
                       st.fullname, st.faculty_name, st.speciality_name,
                       st.subject_name, st.credit, st.end_point, st.before_point,
                       st.exam_point, st.semester, st.eps_education_year,
                       st.type, st.create_date
                FROM student_transcript st
                WHERE st.id = :request_id AND st.active = 1
            """), {"request_id": request_id})

            transcript = result.fetchone()
            if not transcript:
                raise HTTPException(status_code=404, detail="Student transcript not found")

            return {
                "id": str(transcript[0]),  # Convert to string for precision
                "student_id": transcript[1],
                "course_id": transcript[2],
                "education_group_id": transcript[3],
                "fullname": transcript[4],
                "faculty_name": transcript[5],
                "speciality_name": transcript[6],
                "subject_name": transcript[7],
                "credit": transcript[8],
                "end_point": transcript[9],
                "before_point": transcript[10],
                "exam_point": transcript[11],
                "semester": transcript[12],
                "education_year": transcript[13],
                "type": transcript[14],
                "create_date": transcript[15]
            }

        elif request_type == "documents":
            result = db.execute(text("""
                SELECT d.id, d.type_id, d.serial, d.num, d.start_date,
                       d.end_date, d.file_id, d.issuing_organization, d.create_date,
                       dt.name_az as type_name
                FROM documents d
                LEFT JOIN dictionaries dt ON d.type_id = dt.id
                WHERE d.id = :request_id AND d.active = 1
            """), {"request_id": request_id})

            document = result.fetchone()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            return {
                "id": str(document[0]),  # Convert to string for precision
                "type_id": document[1],
                "serial": document[2],
                "num": document[3],
                "start_date": document[4],
                "end_date": document[5],
                "file_id": document[6],
                "issuing_organization": document[7],
                "create_date": document[8],
                "type_name": document[9]
            }

        else:
            raise HTTPException(status_code=404, detail="Request type not found")

    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without modification
        raise
    except Exception as e:
        logger.error(f"Database error in get_request_detail: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/stats/{request_type}")
def get_request_stats(
    request_type: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific request type"""
    try:
        if request_type == "orders":
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN o.status = 110000058 THEN 1 END) as approved,
                    COUNT(CASE WHEN o.status = 110000057 THEN 1 END) as pending,
                    COUNT(CASE WHEN o.status = 110000059 THEN 1 END) as rejected
                FROM orders o
                WHERE o.active = 1
            """))
            
        elif request_type == "teacher_request":
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN tr.status = 100000199 THEN 1 END) as approved,
                    COUNT(CASE WHEN tr.status = 100000198 THEN 1 END) as pending,
                    COUNT(CASE WHEN tr.status = 100000197 THEN 1 END) as rejected
                FROM teacher_request tr
                WHERE tr.active = 1
            """))
            
        elif request_type == "resource_request":
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN rr.status = 110000376 THEN 1 END) as reserved,
                    COUNT(CASE WHEN rr.status = 110000377 THEN 1 END) as taken,
                    COUNT(CASE WHEN rr.status = 110000378 THEN 1 END) as returned,
                    COUNT(CASE WHEN rr.status = 110000382 THEN 1 END) as cancelled
                FROM resource_request rr
                WHERE rr.active = 1
            """))
            
        else:
            result = db.execute(text(f"""
                SELECT COUNT(*) as total
                FROM {request_type}
                WHERE active = 1
            """))

        stats = result.fetchone()
        
        if request_type == "resource_request":
            return {
                "request_type": request_type,
                "total": stats[0],
                "reserved": stats[1],
                "taken": stats[2],
                "returned": stats[3],
                "cancelled": stats[4]
            }
        elif request_type in ["orders", "teacher_request"]:
            return {
                "request_type": request_type,
                "total": stats[0],
                "approved": stats[1],
                "pending": stats[2],
                "rejected": stats[3]
            }
        else:
            return {
                "request_type": request_type,
                "total": stats[0]
            }

    except Exception as e:
        logger.error(f"Database error in get_request_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


# ==================== TRANSCRIPT REQUESTS CRUD ENDPOINTS ====================

class TranscriptRequestCreate(BaseModel):
    student_id: str
    request_type: str
    delivery_method: str
    purpose: Optional[str] = None
    copies_requested: int = 1
    rush_processing: bool = False
    recipient_name: Optional[str] = None
    recipient_organization: Optional[str] = None
    notes: Optional[str] = None

class TranscriptRequestUpdate(BaseModel):
    request_type: Optional[str] = None
    delivery_method: Optional[str] = None
    purpose: Optional[str] = None
    copies_requested: Optional[int] = None
    rush_processing: Optional[bool] = None
    status: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_organization: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None

class TranscriptRequestResponse(BaseModel):
    id: str
    student_id: str
    student_number: Optional[str] = None
    student_name: Optional[str] = None
    request_type: str
    delivery_method: str
    status: str
    purpose: Optional[str] = None
    copies_requested: int
    rush_processing: bool
    fee_amount: float
    payment_status: str
    recipient_name: Optional[str] = None
    recipient_organization: Optional[str] = None
    requested_date: str
    approved_date: Optional[str] = None
    completed_date: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None


@router.post("/transcript-requests", response_model=TranscriptRequestResponse)
def create_transcript_request(
    request: TranscriptRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new transcript request"""
    try:
        # Calculate fee based on request type and copies
        fee_amount = 0.0
        if request.request_type == "official":
            fee_amount = 15.00 * request.copies_requested
        elif request.request_type == "verification":
            fee_amount = 10.00 * request.copies_requested
        elif request.request_type == "duplicate":
            fee_amount = 25.00 * request.copies_requested

        if request.rush_processing:
            fee_amount *= 1.5  # 50% surcharge for rush

        result = db.execute(text("""
            INSERT INTO transcript_requests (
                student_id, request_type, delivery_method, purpose,
                copies_requested, rush_processing, fee_amount,
                recipient_name, recipient_organization, notes
            )
            VALUES (
                :student_id, :request_type, :delivery_method, :purpose,
                :copies_requested, :rush_processing, :fee_amount,
                :recipient_name, :recipient_organization, :notes
            )
            RETURNING id, requested_date, status, payment_status
        """), {
            "student_id": request.student_id,
            "request_type": request.request_type,
            "delivery_method": request.delivery_method,
            "purpose": request.purpose,
            "copies_requested": request.copies_requested,
            "rush_processing": request.rush_processing,
            "fee_amount": fee_amount,
            "recipient_name": request.recipient_name,
            "recipient_organization": request.recipient_organization,
            "notes": request.notes
        })

        db.commit()
        row = result.fetchone()

        # Get student info
        student_result = db.execute(text("""
            SELECT s.student_number, p.first_name, p.last_name
            FROM students s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE s.id = :student_id
        """), {"student_id": request.student_id})
        student = student_result.fetchone()

        return TranscriptRequestResponse(
            id=str(row[0]),
            student_id=request.student_id,
            student_number=student[0] if student else None,
            student_name=f"{student[1]} {student[2]}".strip() if student and student[1] else None,
            request_type=request.request_type,
            delivery_method=request.delivery_method,
            status=row[2],
            purpose=request.purpose,
            copies_requested=request.copies_requested,
            rush_processing=request.rush_processing,
            fee_amount=fee_amount,
            payment_status=row[3],
            recipient_name=request.recipient_name,
            recipient_organization=request.recipient_organization,
            requested_date=row[1].isoformat(),
            notes=request.notes
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating transcript request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create request: {str(e)}")


@router.get("/transcript-requests/{request_id}", response_model=TranscriptRequestResponse)
def get_transcript_request(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Get a single transcript request by ID"""
    try:
        result = db.execute(text("""
            SELECT
                tr.id, tr.student_id, tr.request_type, tr.delivery_method,
                tr.status, tr.purpose, tr.copies_requested, tr.rush_processing,
                tr.fee_amount, tr.payment_status, tr.recipient_name,
                tr.recipient_organization, tr.requested_date, tr.approved_date,
                tr.completed_date, tr.rejection_reason, tr.notes,
                s.student_number, p.first_name, p.last_name
            FROM transcript_requests tr
            LEFT JOIN students s ON tr.student_id = s.id
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE tr.id = :request_id
        """), {"request_id": request_id})

        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcript request not found")

        return TranscriptRequestResponse(
            id=str(row[0]),
            student_id=str(row[1]),
            student_number=row[17],
            student_name=f"{row[18]} {row[19]}".strip() if row[18] else None,
            request_type=row[2],
            delivery_method=row[3],
            status=row[4],
            purpose=row[5],
            copies_requested=row[6],
            rush_processing=row[7],
            fee_amount=float(row[8]),
            payment_status=row[9],
            recipient_name=row[10],
            recipient_organization=row[11],
            requested_date=row[12].isoformat(),
            approved_date=row[13].isoformat() if row[13] else None,
            completed_date=row[14].isoformat() if row[14] else None,
            rejection_reason=row[15],
            notes=row[16]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcript request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch request: {str(e)}")


@router.put("/transcript-requests/{request_id}", response_model=TranscriptRequestResponse)
def update_transcript_request(
    request_id: str,
    request: TranscriptRequestUpdate,
    db: Session = Depends(get_db)
):
    """Update a transcript request"""
    try:
        # Build update query dynamically
        update_fields = []
        params = {"request_id": request_id}

        if request.request_type is not None:
            update_fields.append("request_type = :request_type")
            params["request_type"] = request.request_type
        if request.delivery_method is not None:
            update_fields.append("delivery_method = :delivery_method")
            params["delivery_method"] = request.delivery_method
        if request.purpose is not None:
            update_fields.append("purpose = :purpose")
            params["purpose"] = request.purpose
        if request.copies_requested is not None:
            update_fields.append("copies_requested = :copies_requested")
            params["copies_requested"] = request.copies_requested
        if request.rush_processing is not None:
            update_fields.append("rush_processing = :rush_processing")
            params["rush_processing"] = request.rush_processing
        if request.status is not None:
            update_fields.append("status = :status")
            params["status"] = request.status
        if request.recipient_name is not None:
            update_fields.append("recipient_name = :recipient_name")
            params["recipient_name"] = request.recipient_name
        if request.recipient_organization is not None:
            update_fields.append("recipient_organization = :recipient_organization")
            params["recipient_organization"] = request.recipient_organization
        if request.notes is not None:
            update_fields.append("notes = :notes")
            params["notes"] = request.notes
        if request.rejection_reason is not None:
            update_fields.append("rejection_reason = :rejection_reason")
            params["rejection_reason"] = request.rejection_reason

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE transcript_requests
            SET {', '.join(update_fields)}
            WHERE id = :request_id
            RETURNING id
        """

        result = db.execute(text(query), params)
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transcript request not found")

        # Return updated request
        return get_transcript_request(request_id, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating transcript request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update request: {str(e)}")


@router.delete("/transcript-requests/{request_id}")
def delete_transcript_request(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Delete/cancel a transcript request"""
    try:
        result = db.execute(text("""
            UPDATE transcript_requests
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE id = :request_id
            RETURNING id
        """), {"request_id": request_id})

        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transcript request not found")

        return {"message": "Transcript request cancelled successfully", "id": request_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting transcript request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete request: {str(e)}")