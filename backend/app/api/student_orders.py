"""
Student Orders API endpoints
Provides access to student orders data from the LMS database
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Any
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings

router = APIRouter()


def get_db_connection():
    """Get database connection to LMS database"""
    return psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        cursor_factory=RealDictCursor
    )


class OrderType(BaseModel):
    order_type: str
    count: int
    active_count: int


class OrderSummary(BaseModel):
    total_orders: int = 0
    active_orders: int = 0
    inactive_orders: int = 0
    total_students: int = 0
    total_relationships: int = 0


class OrdersSummaryResponse(BaseModel):
    summary: OrderSummary
    order_types: List[OrderType] = []


class OrderResponse(BaseModel):
    id: str  # Changed to str for UUID
    order_number: str
    order_type: str
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    status: str
    created_date: Optional[str] = None


class PaginationInfo(BaseModel):
    page: int = 1
    limit: int = 20
    total: int = 0
    total_pages: int = 0


class OrdersListResponse(BaseModel):
    orders: List[Any] = []  # Using Any to allow dict responses with flexible schema
    pagination: PaginationInfo


class OrderCategory(BaseModel):
    id: int
    category_name: str
    order_count: int


class OrderCategoriesResponse(BaseModel):
    categories: List[OrderCategory] = []


@router.get("/orders/summary", response_model=OrdersSummaryResponse)
def get_orders_summary():
    """
    Get summary statistics of all student orders
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total orders count
        cursor.execute("""
            SELECT COUNT(*) as total FROM student_orders
        """)
        total_orders = cursor.fetchone()['total']
        
        # Get active/inactive counts (using status)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as active,
                COUNT(CASE WHEN status != 'approved' THEN 1 END) as inactive
            FROM student_orders
        """)
        status_counts = cursor.fetchone()
        
        # Get total students affected
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id) as total 
            FROM student_order_assignments
            WHERE person_id IS NOT NULL
        """)
        total_students = cursor.fetchone()['total']
        
        # Get total relationships
        cursor.execute("""
            SELECT COUNT(*) as total FROM student_order_assignments
        """)
        total_relationships = cursor.fetchone()['total']
        
        # Get order types with counts
        cursor.execute("""
            SELECT 
                order_type,
                COUNT(*) as count,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as active_count
            FROM student_orders
            GROUP BY order_type
            ORDER BY count DESC
        """)
        
        order_types = []
        for row in cursor.fetchall():
            order_types.append(OrderType(
                order_type=row['order_type'],
                count=row['count'],
                active_count=row['active_count']
            ))
        
        return OrdersSummaryResponse(
            summary=OrderSummary(
                total_orders=total_orders,
                active_orders=status_counts['active'],
                inactive_orders=status_counts['inactive'],
                total_students=total_students,
                total_relationships=total_relationships
            ),
            order_types=order_types
        )
    finally:
        conn.close()


@router.get("/orders/list", response_model=OrdersListResponse)
def get_orders_list(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    order_type: Optional[str] = None,
    active_only: bool = True,
    search: Optional[str] = None
):
    """
    Get paginated list of student orders
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if order_type and order_type != 'all':
            where_clauses.append("order_type = %s")
            params.append(order_type)
        
        if active_only:
            where_clauses.append("status = 'approved'")
        
        if search:
            where_clauses.append(
                "(order_number ILIKE %s OR notes ILIKE %s)"
            )
            params.extend([f"%{search}%", f"%{search}%"])
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count
        cursor.execute(f"""
            SELECT COUNT(*) as total FROM student_orders {where_sql}
        """, params)
        total_count = cursor.fetchone()['total']
        
        # Calculate pagination
        offset = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit
        
        # Get orders with student info
        cursor.execute(f"""
            SELECT
                so.id,
                so.order_number,
                so.order_type,
                so.order_date,
                so.status,
                so.notes,
                so.created_at,
                COUNT(soa.id) as student_count
            FROM student_orders so
            LEFT JOIN student_order_assignments soa ON soa.order_id = so.id
            {where_sql}
            GROUP BY so.id, so.order_number, so.order_type, so.order_date, so.status, so.notes, so.created_at
            ORDER BY so.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        orders = []
        for row in cursor.fetchall():
            # Map database fields to frontend expected fields
            order_data = {
                'id': str(row['id']),  # Convert UUID to string
                'serial': row['order_number'],  # Map order_number to serial
                'order_date': row['order_date'].strftime('%Y-%m-%d') if row.get('order_date') else None,
                'description': row.get('notes'),  # Map notes to description
                'active': 1 if row.get('status') == 'approved' else 0,  # Map status to active
                'order_type': row.get('order_type', ''),
                'status': row.get('status', ''),
                'create_date': row['created_at'].strftime('%Y-%m-%d') if row.get('created_at') else None,
                'student_count': row.get('student_count', 0)
            }
            orders.append(order_data)
        
        return OrdersListResponse(
            orders=orders,
            pagination=PaginationInfo(
                page=page,
                limit=limit,
                total=total_count,
                total_pages=total_pages
            )
        )
    finally:
        conn.close()


