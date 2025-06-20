CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    can_access_sensitive BOOLEAN NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    session_id INT AUTO_INCREMENT PRIMARY KEY,      
    patient_id INT,                         
    hospital_code VARCHAR(255),                              
    start_time DATETIME,                             
    end_time DATETIME,                    
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE KEY unique_patient_hospital_start (patient_id, hospital_code, start_time)
);


CREATE TABLE IF NOT EXISTS records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,      
    session_id INT,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(255) NOT NULL,
    smb_path VARCHAR(255) NOT NULL,
    modality ENUM('hospital_video', 'hospital_eeg', 'wearable', 'report') NOT NULL,   
    start_time DATETIME,                             
    end_time DATETIME,                          
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE KEY unique_session_name_type (session_id, file_name, file_extension)
);

CREATE TABLE IF NOT EXISTS events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    onset_time DATETIME,
    offset_time DATETIME,
    annotations TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE KEY unique_session_onset (session_id, onset_time)
);


CREATE TABLE classifications (
    classification_id INT AUTO_INCREMENT PRIMARY KEY,
    name ENUM("seizure", "non-seizure", "subclinical", "electrographic", "non-electrographic",
    "aware", "impaired awareness", "unknown awareness", 
    "focal", "generalized", "to bilateral tonic-clonic", "tonic-clonic", "tonic", 
    "motor", "non-motor", "automatisms", "behavior arrest", "absence"
    ) NOT NULL
);


CREATE TABLE event_classifications (
    event_id INT,
    classification_id INT,
    PRIMARY KEY (event_id, classification_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (classification_id) REFERENCES classifications(classification_id)
);