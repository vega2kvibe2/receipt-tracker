from fastapi import APIRouter

router = APIRouter()


@router.get("/expenses")
async def get_expenses():
    # Phase 3에서 구현
    return []


@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    # Phase 3에서 구현
    return {"message": f"{expense_id} 삭제 예정"}


@router.put("/expenses/{expense_id}")
async def update_expense(expense_id: str):
    # Phase 3에서 구현
    return {"message": f"{expense_id} 수정 예정"}
