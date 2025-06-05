from fastapi import APIRouter

router = APIRouter(tags=["v1"])


@router.get("/")
async def root_v1():
    """
    Root endpoint for API v1
    """
    return {"version": "v1", "message": "Welcome to API v1"}
