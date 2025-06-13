# built-in
from datetime import datetime

# third-party
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

# local
from app.database import get_db_connection
from app.routers.checks import check_session_date_id
from app.routers.enums import SeizureTypeEnum

router = APIRouter(prefix='/events', tags=['events'])

@router.get("/", summary="Get events", description="Retrieve all events with optional filters, including by patient code, session, and event type.")
def get_events(
    patient_code: Optional[str] = Query(None, description='4-letter code identifying the patient'),
    session_date: Optional[datetime] = Query(None, description='Session datetime (in the format YYYY-MM-DD HH:MM:SS) which should be within the range of start_time and end_time of desired session'),
    session_id: Optional[int] = Query(None, description='Session ID'),
    event_types: Optional[list[SeizureTypeEnum]] = Query(None, description='List of seizure classifications (see class SeizureTypeEnum for options)'),
):
    """
    Retrieve all events with optional filters, including by patient code and session.

    - **patient_code**: 4-letter code identifying the patient
    - **session_date**: Session datetime (in the format YYYY-MM-DD HH:MM:SS) which should be within the range of start_time and end_time of desired session
    - **session_id**: Session ID
    - **event_types**: List of seizure classifications (see class SeizureTypeEnum for options)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Consistency check if both session_id and session_date are provided
        if session_id and session_date:
            check_session_date_id(cursor, session_id, session_date)
            
        query = """
            SELECT e.event_id, e.onset_time, e.offset_time, e.annotations
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

        # Seizure types: require ALL specified types
        if event_types:
            placeholders = ', '.join(['%s'] * len(event_types))
            subquery = f"""
                SELECT et_inner.event_id
                FROM event_seizure_types et_inner
                JOIN seizure_types st_inner ON et_inner.seizure_type_id = st_inner.seizure_type_id
                WHERE st_inner.name IN ({placeholders})
                GROUP BY et_inner.event_id
                HAVING COUNT(DISTINCT st_inner.name) = %s
            """
            query += f" AND e.event_id IN ({subquery})"
            params.extend(event_types)
            params.append(len(event_types))

        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No events found matching the filters.")
        return results
    
    finally:
        cursor.close()
        conn.close()