@router.get("/orders/categories", response_model=OrderCategoriesResponse)
def get_order_categories():
    """
    Get list of order categories with counts
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                order_type,
                COUNT(*) as count
            FROM student_orders
            GROUP BY order_type
            ORDER BY count DESC
        """)
        
        categories = []
        for idx, row in enumerate(cursor.fetchall(), 1):
            categories.append(OrderCategory(
                id=idx,
                category_name=row['order_type'],
                order_count=row['count']
            ))
        
        return OrderCategoriesResponse(categories=categories)
    finally:
        conn.close()


@router.get("/orders/stats")
async def get_orders_stats():
    """
    Get order statistics - STUB
    Note: Student orders functionality not yet implemented in LMS database
    """
    
    return {
        "total_orders": 0,
        "pending_orders": 0,
        "approved_orders": 0,
        "rejected_orders": 0
    }


@router.get("/orders/{order_id}")
def get_order_detail(order_id: str):
    """
    Return detailed information for a single order including students.
    Includes metadata, affected students/persons, and transfer parameters.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Fetch order details from student_orders
        cursor.execute(
            """
            SELECT
                id, order_number, order_type, order_date,
                status, notes, metadata, created_at
            FROM student_orders
            WHERE id = %s
            """,
            (order_id,)
        )
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Fetch linked students/assignments
        cursor.execute(
            """
            SELECT
                student_id, person_id, notes, metadata, created_at
            FROM student_order_assignments
            WHERE order_id = %s
            """,
            (order_id,)
        )
        assignments = cursor.fetchall()

        # Build students list
        students = []
        transfer_parameters = []
        for a in assignments:
            # Attempt to resolve student name if student_id exists
            student_name = None
            if a.get('student_id'):
                try:
                    cursor.execute(
                        """
                        SELECT
                            student_number,
                            metadata->>'first_name' as first_name,
                            metadata->>'last_name' as last_name
                        FROM students
                        WHERE id = %s
                        """,
                        (a['student_id'],)
                    )
                    s = cursor.fetchone()
                    if s:
                        first_name = s.get('first_name') or ''
                        last_name = s.get('last_name') or ''
                        student_name = f"{first_name} {last_name}".strip()
                        if not student_name:
                            student_name = s.get('student_number')
                except Exception:
                    student_name = None

            students.append({
                'student_id': a.get('student_id'),
                'person_id': a.get('person_id'),
                'name': student_name,
                'notes': a.get('notes'),
                'created_at': a.get('created_at')
            })

            # Extract transfer parameters from metadata
            try:
                meta = a.get('metadata') or {}
                if isinstance(meta, dict) and meta.get('transfer_from'):
                    transfer_parameters.append({
                        'student_id': a.get('student_id'),
                        'from_group_id': meta.get('transfer_from'),
                        'to_group_id': meta.get('transfer_to'),
                        'active': 1,
                        'from_group_name': meta.get('from_group_name'),
                        'to_group_name': meta.get('to_group_name')
                    })
            except Exception:
                pass

        # Map to frontend expected format
        result = {
            'order': {
                'id': str(order.get('id')),
                'serial': order.get('order_number'),  # Map order_number to serial
                'order_number': order.get('order_number'),
                'order_type': order.get('order_type'),
                'order_date': order.get('order_date').strftime('%Y-%m-%d') if order.get('order_date') else None,
                'status': order.get('status'),
                'active': order.get('status') == 'approved',  # Map status to active boolean
                'description': order.get('notes'),  # Map notes to description
                'notes': order.get('notes'),
                'metadata': order.get('metadata'),
                'create_date': order.get('created_at').strftime('%Y-%m-%d') if order.get('created_at') else None,
                'created_at': order.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if order.get('created_at') else None
            },
            'students': students,
            'transfer_parameters': transfer_parameters
        }

        return result
    finally:
        conn.close()
