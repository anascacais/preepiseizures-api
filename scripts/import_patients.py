import csv
import os
from hashlib import sha256
import mysql.connector
from dotenv import load_dotenv
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

def get_or_create_diagnosis_id(cursor, name):
    name = name.strip().lower()
    cursor.execute("SELECT diagnosis_id FROM diagnoses WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO diagnoses (name) VALUES (%s)", (name,))
    return cursor.lastrowid

def import_patients_from_csv(csv_path):
    conn = get_db_connection()
    cursor = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["patient_code"].strip()
            laterality = row.get("laterality") or None
            common_auras = row.get("common_auras") or None
            comorbidities = row.get("comorbidities") or None
            diagnoses = [d.strip() for d in (row.get("diagnosis") or "").split(",") if d.strip()]

            try:
                # Insert patient
                cursor.execute(
                    """
                    INSERT INTO patients (patient_code, laterality, common_auras, comorbidities)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (code, laterality, common_auras, comorbidities)
                )
                patient_id = cursor.lastrowid

                # Insert diagnoses and link
                for diag in diagnoses:
                    diagnosis_id = get_or_create_diagnosis_id(cursor, diag)
                    cursor.execute(
                        "INSERT IGNORE INTO patient_diagnoses (patient_id, diagnosis_id) VALUES (%s, %s)",
                        (patient_id, diagnosis_id)
                    )

                print(f"Imported patient {code} (ID: {patient_id})")
            except mysql.connector.Error as err:
                print(f"Error importing patient {code}: {err}")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    csv_path = input("Path to patient CSV file: ").strip()
    import_patients_from_csv(csv_path)