from typing import List
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, select
from sqlalchemy.orm import selectinload, joinedload

from .models import Goods, RestockInference, Sales

######################################################
# Generic CRUD operations
######################################################


def update_db_element(
    db: Session, original_element: SQLModel, element_update: BaseModel
) -> BaseModel:
    """Updates an element in database.
    Note that it doesn't take care of user ownership.
    """
    update_data = element_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(original_element, key, value)

    db.add(original_element)
    db.commit()
    db.refresh(original_element)

    return original_element


def delete_db_element(db: Session, element: SQLModel):
    """Deletes an element from database."""
    db.delete(element)
    db.commit()


######################################################
# Specific CRUD operations
######################################################


def get_all_goods(db: Session, user_id: UUID, limit: int) -> List[Goods]:
    """Returns all goods for a user."""
    q = select(Goods).where(Goods.user_id == user_id)
    if limit:
        q = q.limit(limit)
    db_goods = db.exec(q).all()
    if not db_goods:
        raise HTTPException(status_code=404, detail="Goods not found")

    return db_goods


def get_goods_by_id(db: Session, goods_id: UUID, user_id: UUID) -> Goods:
    """Returns a specific goods by its ID for a user."""
    db_goods = db.exec(
        select(Goods).where(Goods.id == goods_id, Goods.user_id == user_id)
    ).first()
    if not db_goods:
        raise HTTPException(status_code=404, detail="Goods not found")

    return db_goods


def get_goods_with_relations(db: Session, goods_id: UUID, user_id: UUID):
    """Returns a specific goods by its ID for a user, including its sales and restock inferences."""
    q = select(Goods).where(Goods.id == goods_id, Goods.user_id == user_id)
    result = db.exec(q).one_or_none()
    if result is None:
        raise HTTPException(status_code=404, detail="Goods not found")
    return result


def get_all_sales(db: Session, user_id: UUID):
    """Returns all sales for a user."""
    stmt = (
        select(Sales).where(Sales.user_id == user_id).options(selectinload(Sales.goods))
    )

    result = db.exec(stmt).all()
    return result


def get_sales_by_id(db: Session, sales_id: UUID, user_id: UUID) -> Sales:
    """Returns a specific sales by its ID for a user."""
    db_sales = db.exec(
        select(Sales).where(Sales.id == sales_id, Sales.user_id == user_id)
    ).first()
    if not db_sales:
        raise HTTPException(status_code=404, detail="Sales not found")

    return db_sales
