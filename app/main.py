# built-in
from pathlib import Path

# third-party
from fastapi import FastAPI
import smbclient

# local
from app.routers import records, download, events, sessions, token
from app.config import SMB_USER, SMB_PASSWORD

# Register your SMB server credentials
smbclient.ClientConfig(username=SMB_USER, password=SMB_PASSWORD)

description = Path("README.md").read_text()

app = FastAPI(
    title="PreEpiSeizuresAPI",
    description=description,
    summary="RESTful API to query metadata about hospital records.",
    version="2.0.0",
    contact={
        "name": "Ana Sofia Carmo",
        "email": "anascacais@gmail.com",
    },
    license_info={
        "name": "BSD 3-Clause License",
    },
)

app.include_router(token.router)
app.include_router(records.router)
app.include_router(download.router)
app.include_router(events.router)
app.include_router(sessions.router)





