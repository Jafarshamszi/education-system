from fastapi import APIRouter, Depends, HTTPException
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

from app.core.config import settings

router = APIRouter()

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@router.get("/academic-schedule/years")
def get_academic_years():
    """Get all academic years from academic_terms"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT
                academic_year as name,
                MIN(start_date) as start_date,
                MAX(end_date) as end_date,
                MAX(CASE WHEN is_current THEN 1 ELSE 0 END) as active
            FROM academic_terms 
            GROUP BY academic_year
            ORDER BY academic_year DESC
        """)
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        conn.close()



@router.get("/academic-schedule/details")
def get_academic_schedule_details():
    """Get detailed academic schedule using academic_terms and calendar_events"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get academic terms with their calendar events
        cursor.execute("""
            SELECT 
                at.academic_year,
                at.term_type,
                at.start_date as term_start,
                at.end_date as term_end,
                at.is_current,
                ce.id::text as event_id,
                ce.title,
                ce.description,
                ce.start_datetime as event_start,
                ce.end_datetime as event_end,
                ce.event_type,
                ce.is_mandatory
            FROM academic_terms at
            LEFT JOIN calendar_events ce ON at.id = ce.academic_term_id
            ORDER BY at.start_date DESC, ce.start_datetime ASC
        """)
        
        results = cursor.fetchall()
        
        # Group results by academic year and term
        years_data = {}
        for row in results:
            key = f"{row['academic_year']}-{row['term_type']}"
            if key not in years_data:
                years_data[key] = {
                    'education_year': row['academic_year'],
                    'term_type': row['term_type'],
                    'year_start': row['term_start'].isoformat() if row['term_start'] else None,
                    'year_end': row['term_end'].isoformat() if row['term_end'] else None,
                    'is_current': row['is_current'],
                    'events': []
                }
            
            # Add event if it exists
            if row['event_id']:
                event = {
                    'id': row['event_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'start_date': row['event_start'].isoformat() if row['event_start'] else None,
                    'end_date': row['event_end'].isoformat() if row['event_end'] else None,
                    'event_type': row['event_type'],
                    'is_mandatory': row['is_mandatory'],
                    'semester_type': f"{row['term_type'].capitalize()} Semester"
                }
                years_data[key]['events'].append(event)
        
        return list(years_data.values())
        
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

@router.get("/academic-schedule/stats")
def get_education_statistics():
    """Get education system statistics"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get academic programs count (replaces education_plan)
        cursor.execute("SELECT COUNT(*) as count FROM academic_programs")
        education_plans_count = cursor.fetchone()['count']
        
        # Get student groups count (replaces education_group)
        cursor.execute("SELECT COUNT(*) as count FROM student_groups")
        education_groups_count = cursor.fetchone()['count']
        
        # Get scheduled events count (replaces academic_schedule_details)
        cursor.execute("SELECT COUNT(*) as count FROM calendar_events")
        scheduled_events_count = cursor.fetchone()['count']
        
        return {
            'total_education_plans': education_plans_count,
            'total_education_groups': education_groups_count,
            'total_scheduled_events': scheduled_events_count
        }
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        conn.close()

