# third-party
from fastapi import APIRouter, HTTPException, Path

# local
from app.database import get_db_connection

router = APIRouter(prefix='/patients', tags=['patients'])

@router.get("/{patient_code}/sessions", summary="Get sessions", description="Retrieve all sessions for a patient")
def get_sessions(patient_code: str = Path(..., description='4-letter code identifying the patient')):
    """
    Retrieve all sessions for a patient.

    - **patient_code**: 4-letter code identifying the patient
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT s.session_id
            FROM patients p
            JOIN sessions s ON p.patient_id = s.patient_id
            WHERE p.patient_code = %s
        """
        cursor.execute(query, (patient_code,))
        results = cursor.fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No sessions found for this patient code.")

        return results
    finally:
        cursor.close()
        conn.close()
