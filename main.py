from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from config import SQLALCHEMY_DATABASE_URL
import databases

app = FastAPI()

# Async DB setup with databases package (optional)
database = databases.Database(SQLALCHEMY_DATABASE_URL)

# For sync queries (SQLAlchemy engine + session)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
metadata = MetaData()

# Reflect tables from existing database schema
patients = Table("patients", metadata, autoload_with=engine)
files = Table("files", metadata, autoload_with=engine)

SessionLocal = sessionmaker(bind=engine)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/files/by_patient/{patient_id}")
async def get_files_by_patient(patient_id: int):
    query = files.select().where(files.c.patient_id == patient_id)
    results = await database.fetch_all(query)
    if not results:
        raise HTTPException(
            status_code=404, detail="No files found for this patient")
    return results


@app.get("/patients")
async def list_patients():
    query = patients.select()
    results = await database.fetch_all(query)
    return results
