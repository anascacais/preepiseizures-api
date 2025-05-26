from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from fastapi import FastAPI
import mysql.connector

app = FastAPI()


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


@app.get("/get_files")
def get_files(patient_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM files WHERE patient_id = %s", (patient_id,))
    result = cursor.fetchall()
    conn.close()
    return result
