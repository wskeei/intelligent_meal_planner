from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import User
from ..schemas import (
    ShoppingListGenerateRequest,
    ShoppingListItemCreateRequest,
    ShoppingListItemUpdateRequest,
    ShoppingListResponse,
    ShoppingListSummaryResponse,
)
from ..services import shopping_list_service
from .auth import get_current_user

router = APIRouter(prefix="/shopping-lists", tags=["购物清单"])


@router.get("", response_model=list[ShoppingListSummaryResponse])
async def list_shopping_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.list_lists(db, current_user.id)


@router.get("/{shopping_list_id}", response_model=ShoppingListResponse)
async def get_shopping_list(
    shopping_list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.get_list(db, current_user.id, shopping_list_id)


@router.post("/generate", response_model=ShoppingListResponse)
async def generate_shopping_list(
    payload: ShoppingListGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.generate_from_weekly_plan(
        db,
        current_user.id,
        payload.weekly_plan_id,
        payload.name,
    )


@router.post("/{shopping_list_id}/items", response_model=ShoppingListResponse)
async def add_manual_item(
    shopping_list_id: int,
    payload: ShoppingListItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.add_manual_item(
        db,
        current_user.id,
        shopping_list_id,
        payload.ingredient_name,
        payload.display_amount,
        payload.category,
    )


@router.patch("/{shopping_list_id}/items/{item_id}", response_model=ShoppingListResponse)
async def update_item(
    shopping_list_id: int,
    item_id: int,
    payload: ShoppingListItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.update_item(
        db,
        current_user.id,
        shopping_list_id,
        item_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete("/{shopping_list_id}/items/{item_id}", response_model=ShoppingListResponse)
async def delete_item(
    shopping_list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.delete_item(
        db,
        current_user.id,
        shopping_list_id,
        item_id,
    )
