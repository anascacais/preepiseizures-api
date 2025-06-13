# third-party
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

# local
from app.database import get_db_connection
from app.routers.enums import ModalityEnum, SeizureTypeEnum

router = APIRouter(prefix='/sessions', tags=['sessions'])

@router.get("/", summary="Get sessions", description="Retrieve all sessions with optional filters, including by patient code, event types, or modality.")
def get_sessions(
    patient_code: Optional[str] = Query(None, description='4-letter code identifying the patient'),
    event_types: Optional[list[SeizureTypeEnum]] = Query(None, description='List of seizure classifications (see class SeizureTypeEnum for options)'),
    modality: Optional[ModalityEnum] = Query(None, description='Type of data modality (e.g., hospital_eeg, wearable, hospital_video, report)')
):
    """
    Retrieve all sessions for a patient.

    - **patient_code**: 4-letter code identifying the patient
    - **event_types**: List of seizure classifications (see class SeizureTypeEnum for options)
    - **modality**: Type of data modality (e.g., hospital_eeg, wearable, hospital_video, report)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT DISTINCT s.session_id,s.hospital_code,s.start_time,s.end_time
            FROM sessions s
            JOIN patients p ON s.patient_id = p.patient_id
            JOIN events e ON s.session_id = e.session_id
            JOIN records r ON s.session_id = r.session_id
            WHERE 1=1
        """

        params = []

        if patient_code:
            query += " AND p.patient_code = %s"
            params.append(patient_code)

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

        if modality:
            query += " AND r.modality = %s"
            params.append(modality)


        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No sessions found matching the filters.")

        return results
    finally:
        cursor.close()
        conn.close()
