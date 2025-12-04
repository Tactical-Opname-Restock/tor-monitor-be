from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, select
from sqlalchemy import or_, func, cast
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import DATE as SA_DATE

from .models import Goods, Sales

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


def get_all_goods(
    db: Session, user_id: UUID, limit: int, page_index: int, q: Optional[str] = None
) -> Tuple[List[Goods], int]:
    """Returns all goods for a user with optional search query.

    Args:
        db: Database session
        user_id: User ID filter
        limit: Number of items per page
        page_index: Page number (1-indexed)
        q: Search query to filter by name or category

    Returns:
        Tuple of (goods list, total count)
    """
    query = select(Goods).where(Goods.user_id == user_id)

    if q:
        search_filter = or_(Goods.name.ilike(f"%{q}%"), Goods.category.ilike(f"%{q}%"))
        query = query.where(search_filter)

    count_query = select(Goods).where(Goods.user_id == user_id)
    if q:
        search_filter = or_(Goods.name.ilike(f"%{q}%"), Goods.category.ilike(f"%{q}%"))
        count_query = count_query.where(search_filter)

    total_count = len(db.exec(count_query).all())

    if limit:
        query = query.offset((page_index - 1) * limit).limit(limit)

    db_goods = list(db.exec(query).all())
    if not db_goods:
        raise HTTPException(status_code=404, detail="Goods not found")

    return db_goods, total_count


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


def get_all_sales(
    db: Session,
    user_id: UUID,
    limit: int = 20,
    page_index: int = 1,
    q: Optional[str] = None,
) -> Tuple[List[Sales], int]:
    """Returns all sales for a user with optional search query on goods name.

    Args:
        db: Database session
        user_id: User ID filter
        limit: Number of items per page
        page_index: Page number (1-indexed)
        q: Search query to filter by goods name

    Returns:
        Tuple of (sales list, total count)
    """
    query = (
        select(Sales).where(Sales.user_id == user_id).options(selectinload(Sales.goods))
    )

    # Add search filter if query is provided
    if q:
        search_filter = Goods.name.ilike(f"%{q}%")
        query = query.join(Goods).where(search_filter)

    # Get total count before pagination
    count_query = select(Sales).where(Sales.user_id == user_id)
    if q:
        count_query = count_query.join(Goods).where(Goods.name.ilike(f"%{q}%"))

    total_count = len(db.exec(count_query).all())

    # Apply pagination
    if limit:
        query = query.offset((page_index - 1) * limit).limit(limit)

    result = list(db.exec(query).all())
    if not result:
        raise HTTPException(status_code=404, detail="Sales not found")

    return result, total_count


def get_sales_by_id(db: Session, sales_id: UUID, user_id: UUID) -> Sales:
    """Returns a specific sales by its ID for a user."""
    db_sales = db.exec(
        select(Sales).where(Sales.id == sales_id, Sales.user_id == user_id)
    ).first()
    if not db_sales:
        raise HTTPException(status_code=404, detail="Sales not found")

    return db_sales


def create_sales_with_stock_deduction(
    db: Session, sales_data: dict, user_id: UUID
) -> Sales:
    """Creates a sales record and deducts stock from goods.

    Args:
        db: Database session
        sales_data: Dictionary with goods_id, quantity, sale_date
        user_id: User ID for ownership validation

    Returns:
        Created Sales object with total_profit calculated

    Raises:
        HTTPException: If goods not found, insufficient stock, or other errors
    """
    goods_id = sales_data.get("goods_id")
    quantity = sales_data.get("quantity")

    # Get goods to validate stock
    goods = db.exec(
        select(Goods).where(Goods.id == goods_id, Goods.user_id == user_id)
    ).first()

    if not goods:
        raise HTTPException(status_code=404, detail="Goods not found")

    # Validate sufficient stock
    if goods.stock_quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {goods.stock_quantity}, Requested: {quantity}",
        )

    # Calculate total profit (price x quantity)
    total_profit = goods.price * quantity

    # Deduct stock from goods
    goods.stock_quantity -= quantity
    db.add(goods)

    # Create sales record with total_profit
    new_sales = Sales(**sales_data, user_id=user_id, total_profit=total_profit)
    db.add(new_sales)
    db.commit()
    db.refresh(new_sales)

    return new_sales


######################################################
# Dashboard CRUD operations
######################################################


def get_top_low_stock_goods(db: Session, user_id: UUID, limit: int = 10) -> List[Goods]:
    """Returns top N goods with lowest stock quantity.

    Args:
        db: Database session
        user_id: User ID filter
        limit: Number of items to return (default 10)

    Returns:
        List of Goods ordered by stock_quantity ascending
    """
    query = (
        select(Goods)
        .where(Goods.user_id == user_id)
        .order_by(Goods.stock_quantity.asc())
        .limit(limit)
    )
    goods = db.exec(query).all()
    return list(goods) if goods else []


def get_sales_chart_data(
    db: Session, user_id: UUID, year: int, month: int
) -> List[dict]:
    """Returns sales data aggregated by date for chart.

    Args:
        db: Database session
        user_id: User ID filter
        year: Year to filter
        month: Month to filter

    Returns:
        List of dicts with date and total_sales
    """

    # Query sales for specific month
    query = (
        select(
            cast(Sales.sale_date, SA_DATE).label("date"),
            func.sum(Sales.total_profit).label("total_sales"),
        )
        .where(
            Sales.user_id == user_id,
            func.extract("year", Sales.sale_date) == year,
            func.extract("month", Sales.sale_date) == month,
        )
        .group_by(cast(Sales.sale_date, SA_DATE))
        .order_by(cast(Sales.sale_date, SA_DATE))
    )

    results = db.exec(query).all()

    # Convert to list of dicts
    chart_data = []
    for date_val, total in results:
        chart_data.append(
            {"date": str(date_val), "total_sales": float(total) if total else 0.0}
        )

    return chart_data


def get_monthly_revenue(db: Session, user_id: UUID, year: int, month: int) -> float:
    """Returns total revenue for a specific month.

    Args:
        db: Database session
        user_id: User ID filter
        year: Year to filter
        month: Month to filter

    Returns:
        Total revenue (sum of total_profit)
    """

    query = select(func.sum(Sales.total_profit)).where(
        Sales.user_id == user_id,
        func.extract("year", Sales.sale_date) == year,
        func.extract("month", Sales.sale_date) == month,
    )

    result = db.exec(query).first()
    return float(result) if result else 0.0


def get_top_selling_item(
    db: Session, user_id: UUID, year: int, month: int
) -> Optional[dict]:
    """Returns the top selling item (by quantity) for a specific month.

    Args:
        db: Database session
        user_id: User ID filter
        year: Year to filter
        month: Month to filter

    Returns:
        Dict with name and total_quantity_sold, or None if no sales
    """

    query = (
        select(
            Goods.name,
            func.sum(Sales.quantity).label("total_quantity"),
            func.sum(Sales.total_profit).label("total_profit"),
        )
        .join(Sales, Sales.goods_id == Goods.id)
        .where(
            Sales.user_id == user_id,
            func.extract("year", Sales.sale_date) == year,
            func.extract("month", Sales.sale_date) == month,
        )
        .group_by(Goods.name)
        .order_by(func.sum(Sales.quantity).desc())
        .limit(1)
    )

    result = db.exec(query).first()

    if result:
        return {
            "name": result[0],
            "total_quantity_sold": int(result[1]),
            "total_profit": float(result[2]) if result[2] else 0.0,
        }

    return None
