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

def add_patient(patient_code, diagnosis=None, laterality=None, common_auras=None, comorbidities=None):
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO patients (patient_code, diagnosis, laterality, common_auras, comorbidities)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (patient_code, diagnosis, laterality, common_auras, comorbidities)
        )
        conn.commit()
        print(f"Patient '{code}' added successfully with ID {patient_code}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    code = input("Patient code: ").strip()
    diagnosis = input("Diagnosis (optional): ").strip() or None
    laterality = input("Laterality (optional): ").strip() or None
    common_auras = input("Common auras (optional): ").strip() or None
    comorbidities = input("Comorbidities (optional): ").strip() or None

    add_patient(code, diagnosis, laterality, common_auras, comorbidities)