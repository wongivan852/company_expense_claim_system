"""Expense claims API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_claims():
    """Get list of expense claims."""
    return {"message": "Get claims endpoint - to be implemented"}


@router.post("/")
async def create_claim():
    """Create new expense claim."""
    return {"message": "Create claim endpoint - to be implemented"}


@router.get("/{claim_id}")
async def get_claim(claim_id: int):
    """Get specific claim by ID."""
    return {"message": f"Get claim {claim_id} endpoint - to be implemented"}


@router.put("/{claim_id}")
async def update_claim(claim_id: int):
    """Update specific claim."""
    return {"message": f"Update claim {claim_id} endpoint - to be implemented"}


@router.delete("/{claim_id}")
async def delete_claim(claim_id: int):
    """Delete specific claim."""
    return {"message": f"Delete claim {claim_id} endpoint - to be implemented"}


@router.post("/{claim_id}/approve")
async def approve_claim(claim_id: int):
    """Approve expense claim (managers only)."""
    return {"message": f"Approve claim {claim_id} endpoint - to be implemented"}


@router.post("/{claim_id}/reject")
async def reject_claim(claim_id: int):
    """Reject expense claim (managers only)."""
    return {"message": f"Reject claim {claim_id} endpoint - to be implemented"}
