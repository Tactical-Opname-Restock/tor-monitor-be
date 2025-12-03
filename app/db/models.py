from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, DATE


class AuthSchemeModel(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: UUID = Field(default_factory=uuid4, primary_key=True)


class Sales(SQLModel, table=True):
    __tablename__ = "sales"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    goods_id: UUID = Field(foreign_key="goods.id", nullable=False)

    quantity: int = Field(default=0, nullable=False)
    sale_date: datetime = Field(sa_column=Column(DATE), default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)

    user: "User" = Relationship(back_populates="sales")
    goods: "Goods" = Relationship(back_populates="sales")


class RestockInference(SQLModel, table=True):
    __tablename__ = "restock_inference"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    goods_id: UUID = Field(foreign_key="goods.id", nullable=False)

    predicted_restock_date: List[datetime] = Field(
        sa_column=Column(ARRAY(DATE), nullable=False)
    )
    quantity_needed: List[int] = Field(sa_column=Column(ARRAY(INTEGER), nullable=False))
    total_quantity: int = Field(default=0, nullable=False)

    created_at: datetime = Field(default_factory=datetime.now)
    goods: "Goods" = Relationship(back_populates="restock_inferences")


class Goods(SQLModel, table=True):
    __tablename__ = "goods"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)

    name: str = Field(nullable=False)
    category: Optional[str] = Field(default=None, nullable=True)
    price: float = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    stock_quantity: int = Field(default=0, nullable=False)

    user: "User" = Relationship(back_populates="goods")
    sales: Optional[List[Sales]] = Relationship(back_populates="goods")
    restock_inferences: Optional[List[RestockInference]] = Relationship(
        back_populates="goods"
    )


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True, foreign_key="auth.users.id"
    )

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    goods: Optional[List[Goods]] = Relationship(back_populates="user")
    sales: Optional[List[Sales]] = Relationship(back_populates="user")
