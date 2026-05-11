from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_receipt():
    # Phase 2에서 구현
    return {"message": "upload endpoint - Phase 2에서 구현 예정"}
