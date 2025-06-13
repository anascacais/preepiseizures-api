import csv
import mysql.connector
from dotenv import load_dotenv
import sys
sys.path.append('app')
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

def get_patient_id(cursor, patient_code):
    cursor.execute("SELECT patient_id FROM patients WHERE patient_code = %s", (patient_code,))
    row = cursor.fetchone()
    return row[0] if row else None
    

def import_sessions_from_csv(csv_path):
    conn = get_db_connection()
    cursor = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            patient_code = row["patient_code"].strip()
            patient_id = get_patient_id(cursor, patient_code)
            hospital_code = row.get("hospital_code") or None
            start_time = row.get("start_time") or None
            end_time = row.get("end_time") or None

            try:
                # Insert patient
                cursor.execute(
                    """
                    INSERT INTO sessions (patient_id, hospital_code, start_time, end_time)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (patient_id, hospital_code, start_time, end_time)
                )
                session_id = cursor.lastrowid

                print(f"Imported session {start_time} from patient {patient_code} (ID: {session_id})")
            except mysql.connector.Error as err:
                print(f"Error importing patient {start_time}from patient {patient_code}: {err}")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    csv_path = input("Path to sessions CSV file: ").strip()
    import_sessions_from_csv(csv_path)