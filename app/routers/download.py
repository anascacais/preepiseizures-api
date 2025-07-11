# third-party
from fastapi import APIRouter, Path, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
import io
import smbclient
import zipstream

# local
from app.database import get_db_connection
from app.config import SMB_SHARE
from app.routers.token import get_current_user


router = APIRouter(prefix='/download', tags=['download'])

@router.get("/{record_id}", summary="Download record", description="Download a single record by ID")
def download_file(record_id: int = Path(..., description="Record ID"), user=Depends(get_current_user)):
    """
    Download a single record by ID.

    - **record_id**: Record ID
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM records WHERE record_id = %s
        """
        cursor.execute(query, (record_id,))
        entry = cursor.fetchone()

        if not entry:
            raise HTTPException(status_code=404, detail="File not found")
        
        if entry["modality"] in ["hospital_video", "report"] and not user['can_access_sensitive']:
            raise HTTPException(status_code=403, detail="Access to sensitive data denied.")
        
        smb_path = rf"{SMB_SHARE}\{entry['smb_path']}"

        with smbclient.open_file(smb_path, mode='rb') as remote_file:
            data = remote_file.read()

        return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream", headers={
            "Content-Disposition": f"attachment; filename={entry['smb_path']}"
        })

    finally:
        cursor.close()
        conn.close()


@router.get("/", summary="Download records", description="Download multiple records by ID into a zip")
def download_files(record_ids: list[int] = Query(..., description="List with record IDs"), user=Depends(get_current_user)):
    """
    Download multiple records by ID into a zip. The zip maintains original directory structure.

    - **record_id**: List with record IDs
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch all files matching the given IDs
        format_strings = ','.join(['%s'] * len(record_ids))
        query = f"SELECT * FROM records WHERE record_id IN ({format_strings})"
        cursor.execute(query, tuple(record_ids))
        files = cursor.fetchall()

        if not files:
            raise HTTPException(status_code=404, detail="No files found")

        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)

        # Add files to ZIP stream one by one
        for f in files:
            if f["modality"] in ["hospital_video", "report"] and not user['can_access_sensitive']:
                raise HTTPException(status_code=403, detail="Access to sensitive data denied.")
            smb_path = rf"{SMB_SHARE}\{f['smb_path']}"

            def file_generator(path):
                with smbclient.open_file(path, mode='rb') as remote_file:
                    chunk = remote_file.read(4096)
                    while chunk:
                        yield chunk
                        chunk = remote_file.read(4096)

            z.write_iter(f['smb_path'], file_generator(smb_path))

        return StreamingResponse(
            z,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=records.zip"}
        )

    finally:
        cursor.close()
        conn.close()