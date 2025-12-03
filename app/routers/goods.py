import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from ..db import crud
from ..db.models import Goods, RestockInference, Sales
from ..dependencies import DBSessionDependency, UserDependency
from ..schemas.goods import (
    GoodsCreate,
    GoodsUpdate,
    GoodsAllResponse,
    GoodsDetailResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["goods"])


@router.get("/api/goods/")
def get_goods(
    db: DBSessionDependency, user: UserDependency, limit: int = 50
) -> GoodsAllResponse:
    try:
        goods = crud.get_all_goods(db, user_id=user.id, limit=limit)
        return {"data": goods}
    except Exception as e:
        logging.error("Error fetching goods %s", e)
        raise HTTPException(status_code=400, detail="Error fetching goods")


@router.get("/api/goods/{goods_id}")
def get_goods_by_id(
    goods_id: UUID, db: DBSessionDependency, user: UserDependency
) -> GoodsDetailResponse:
    goods_detail = crud.get_goods_with_relations(db, goods_id=goods_id, user_id=user.id)
    resp = {"data": goods_detail}
    return resp


@router.post("/api/goods/")
def create_goods(db: DBSessionDependency, goods: GoodsCreate, user: UserDependency):
    try:
        db.add(Goods(**goods.model_dump(), user_id=user.id))
        db.commit()
    except Exception as e:
        logging.error("Error during goods creation %s", e)
        raise HTTPException(status_code=400, detail="Error during goods creation")
    return {"message": "Goods created successfully", "data": goods}


@router.put("/api/goods/{goods_id}")
def update_goods(
    goods_id: UUID,
    goods_update: GoodsUpdate,
    db: DBSessionDependency,
    user: UserDependency,
):
    db_goods = crud.get_goods_by_id(db, goods_id=goods_id, user_id=user.id)
    if db_goods is None:
        logging.error("Goods not found for id %s", goods_id)
        raise HTTPException(status_code=404, detail="Goods not found")
    updated_goods = crud.update_db_element(
        db=db, original_element=db_goods, element_update=goods_update
    )
    return updated_goods


@router.delete("/api/goods/{goods_id}")
def delete_goods(goods_id: UUID, db: DBSessionDependency, user: UserDependency):
    db_goods = crud.get_goods_by_id(db, user_id=user.id, goods_id=goods_id)
    if db_goods is None:
        logging.error("Goods not found for id %s", goods_id)
        raise HTTPException(status_code=404, detail="Goods not found")

    ri_q = select(RestockInference).where(RestockInference.goods_id == goods_id)
    for ri in db.exec(ri_q).all():
        db.delete(ri)

    sales_q = select(Sales).where(Sales.goods_id == goods_id)
    for sale in db.exec(sales_q).all():
        db.delete(sale)

    db.delete(db_goods)
    db.commit()
    return {"message": "Goods deleted successfully", "data": db_goods}


@router.get("/goods/search/")
def search_goods(
    query: str, db: DBSessionDependency, user: UserDependency
) -> GoodsAllResponse:
    try:
        q = db.exec(
            select(Goods).where(
                Goods.user_id == user.id,
                Goods.name.ilike(f"%{query}%"),
            )
        )
        return {"data": q.all()}
    except Exception as e:
        logging.error("Error searching goods %s", e)
        raise HTTPException(status_code=400, detail="Error searching goods")
