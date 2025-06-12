# third-party
from fastapi import FastAPI
import smbclient

# local
from app.routers import records, download, events, token, patients
from config import SMB_USER, SMB_PASSWORD

# Register your SMB server credentials
smbclient.ClientConfig(username=SMB_USER, password=SMB_PASSWORD)
app = FastAPI()

app.include_router(token.router)
app.include_router(records.router)
app.include_router(download.router)
app.include_router(events.router)
app.include_router(patients.router)





