import os
from dotenv import load_dotenv
import mysql.connector
from app.config import SMB_USER, SMB_PASSWORD, SMB_SHARE, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import smbclient
from pymediainfo import MediaInfo
import tempfile

load_dotenv()
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def _get_metadata_from_name(file):
    file_name, file_extension = os.path.splitext(file)
    modality_map = {
        'hospital_video': ['.mpe', '.wmv', '.avi'],
        'hospital_eeg': ['.vhdr', '.vmrk', '.eeg', '.edf', '.bdf', '.gdf', '.cnt', '.egi', '.mff', '.set', '.fdt', '.data', '.nxe', '.lay', '.dat', '.eeg', '.21e', '.pnt', '.log', '.xdf', '.xdfz', '.trc'],
        'wearable': ['.txt'],
        'report': ['.doc', '.docx', '.pdf']
    }
    for modality, extensions in modality_map.items():
        if file_extension.lower() in extensions:
            return file_name, file_extension, modality
    return file_name, file_extension, 'unknown'

def _get_session_id_from_patient(cursor, code):
    cursor.execute("SELECT s.session_id FROM patients p LEFT JOIN sessions s ON p.patient_id=s.patient_id WHERE p.patient_code=%s", (code,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
def _get_times_from_file(smb_path):
    return None, None


conn = get_db_connection()
cursor = conn.cursor()

# Register your SMB server credentials
smbclient.ClientConfig(username=SMB_USER, password=SMB_PASSWORD)

patient_list = smbclient.listdir(rf"{SMB_SHARE}")


for pat in patient_list:

    patient_dir = rf"{SMB_SHARE}\{pat}"
    session_id = _get_session_id_from_patient(cursor, pat)

    directory_list = smbclient.listdir(patient_dir)
    if 'Hospital' not in directory_list: # temporary
        continue
    
    for dir in directory_list:
        
        if not smbclient.path.isdir(rf"{patient_dir}\{dir}"):
            continue
        
        file_dir = rf"{patient_dir}\{dir}" 
        file_list = smbclient.listdir(file_dir)
        
        for file in file_list:
            file_name, file_extension, modality = _get_metadata_from_name(file)
            smb_path = rf"{pat}\{dir}\{file}"
            start_time, end_time = _get_times_from_file(fr"{file_dir}\{file}")

            try:
                cursor.execute(
                    """
                    INSERT INTO records (session_id, file_name, file_extension, smb_path, modality, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (session_id, file_name, file_extension, smb_path, modality, start_time, end_time)
                )
                record_id = cursor.lastrowid

                print(f"Imported record {file} (ID: {record_id})")
            except mysql.connector.Error as err:
                print(f"Error importing record {file}: {err}")
    
conn.commit()
cursor.close()
conn.close()
        
