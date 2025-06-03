import getpass
import mysql.connector
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env variables

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def create_user(username: str, password: str, full_name=None, email=None):
    hashed_password = pwd_context.hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password, full_name, email) VALUES (%s, %s, %s, %s)",
            (username, hashed_password, full_name, email)
        )
        conn.commit()
        print(f"User '{username}' created successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    username = input("Enter new username: ")
    password = getpass.getpass("Enter new password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Passwords do not match. Exiting.")
        exit(1)

    full_name = input("Full name (optional): ").strip() or None
    email = input("Email (optional): ").strip() or None

    create_user(username, password, full_name, email)