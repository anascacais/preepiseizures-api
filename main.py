from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
import mysql.connector
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import mysql.connector
from fastapi.responses import StreamingResponse
import io
import smbclient
import zipstream

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, SECRET_KEY, ALGORITHM, SMB_HOST, SMB_USER, SMB_PASSWORD, SMB_SHARE

# Register your SMB server credentials
smbclient.ClientConfig(username=SMB_USER, password=SMB_PASSWORD)


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        print(f"DB Connection Error: {err}")
        raise HTTPException(status_code=500, detail="Database connection error")
    
# Authenticate user (e.g., via /token)
def authenticate_user(username: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and pwd_context.verify(password, user["hashed_password"]):
        return user
    return None

# Token creation
def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"], "user_id": user["id"]})
    return {"access_token": token, "token_type": "bearer"}

# Dependency to get current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except JWTError:
        raise credentials_exception
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user is None:
        raise credentials_exception
    return user

# Protected route to files
@app.get("/files")
def get_files(
    min_events: Optional[int] = Query(0, ge=0),):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM files 
            WHERE event_count >= %s
        """
        cursor.execute(query, (min_events,))
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()


@app.get("/download/{file_id}")
def download_file(file_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM files WHERE id = %s
        """
        cursor.execute(query, (file_id,))
        file_entry = cursor.fetchone()

        if not file_entry:
            raise HTTPException(status_code=404, detail="File not found")
        
        smb_path = rf"{SMB_SHARE}\{file_entry['smb_path']}"
        print(smb_path)
        filename = file_entry["filename"]

        with smbclient.open_file(smb_path, mode='rb') as remote_file:
            data = remote_file.read()

        return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream", headers={
            "Content-Disposition": f"attachment; filename={filename}"
        })

    finally:
        cursor.close()
        conn.close()


@app.get("/download")
def download_files(file_ids: list[int] = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch all files matching the given IDs
        format_strings = ','.join(['%s'] * len(file_ids))
        query = f"SELECT * FROM files WHERE id IN ({format_strings})"
        cursor.execute(query, tuple(file_ids))
        files = cursor.fetchall()

        if not files:
            raise HTTPException(status_code=404, detail="No files found")

        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)

        # Add files to ZIP stream one by one
        for f in files:
            smb_path = rf"{SMB_SHARE}\{f['smb_path']}"
            filename = f['filename']

            def file_generator(path):
                with smbclient.open_file(path, mode='rb') as remote_file:
                    chunk = remote_file.read(4096)
                    while chunk:
                        yield chunk
                        chunk = remote_file.read(4096)

            z.write_iter(filename, file_generator(smb_path))

        return StreamingResponse(
            z,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=files.zip"}
        )

    finally:
        cursor.close()
        conn.close()


@app.get("/patients/{patient_code}/sessions")
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


def _check_session_date_id(cursor, session_id, session_date):
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

@app.get("/records")
def get_records(
    patient_code: Optional[str] = Query(None),
    session_date: Optional[datetime] = Query(None),
    session_id: Optional[int] = Query(None),
    modality: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Consistency check if both session_id and session_date are provided
        if session_id and session_date:
            _check_session_date_id(cursor, session_id, session_date)

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


@app.get("/events")
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
            _check_session_date_id(cursor, session_id, session_date)
            
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

