from ..db import crud
from typing import Optional
from sqlmodel import Session
from uuid import UUID


def get_all_goods(
    db: Session,
    user_id: UUID,
    limit: int = 10,
    page_index: int = 1,
    q: Optional[str] = None,
) -> str:
    """
    Mengambil semua barang (goods) untuk user tertentu dan mengembalikan dalam format text list.

    Args:
        db: Database session
        limit: Jumlah item per halaman (default: 10)
        page_index: Halaman yang diinginkan (default: 1)
        q: Query pencarian nama atau kategori opsional

    Returns:
        String berisi text list dari semua goods
    """
    try:
        goods_list, total_count = crud.get_all_goods(
            db=db, user_id=user_id, limit=limit, page_index=page_index, q=q
        )

        # Format hasil ke dalam text list
        text_output = f"Total Barang: {total_count}\n"
        text_output += (
            f"Menampilkan halaman {page_index} (Items per halaman: {limit})\n"
        )
        text_output += "=" * 60 + "\n\n"

        for idx, good in enumerate(goods_list, 1):
            text_output += f"{idx}. {good.name}\n"
            text_output += f"   Kategori: {good.category or 'Tidak ada kategori'}\n"
            text_output += f"   Harga: Rp {good.price:,.0f}\n"
            text_output += f"   Stok: {good.stock_quantity} unit\n"
            text_output += (
                f"   Dibuat: {good.created_at.strftime('%d-%m-%Y %H:%M:%S')}\n"
            )
            text_output += "\n"

        return text_output

    except Exception as e:
        return f"Error mengambil data barang: {str(e)}"
