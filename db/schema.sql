CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(50),
    filename VARCHAR(255),
    event_count INT,
    timestamp DATETIME
);
