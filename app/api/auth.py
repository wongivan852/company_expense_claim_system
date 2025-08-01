"""Authentication API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    """User registration endpoint."""
    return {"message": "Registration endpoint - to be implemented"}


@router.post("/login")
async def login():
    """User login endpoint."""
    return {"message": "Login endpoint - to be implemented"}


@router.post("/refresh")
async def refresh_token():
    """Token refresh endpoint."""
    return {"message": "Token refresh endpoint - to be implemented"}
