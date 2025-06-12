# third-party
import mysql.connector
from fastapi import HTTPException

# local
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

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