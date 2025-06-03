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