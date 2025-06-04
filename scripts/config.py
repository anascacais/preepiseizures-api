from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
PATIENT_HASH_SALT = os.getenv("PATIENT_HASH_SALT")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

SMB_HOST = os.getenv("SMB_HOST")
SMB_SHARE = os.getenv("SMB_SHARE")
SMB_USER = os.getenv("SMB_USER")
SMB_PASSWORD = os.getenv("SMB_PASSWORD")