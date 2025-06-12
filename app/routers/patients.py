# third-party
from fastapi import APIRouter, HTTPException

# local
from app.database import get_db_connection

router = APIRouter(prefix='/patients', tags=['patients'])

@router.get("/{patient_code}/sessions")
def get_sessions(patient_code: str):
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
