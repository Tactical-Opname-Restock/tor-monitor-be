import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from ..db import crud
from ..db.models import Goods, Sales
from ..dependencies import DBSessionDependency, UserDependency
from ..schemas.sales import SalesCreate, SalesUpdate, SalesBase, SalesAllResponse
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sales"])


@router.get("/api/sales/")
def get_sales(db: DBSessionDependency, user: UserDependency) -> SalesAllResponse:
    try:
        sales = crud.get_all_sales(db, user_id=user.id)
        return {"data": sales}
    except Exception as e:
        logging.error("Error fetching sales %s", e)
        raise HTTPException(status_code=400, detail="Error fetching sales")


@router.post("/api/sales/")
def create_sales(db: DBSessionDependency, sales: SalesCreate, user: UserDependency):
    try:
        db.add(Sales(**sales.model_dump(), user_id=user.id))
        db.commit()
    except Exception as e:
        logging.error("Error during sales creation %s", e)
        raise HTTPException(status_code=400, detail="Error during sales creation")
    return {"message": "Sales created successfully", "data": sales}


@router.put("/api/sales/{sales_id}")
def update_sales(
    sales_id: UUID,
    sales_update: SalesUpdate,
    db: DBSessionDependency,
    user: UserDependency,
):
    db_sales = crud.get_sales_by_id(db, sales_id=sales_id, user_id=user.id)
    if db_sales is None:
        logging.error("Goods not found for id %s", sales_id)
        raise HTTPException(status_code=404, detail="Goods not found")
    updated_sales = crud.update_db_element(
        db=db, original_element=db_sales, element_update=sales_update
    )
    return updated_sales


@router.delete("/api/sales/{sales_id}")
def delete_sales(sales_id: UUID, db: DBSessionDependency, user: UserDependency):
    db_sales = crud.get_sales_by_id(db, user_id=user.id, sales_id=sales_id)
    if db_sales is None:
        logging.error("Goods not found for id %s", sales_id)
        raise HTTPException(status_code=404, detail="Goods not found")

    db.delete(db_sales)
    db.commit()
    return {"message": "Sales deleted successfully", "data": db_sales}


@router.get("/sales/filter/")
def search_sales(
    db: DBSessionDependency,
    user: UserDependency,
    goods_name: Optional[str] = None,
    datestart: Optional[datetime] = None,
    dateend: Optional[datetime] = None,
) -> SalesAllResponse:
    try:
        filters = [Sales.user_id == user.id]
        if goods_name:
            filters.append(Goods.name.ilike(f"%{goods_name}%"))
        if datestart:
            filters.append(Sales.sale_date >= datestart)
        if dateend:
            filters.append(Sales.sale_date <= dateend)
        sales = db.exec(
            select(Sales).join(Goods, Sales.goods_id == Goods.id).where(*filters)
        ).all()
        return {"data": sales}
    except Exception as e:
        logging.error("Error searching sales %s", e)
        raise HTTPException(status_code=400, detail="Error searching sales")