@router.get("/academic-schedule/year/{year_name}")
def get_academic_year_details(year_name: str):
    """Get detailed schedule for a specific academic year from LMS database"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Query academic_terms and calendar_events from LMS database
        cursor.execute("""
            SELECT
                at.id::text as term_id,
                at.academic_year as education_year,
                at.term_type,
                at.start_date as term_start,
                at.end_date as term_end,
                at.registration_start,
                at.registration_end,
                at.add_drop_deadline,
                at.withdrawal_deadline,
                at.grade_submission_deadline,
                at.is_current as active,
                ce.id::text as event_id,
                ce.title as event_title,
                ce.description as event_description,
                ce.start_datetime as event_start,
                ce.end_datetime as event_end,
                ce.event_type,
                ce.is_mandatory,
                ce.location
            FROM academic_terms at
            LEFT JOIN calendar_events ce ON at.id = ce.academic_term_id
            WHERE at.academic_year = %s
            ORDER BY at.term_number ASC, ce.start_datetime ASC
        """, (year_name,))

        results = cursor.fetchall()

        if not results:
            raise HTTPException(status_code=404, detail=f"Academic year '{year_name}' not found")

        # Get the first term to extract year-level info
        first_term = results[0]

        # Find min start_date and max end_date across all terms
        cursor.execute("""
            SELECT
                MIN(start_date) as year_start,
                MAX(end_date) as year_end
            FROM academic_terms
            WHERE academic_year = %s
        """, (year_name,))
        year_dates = cursor.fetchone()

        # Structure the response
        year_info = {
            'year_id': first_term['term_id'],  # Use first term ID as year ID
            'education_year': first_term['education_year'],
            'year_start': year_dates['year_start'].isoformat() if year_dates['year_start'] else None,
            'year_end': year_dates['year_end'].isoformat() if year_dates['year_end'] else None,
            'active': first_term['active'],
            'events': [],
            'terms': []
        }

        # Group by term
        terms_dict = {}
        for row in results:
            term_key = row['term_id']

            if term_key not in terms_dict:
                terms_dict[term_key] = {
                    'term_id': row['term_id'],
                    'term_type': row['term_type'],
                    'term_start': row['term_start'].isoformat() if row['term_start'] else None,
                    'term_end': row['term_end'].isoformat() if row['term_end'] else None,
                    'registration_start': row['registration_start'].isoformat() if row['registration_start'] else None,
                    'registration_end': row['registration_end'].isoformat() if row['registration_end'] else None,
                    'add_drop_deadline': row['add_drop_deadline'].isoformat() if row['add_drop_deadline'] else None,
                    'withdrawal_deadline': row['withdrawal_deadline'].isoformat() if row['withdrawal_deadline'] else None,
                    'grade_submission_deadline': row['grade_submission_deadline'].isoformat() if row['grade_submission_deadline'] else None,
                    'events': []
                }

            # Add event if it exists
            if row['event_id']:
                event = {
                    'id': row['event_id'],
                    'title': row['event_title'],
                    'description': row['event_description'],
                    'start_date': row['event_start'].isoformat() if row['event_start'] else None,
                    'end_date': row['event_end'].isoformat() if row['event_end'] else None,
                    'event_type': row['event_type'],
                    'is_mandatory': row['is_mandatory'],
                    'location': row['location'],
                    'semester_type': f"{row['term_type'].capitalize()} Semester"
                }
                terms_dict[term_key]['events'].append(event)
                year_info['events'].append(event)

        year_info['terms'] = list(terms_dict.values())

        return year_info

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        conn.close()

@router.get("/academic-schedule/current")
def get_current_academic_year():
    """Get the current active academic year from LMS database"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # First try to get the term marked as current
        cursor.execute("""
            SELECT
                at.id::text as year_id,
                at.academic_year as education_year,
                MIN(at.start_date) as year_start,
                MAX(at.end_date) as year_end,
                bool_or(at.is_current) as active
            FROM academic_terms at
            WHERE at.is_current = true
            GROUP BY at.academic_year, at.id
            LIMIT 1
        """)

        result = cursor.fetchone()

        if not result:
            # Fallback to finding year that contains current date
            current_date = datetime.now().date()
            cursor.execute("""
                SELECT
                    at.id::text as year_id,
                    at.academic_year as education_year,
                    MIN(at.start_date) as year_start,
                    MAX(at.end_date) as year_end,
                    bool_or(at.is_current) as active
                FROM academic_terms at
                WHERE at.start_date <= %s AND at.end_date >= %s
                GROUP BY at.academic_year, at.id
                ORDER BY at.start_date DESC
                LIMIT 1
            """, (current_date, current_date))
            result = cursor.fetchone()

        if not result:
            # Final fallback to the most recent academic year
            cursor.execute("""
                SELECT
                    at.id::text as year_id,
                    at.academic_year as education_year,
                    MIN(at.start_date) as year_start,
                    MAX(at.end_date) as year_end,
                    bool_or(at.is_current) as active
                FROM academic_terms at
                GROUP BY at.academic_year, at.id
                ORDER BY at.start_date DESC
                LIMIT 1
            """)
            result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="No academic years found")

        return dict(result)

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        conn.close()


