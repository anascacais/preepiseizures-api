import getpass
import mysql.connector
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

load_dotenv() 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

def create_user(can_access_sensitive: str, username: str, password: str, full_name=None, email=None):
    hashed_password = pwd_context.hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    if can_access_sensitive == 'y': permission=True
    elif can_access_sensitive == 'n': permission=False
    else: raise ValueError("Unknown input. For 'Can this user access sensitive records [y/n]?' type either 'y' or 'n'.")
    try:
        cursor.execute(
            "INSERT INTO users (can_access_sensitive, username, hashed_password, full_name, email) VALUES (%s, %s, %s, %s, %s)",
            (permission, username, hashed_password, full_name, email)
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
    can_access_sensitive = input("Can this user access sensitive records [y/n]?")

    if password != password_confirm:
        print("Passwords do not match. Exiting.")
        exit(1)

    full_name = input("Full name (optional): ").strip() or None
    email = input("Email (optional): ").strip() or None

    create_user(can_access_sensitive, username, password, full_name, email)