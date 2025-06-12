# built-in
from datetime import datetime

# third-party
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

# local
from app.database import get_db_connection
from app.routers.checks import check_session_date_id

router = APIRouter(prefix='/events', tags=['events'])

@router.get("/")
def get_events(
    patient_code: Optional[str] = Query(None),
    session_date: Optional[datetime] = Query(None),
    session_id: Optional[int] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Consistency check if both session_id and session_date are provided
        if session_id and session_date:
            check_session_date_id(cursor, session_id, session_date)
            
        query = """
            SELECT e.event_id, e.onset_time, e.offset_time, e.event_name, e.annotations
            FROM events e
            JOIN sessions s ON e.session_id=s.session_id
            JOIN patients p ON s.patient_id=p.patient_id
            WHERE 1=1
        """
        params = []

        if patient_code:
            query += " AND p.patient_code = %s"
            params.append(patient_code)

        if session_date:
            query += " AND s.start_time <= %s AND s.end_time > %s"
            params.extend([session_date, session_date])

        if session_id:
            query += " AND s.session_id = %s"
            params.append(session_id)

        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No events found matching the filters.")
        return results
    
    finally:
        cursor.close()
        conn.close()