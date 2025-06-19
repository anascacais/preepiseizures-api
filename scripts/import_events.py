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


def get_or_create_event_type_id(cursor, name):
    name = name.strip().lower()
    cursor.execute("SELECT classification_id FROM classifications WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO classifications (name) VALUES (%s)", (name,))
    return cursor.lastrowid


def get_session_id(cursor, onset_time, patient_code):
    query = """
            SELECT s.session_id 
            FROM sessions s
            LEFT JOIN patients p ON s.patient_id=p.patient_id
            WHERE 1=1
        """
    params = []
    
    query += " AND s.start_time <= %s AND s.end_time > %s"
    params.extend([onset_time, onset_time])

    if patient_code:
        query += " AND p.patient_code = %s"
        params.append(patient_code)

    cursor.execute(query, params)
    row = cursor.fetchone()
    return row[0] if row else None
    

def import_events_from_csv(csv_path):
    conn = get_db_connection()
    cursor = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            patient_code = row.get("patient_code") or None
            onset_time = row.get("onset_time") or None
            offset_time = row.get("offset_time") or None
            annotations = row.get("annotations") or None
            session_id = get_session_id(cursor, onset_time, patient_code)
            event_types = [e.strip() for e in (row.get("event_type") or "").split(",") if e.strip()]

            try:
                # Insert event
                cursor.execute(
                    """
                    INSERT INTO events (session_id, onset_time, offset_time, annotations)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, onset_time, offset_time, annotations)
                )
                event_id = cursor.lastrowid

                # Insert diagnoses and link
                for etype in event_types:
                    event_type_id = get_or_create_event_type_id(cursor, etype)
                    cursor.execute(
                        "INSERT IGNORE INTO event_classifications (event_id, classification_id) VALUES (%s, %s)",
                        (event_id, event_type_id)
                    )

                print(f"Imported event {onset_time} from session {session_id} (ID: {event_id})")
            except mysql.connector.Error as err:
                print(f"Error importing event {onset_time}from session {session_id}: {err}")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    csv_path = input("Path to events CSV file: ").strip()
    import_events_from_csv(csv_path)