# Pydantic models for request/response
class EventCreate(BaseModel):
    academic_term_id: str  # UUID of the academic term
    event_type: str  # 'academic', 'exam', 'registration', 'holiday'
    title: dict  # JSONB with multilingual titles (e.g., {"az": "...", "ru": "...", "en": "..."})
    start_date: str  # Format: ISO 8601 or DD/MM/YYYY
    end_date: Optional[str] = None  # Format: ISO 8601 or DD/MM/YYYY
    is_mandatory: Optional[bool] = True
    description: Optional[dict] = None  # JSONB with multilingual descriptions


class EventUpdate(BaseModel):
    start_date: Optional[str] = None  # Format: ISO 8601 or DD/MM/YYYY
    end_date: Optional[str] = None  # Format: ISO 8601 or DD/MM/YYYY


@router.post("/academic-schedule/events")
def create_event(event: EventCreate):
    """Create a new calendar event"""
    import uuid
    import json
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Helper function to parse date strings
        def parse_date(date_str):
            if not date_str:
                return None
            # Try ISO 8601 format first
            try:
                return datetime.fromisoformat(
                    date_str.replace('Z', '+00:00')
                )
            except:
                # Try DD/MM/YYYY format
                try:
                    day, month, year = date_str.split('/')
                    return datetime(int(year), int(month), int(day))
                except:
                    return None
        
        # Parse dates
        start_datetime = parse_date(event.start_date)
        end_datetime = parse_date(event.end_date) if event.end_date else None
        
        if not start_datetime:
            raise HTTPException(
                status_code=400, 
                detail="Invalid start_date format"
            )
        
        # Generate new UUID for the event
        new_id = str(uuid.uuid4())
        
        # Insert new event into calendar_events
        cursor.execute("""
            INSERT INTO calendar_events 
            (id, academic_term_id, event_type, title, start_datetime, 
             end_datetime, is_mandatory, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id::text as id
        """, (
            new_id, 
            event.academic_term_id, 
            event.event_type,
            json.dumps(event.title),
            start_datetime,
            end_datetime,
            event.is_mandatory,
            json.dumps(event.description) if event.description else None
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        return {
            "id": result["id"], 
            "message": "Event created successfully"
        }
        
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create event: {str(e)}"
        )
    finally:
        conn.close()


@router.put("/academic-schedule/events/{event_id}")
def update_event(event_id: str, event: EventUpdate):
    """Update an existing calendar event"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        def parse_date(date_str):
            """Parse date from ISO 8601 or DD/MM/YYYY format"""
            if not date_str:
                return None
            # Try ISO 8601 format first
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                # Try DD/MM/YYYY format
                try:
                    day, month, year = date_str.split('/')
                    return datetime(int(year), int(month), int(day))
                except:
                    return None
            
        if event.start_date is not None:
            parsed_date = parse_date(event.start_date)
            if parsed_date:
                update_fields.append("start_datetime = %s")
                params.append(parsed_date)
            
        if event.end_date is not None:
            parsed_date = parse_date(event.end_date)
            if parsed_date:
                update_fields.append("end_datetime = %s")
                params.append(parsed_date)
            
        if not update_fields:
            raise HTTPException(
                status_code=400,
                detail="No valid fields to update"
            )
            
        # Add update metadata
        update_fields.append("updated_at = NOW()")
        
        # Add event_id parameter
        params.append(event_id)
        
        query = f"""
            UPDATE calendar_events 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id::text as id
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
            
        conn.commit()
        
        return {
            "id": result["id"],
            "message": "Event updated successfully"
        }
        
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update event: {str(e)}")
    finally:
        conn.close()


@router.delete("/academic-schedule/events/{event_id}")
def delete_event(event_id: str):
    """Delete a calendar event"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if event exists in calendar_events
        cursor.execute("SELECT id FROM calendar_events WHERE id = %s", (event_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Delete the event from calendar_events
        cursor.execute("DELETE FROM calendar_events WHERE id = %s", (event_id,))
        conn.commit()
        
        return {"message": "Event deleted successfully"}
        
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")
    finally:
        conn.close()


@router.get("/academic-schedule/types")
def get_event_types():
    """Get available event types for creating new events"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get unique type_ids from existing events
        cursor.execute("""
            SELECT DISTINCT type_id::text as type_id, 
                   COUNT(*) as usage_count
            FROM academic_schedule_details 
            WHERE active = 1
            GROUP BY type_id
            ORDER BY usage_count DESC
        """)
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        conn.close()