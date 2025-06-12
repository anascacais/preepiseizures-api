# third-party
from fastapi import APIRouter, Path, Query, HTTPException
from fastapi.responses import StreamingResponse
import io
import smbclient
import zipstream

# local
from app.database import get_db_connection
from app.config import SMB_SHARE


router = APIRouter(prefix='/download', tags=['download'])

@router.get("/{record_id}", summary="Download record", description="Download a single record by ID")
def download_file(record_id: int = Path(..., description="Record ID")):
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
        
        smb_path = rf"{SMB_SHARE}\{entry['smb_path']}"
        file = f"{entry['file_name']}{entry['file_extension']}"

        with smbclient.open_file(smb_path, mode='rb') as remote_file:
            data = remote_file.read()

        return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream", headers={
            "Content-Disposition": f"attachment; filename={file}"
        })

    finally:
        cursor.close()
        conn.close()


@router.get("/", summary="Download records", description="Download multiple records by ID into a zip")
def download_files(record_ids: list[int] = Query(..., description="List with record IDs")):
    """
    Download multiple records by ID into a zip.

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
            smb_path = rf"{SMB_SHARE}\{f['smb_path']}"
            file = f"{f['file_name']}{f['file_extension']}"

            def file_generator(path):
                with smbclient.open_file(path, mode='rb') as remote_file:
                    chunk = remote_file.read(4096)
                    while chunk:
                        yield chunk
                        chunk = remote_file.read(4096)

            z.write_iter(file, file_generator(smb_path))

        return StreamingResponse(
            z,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=records.zip"}
        )

    finally:
        cursor.close()
        conn.close()