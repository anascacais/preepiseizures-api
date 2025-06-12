# built-in
from datetime import datetime

# third-party
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from enum import Enum

# local
from app.database import get_db_connection
from app.routers.checks import check_session_date_id

router = APIRouter(prefix='/records', tags=['records'])

class ModalityEnum(str, Enum):
    hospital_eeg = "hospital_eeg"
    wearable = "wearable"
    hospital_video = "hospital_video"
    report = "report"


@router.get("/", summary="Get records", description="Retrieve all records with optional filters, including by patient code, session, or modality.")
def get_records(
    patient_code: Optional[str] = Query(None, description='4-letter code identifying the patient'),
    session_date: Optional[datetime] = Query(None, description='Session datetime (in the format YYYY-MM-DD HH:MM:SS) which should be within the range of start_time and end_time of desired session'),
    session_id: Optional[int] = Query(None, description='Session ID'),
    modality: Optional[ModalityEnum] = Query(None, description='Type of data modality (e.g., hospital_eeg, wearable, hospital_video, report)')
):
    """
    Retrieve all records with optional filters, including by patient code, session, or modality.

    - **patient_code**: 4-letter code identifying the patient
    - **session_date**: Session datetime (in the format YYYY-MM-DD HH:MM:SS) which should be within the range of start_time and end_time of desired session
    - **session_id**: Session ID
    - **modality**: Type of data modality (e.g., hospital_eeg, wearable, hospital_video, report)
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Consistency check if both session_id and session_date are provided
        if session_id and session_date:
            check_session_date_id(cursor, session_id, session_date)

        query = """
            SELECT r.record_id
            FROM records r
            JOIN sessions s ON r.session_id=s.session_id
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

        if modality:
            query += " AND r.modality = %s"
            params.append(modality)

        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No records found matching the filters.")
        return results
    
    finally:
        cursor.close()
        conn.close()