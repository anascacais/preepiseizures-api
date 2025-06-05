CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(50),
    filename VARCHAR(255),
    smb_path VARCHAR(255),
    event_count INT,
    starttime DATETIME
);

CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY, 
    patient_code VARCHAR(16) UNIQUE NOT NULL,                              
    laterality TEXT,                            
    common_auras TEXT,                          
    comorbidities TEXT                          
);

CREATE TABLE diagnoses (
    diagnosis_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE patient_diagnoses (
    patient_id INT,
    diagnosis_id INT,
    PRIMARY KEY (patient_id, diagnosis_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(diagnosis_id)
);


CREATE TABLE IF NOT EXISTS sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,       -- Unique session ID
    patient_id VARCHAR(64),                          -- FK to patients.patient_id
    hospital_name TEXT,                              -- Name or code of the hospital
    start_time DATETIME,                             -- Start of the session
    end_time DATETIME,                               -- End of the session
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);