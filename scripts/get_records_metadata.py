import os
from dotenv import load_dotenv
import mysql.connector
from config import SMB_USER, SMB_PASSWORD, SMB_SHARE, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, LOCAL_MNT
import smbclient
import re
from datetime import datetime, timedelta
import ast 


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

def _get_session_id_from_patient(cursor, code, file):
    cursor.execute("""
        SELECT s.* 
        FROM patients p 
        LEFT JOIN sessions s ON p.patient_id = s.patient_id 
        WHERE p.patient_code = %s
    """, (code,))
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No sessions found for that patient code.")
        return None

    session_ids = [row[0] for row in rows if row[0] is not None]
    
    if not session_ids:
        print("Patient found but no session IDs linked.")
        return None

    if len(session_ids) == 1:
        return session_ids[0]
    
    print(f"Multiple sessions found for {file} (patient {code}):")
    for idx, sid in enumerate(session_ids):
        print(f"{idx + 1}. {rows[idx]}")
    
    while True:
        try:
            choice = int(input(f"Select session number (1-{len(session_ids)}): "))
            if 1 <= choice <= len(session_ids):
                return session_ids[choice - 1]
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")
    
def _get_times_from_file(filepath, file):
    data_file_pattern = re.compile(r"A2.*\.txt")

    if data_file_pattern.fullmatch(file):

        # Get start time
        file_datetime = os.path.splitext(file)[0][1:]

        parts = file_datetime.split('-')
        if len(parts[-1]) == 0:
            parts[-1] = parts[-1] + '00'
        elif len(parts[-1]) == 1:  # seconds like '3' → '30'
            parts[-1] = parts[-1] + '0'

        start_time = datetime.strptime('-'.join(parts), '%Y-%m-%d %H-%M-%S')

        # Get end time
        with open(filepath, 'r') as f:
            _ = next(f)
            header_line = next(f).strip()
            sample_count = sum(1 for _ in f)

        dict_str = header_line[1:].strip()
        header_dict = ast.literal_eval(dict_str)

        fs = header_dict[list(header_dict.keys())[0]]['sampling rate']
        duration_sec = sample_count / fs
        end_time = start_time + timedelta(seconds=duration_sec)

        return start_time.strftime("%Y-%m-%d %H-%M-%S"), end_time.strftime("%Y-%m-%d %H-%M-%S")

    else:
        return None, None


conn = get_db_connection()
cursor = conn.cursor()

# Register your SMB server credentials
smbclient.ClientConfig(username=SMB_USER, password=SMB_PASSWORD)

patient_list = smbclient.listdir(rf"{SMB_SHARE}")


for pat in patient_list[25:]: #################### TEMPORARY

    patient_dir = rf"{SMB_SHARE}\{pat}"

    directory_list = smbclient.listdir(patient_dir)
    
    for dir in directory_list:
        
        if not smbclient.path.isdir(rf"{patient_dir}\{dir}"):
            continue
        
        file_dir = rf"{patient_dir}\{dir}" 
        file_list = smbclient.listdir(file_dir)
        
        for file in file_list:
            session_id = _get_session_id_from_patient(cursor, pat, file)
            file_name, file_extension, modality = _get_metadata_from_name(file)
            smb_path = rf"{pat}\{dir}\{file}"
            start_time, end_time = _get_times_from_file(os.path.join('/'.join(LOCAL_MNT.split('\\')), pat, dir, file), file)

            try:
                cursor.execute(
                    """
                    INSERT INTO records (session_id, file_name, file_extension, smb_path, modality, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (session_id, file_name, file_extension, smb_path, modality, start_time, end_time)
                )
                record_id = cursor.lastrowid

                print(f"Imported record {smb_path} (ID: {record_id})")
            except mysql.connector.Error as err:
                print(f"Error importing record {file}: {err}")
    
conn.commit()
cursor.close()
conn.close()
        
