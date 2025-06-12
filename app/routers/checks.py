# third-party
from fastapi import HTTPException

def check_session_date_id(cursor, session_id, session_date):
    cursor.execute(
        "SELECT start_time, end_time FROM sessions WHERE session_id = %s",
        (session_id,)
    )
    session = cursor.fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Session ID not found.")

    try:
        if not (session["start_time"] <= session_date < session["end_time"]):
            raise HTTPException(
                status_code=400,
                detail="Provided session_date is outside the start/end time of the given session_id."
            )
    except TypeError:
        pass