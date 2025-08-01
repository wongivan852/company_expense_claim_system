"""File management API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_file():
    """Upload receipt files."""
    return {"message": "File upload endpoint - to be implemented"}


@router.get("/{filename}")
async def get_file(filename: str):
    """Download/retrieve files."""
    return {"message": f"Get file {filename} endpoint - to be implemented"}
