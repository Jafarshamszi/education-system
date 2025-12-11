from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

router = APIRouter()


@router.get("/")
async def get_accounts(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all accounts with pagination
    """
    return {"message": "Get accounts endpoint - To be implemented"}


@router.get("/{account_id}")
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get account by ID
    """
    return {"message": f"Get account {account_id} - To be implemented"}