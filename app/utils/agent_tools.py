"""AI Agent tools untuk inventory dan sales management"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Session

from ..db import crud
from ..schemas.goods import GoodsUpdate
from ..schemas.sales import SalesUpdate


# ============ CONTEXT VALIDATION ============

def is_request_valid(prompt: str) -> bool:
    """
    Validate apakah request sesuai dengan konteks inventory/sales.
    Reject pertanyaan yang completely diluar domain.
    
    Returns:
        bool: True jika request valid, False jika diluar konteks
    """
    prompt_lower = prompt.lower()
    
    # Block obvious out-of-context requests
    blocked_keywords = [
        # Personal/political
        "politik", "agama", "kepercayaan", "konspirasi",
        # Entertainment
        "lagu", "musik", "film", "game", "tiktok", "instagram",
        # General knowledge yang bukan inventory
        "cuaca", "berita", "recipe", "resep masak", "liburan",
        # Inappropriate
        "hack", "illegal", "malware", "phishing", "scam",
    ]
    
    if any(keyword in prompt_lower for keyword in blocked_keywords):
        return False
    
    # Allow if contains relevant keywords
    allowed_keywords = [
        "barang", "inventory", "stok", "stock", "goods",
        "penjualan", "sales", "jual", "terjual", "laku",
        "forecast", "prediksi", "restock", "restok", "supplies",
        "harga", "price", "kategori", "category", "profit",
        "omset", "revenue", "laporan", "lapor", "cek",
    ]
    
    if any(keyword in prompt_lower for keyword in allowed_keywords):
        return True
    
    # If no clear keywords, be permissive but let agent filter further
    return True


# ============ GOODS/INVENTORY TOOLS ============

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
        user_id: User ID
        limit: Jumlah item per halaman (default: 10)
        page_index: Halaman yang diinginkan (default: 1)
        q: Query pencarian nama atau kategori opsional

    Returns:
        String berisi formatted list dari semua goods
    """
    try:
        goods_list, total_count = crud.get_all_goods(
            db=db, user_id=user_id, limit=limit, page_index=page_index, q=q
        )

        # Format hasil ke dalam text list
        text_output = f"📊 INVENTORY BARANG (Total: {total_count})\n"
        text_output += f"Halaman {page_index} • {limit} item per halaman\n"
        text_output += "=" * 70 + "\n\n"

        for idx, good in enumerate(goods_list, 1):
            # Determine stok status
            stok_status = "✅ OK"
            if good.stock_quantity <= 10:
                stok_status = "⚠️  RENDAH"
            if good.stock_quantity == 0:
                stok_status = "🔴 HABIS"

            text_output += f"{idx}. {good.name} {stok_status}\n"
            text_output += f"   ID: {good.id}\n"
            if good.category:
                text_output += f"   Kategori: {good.category}\n"
            text_output += f"   Harga: Rp {good.price:,.0f}\n"
            text_output += f"   Stok: {good.stock_quantity} unit\n"
            text_output += f"   Dibuat: {good.created_at.strftime('%d-%m-%Y')}\n\n"

        if total_count > limit:
            text_output += f"📄 Total halaman: {(total_count + limit - 1) // limit}\n"

        return text_output

    except Exception as e:
        return f"❌ Error mengambil data barang: {str(e)}"


def get_goods_detail(db: Session, user_id: UUID, goods_id: str) -> str:
    """
    Mengambil detail lengkap satu barang berdasarkan ID.
    
    Args:
        db: Database session
        user_id: User ID
        goods_id: UUID string dari barang
        
    Returns:
        String berisi detail lengkap barang
    """
    try:
        goods_uuid = UUID(goods_id)
        goods = crud.get_goods_with_relations(db, goods_id=goods_uuid, user_id=user_id)
        
        text_output = f"📦 DETAIL BARANG\n"
        text_output += "=" * 70 + "\n\n"
        text_output += f"Nama: {goods.name}\n"
        text_output += f"ID: {goods.id}\n"
        if goods.category:
            text_output += f"Kategori: {goods.category}\n"
        text_output += f"Harga Satuan: Rp {goods.price:,.0f}\n"
        text_output += f"Stok Tersedia: {goods.stock_quantity} unit\n"
        text_output += f"Dibuat: {goods.created_at.strftime('%d-%m-%Y %H:%M:%S')}\n"
        
        return text_output
        
    except ValueError:
        return f"❌ Format ID barang tidak valid"
    except Exception as e:
        return f"❌ Error mengambil detail barang: {str(e)}"


def add_goods(
    db: Session,
    user_id: UUID,
    name: str,
    category: Optional[str] = None,
    price: float = 0,
    stock_quantity: int = 0,
) -> str:
    """
    Menambah barang baru ke inventory.
    
    Args:
        db: Database session
        user_id: User ID
        name: Nama barang
        category: Kategori barang (optional)
        price: Harga satuan
        stock_quantity: Jumlah stok awal
        
    Returns:
        String konfirmasi penambahan barang
    """
    try:
        from ..db.models import Goods
        
        # Validasi
        if not name or len(name.strip()) < 2:
            return "❌ Nama barang minimal 2 karakter"
        if price < 0:
            return "❌ Harga tidak boleh negatif"
        if stock_quantity < 0:
            return "❌ Stok tidak boleh negatif"
        
        goods = Goods(
            name=name.strip(),
            category=category.strip() if category else None,
            price=float(price),
            stock_quantity=int(stock_quantity),
            user_id=user_id,
        )
        db.add(goods)
        db.commit()
        db.refresh(goods)
        
        text_output = f"✅ BARANG BERHASIL DITAMBAHKAN\n"
        text_output += f"Nama: {goods.name}\n"
        if goods.category:
            text_output += f"Kategori: {goods.category}\n"
        text_output += f"Harga: Rp {goods.price:,.0f}\n"
        text_output += f"Stok Awal: {goods.stock_quantity} unit\n"
        text_output += f"ID Barang: {goods.id}\n"
        
        return text_output
        
    except Exception as e:
        return f"❌ Error menambah barang: {str(e)}"


def update_goods(
    db: Session,
    user_id: UUID,
    goods_id: str,
    name: Optional[str] = None,
    category: Optional[str] = None,
    price: Optional[float] = None,
    stock_quantity: Optional[int] = None,
) -> str:
    """
    Mengubah data barang yang sudah ada.
    
    Args:
        db: Database session
        user_id: User ID
        goods_id: UUID string dari barang yang diubah
        name, category, price, stock_quantity: Field yang ingin diubah (optional)
        
    Returns:
        String konfirmasi perubahan
    """
    try:
        goods_uuid = UUID(goods_id)
        goods = crud.get_goods_by_id(db, goods_id=goods_uuid, user_id=user_id)
        
        # Validasi input
        if name is not None and (not name or len(name.strip()) < 2):
            return "❌ Nama barang minimal 2 karakter"
        if price is not None and price < 0:
            return "❌ Harga tidak boleh negatif"
        if stock_quantity is not None and stock_quantity < 0:
            return "❌ Stok tidak boleh negatif"
        
        # Buat update object
        update_data = {}
        if name is not None:
            update_data["name"] = name.strip()
        if category is not None:
            update_data["category"] = category.strip() if category else None
        if price is not None:
            update_data["price"] = float(price)
        if stock_quantity is not None:
            update_data["stock_quantity"] = int(stock_quantity)
        
        goods_update = GoodsUpdate(**update_data)
        updated = crud.update_db_element(db=db, original_element=goods, element_update=goods_update)
        
        text_output = f"✅ BARANG BERHASIL DIPERBARUI\n"
        text_output += f"Nama: {updated.name}\n"
        if updated.category:
            text_output += f"Kategori: {updated.category}\n"
        text_output += f"Harga: Rp {updated.price:,.0f}\n"
        text_output += f"Stok: {updated.stock_quantity} unit\n"
        
        return text_output
        
    except ValueError:
        return f"❌ Format ID barang tidak valid"
    except Exception as e:
        return f"❌ Error mengubah barang: {str(e)}"


def delete_goods(db: Session, user_id: UUID, goods_id: str) -> str:
    """
    Menghapus barang dari inventory.
    
    Args:
        db: Database session
        user_id: User ID
        goods_id: UUID string dari barang yang dihapus
        
    Returns:
        String konfirmasi penghapusan
    """
    try:
        goods_uuid = UUID(goods_id)
        goods = crud.get_goods_by_id(db, goods_id=goods_uuid, user_id=user_id)
        
        deleted = crud.delete_db_element(db=db, element=goods)
        
        return f"✅ Barang '{deleted.name}' berhasil dihapus dari inventory"
        
    except ValueError:
        return f"❌ Format ID barang tidak valid"
    except Exception as e:
        return f"❌ Error menghapus barang: {str(e)}"


# ============ SALES TOOLS ============

def get_all_sales(
    db: Session,
    user_id: UUID,
    limit: int = 20,
    page_index: int = 1,
    q: Optional[str] = None,
) -> str:
    """
    Mengambil semua transaksi penjualan.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Jumlah item per halaman (default: 20)
        page_index: Halaman yang diinginkan (default: 1)
        q: Query pencarian berdasarkan nama barang
        
    Returns:
        String berisi formatted list dari semua sales
    """
    try:
        sales_list, total_count = crud.get_all_sales(
            db=db, user_id=user_id, limit=limit, page_index=page_index, q=q
        )
        
        text_output = f"💰 HISTORY PENJUALAN (Total: {total_count})\n"
        text_output += f"Halaman {page_index} • {limit} item per halaman\n"
        text_output += "=" * 70 + "\n\n"
        
        total_profit = 0
        for idx, sale in enumerate(sales_list, 1):
            text_output += f"{idx}. {sale.goods.name if sale.goods else 'Barang Tidak Ada'}\n"
            text_output += f"   ID Penjualan: {sale.id}\n"
            text_output += f"   Tanggal: {sale.sale_date.strftime('%d-%m-%Y') if hasattr(sale.sale_date, 'strftime') else sale.sale_date}\n"
            text_output += f"   Qty: {sale.quantity} unit × Rp {sale.goods.price:,.0f}\n"
            text_output += f"   Total: Rp {sale.total_profit:,.0f}\n"
            text_output += f"   Dicatat: {sale.created_at.strftime('%d-%m-%Y %H:%M') if hasattr(sale.created_at, 'strftime') else sale.created_at}\n\n"
            total_profit += sale.total_profit
        
        text_output += f"💵 TOTAL OMSET: Rp {total_profit:,.0f}\n"
        
        if total_count > limit:
            text_output += f"📄 Total halaman: {(total_count + limit - 1) // limit}\n"
        
        return text_output
        
    except Exception as e:
        return f"❌ Error mengambil data penjualan: {str(e)}"


def get_sales_detail(db: Session, user_id: UUID, sales_id: str) -> str:
    """
    Mengambil detail lengkap satu transaksi penjualan.
    
    Args:
        db: Database session
        user_id: User ID
        sales_id: UUID string dari penjualan
        
    Returns:
        String berisi detail lengkap penjualan
    """
    try:
        sales_uuid = UUID(sales_id)
        sales = crud.get_sales_by_id(db, sales_id=sales_uuid, user_id=user_id)
        
        text_output = f"💳 DETAIL PENJUALAN\n"
        text_output += "=" * 70 + "\n\n"
        text_output += f"ID Penjualan: {sales.id}\n"
        text_output += f"Barang: {sales.goods.name if sales.goods else 'Tidak Ada'}\n"
        text_output += f"Tanggal: {sales.sale_date.strftime('%d-%m-%Y') if hasattr(sales.sale_date, 'strftime') else sales.sale_date}\n"
        text_output += f"Jumlah: {sales.quantity} unit\n"
        text_output += f"Harga Satuan: Rp {sales.goods.price:,.0f}\n"
        text_output += f"Total Profit: Rp {sales.total_profit:,.0f}\n"
        text_output += f"Dicatat: {sales.created_at.strftime('%d-%m-%Y %H:%M:%S')}\n"
        
        return text_output
        
    except ValueError:
        return f"❌ Format ID penjualan tidak valid"
    except Exception as e:
        return f"❌ Error mengambil detail penjualan: {str(e)}"


def add_sales(
    db: Session,
    user_id: UUID,
    goods_id: str,
    quantity: int,
    sale_date: Optional[str] = None,
) -> str:
    """
    Mencatat transaksi penjualan baru dan otomatis mengurangi stok barang.
    
    Args:
        db: Database session
        user_id: User ID
        goods_id: UUID string dari barang yang dijual
        quantity: Jumlah unit yang terjual
        sale_date: Tanggal penjualan (format: YYYY-MM-DD, default: hari ini)
        
    Returns:
        String konfirmasi penjualan
    """
    try:
        if quantity <= 0:
            return "❌ Jumlah penjualan harus > 0"
        
        goods_uuid = UUID(goods_id)
        
        # Set sale_date ke hari ini jika tidak diberikan
        if not sale_date:
            sale_date = datetime.now().date().isoformat()
        
        sale_data = {
            "goods_id": goods_uuid,
            "quantity": int(quantity),
            "sale_date": sale_date,
        }
        
        sale = crud.create_sales_with_stock_deduction(db=db, sales_data=sale_data, user_id=user_id)
        
        text_output = f"✅ PENJUALAN BERHASIL DICATAT\n"
        text_output += f"Barang: {sale.goods.name}\n"
        text_output += f"Tanggal: {sale.sale_date.strftime('%d-%m-%Y') if hasattr(sale.sale_date, 'strftime') else sale.sale_date}\n"
        text_output += f"Jumlah: {sale.quantity} unit\n"
        text_output += f"Total Penjualan: Rp {sale.total_profit:,.0f}\n"
        text_output += f"Stok {sale.goods.name} sekarang: {sale.goods.stock_quantity} unit\n"
        text_output += f"ID Penjualan: {sale.id}\n"
        
        return text_output
        
    except ValueError as e:
        if "invalid literal" in str(e):
            return f"❌ Format ID barang atau jumlah tidak valid"
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Error mencatat penjualan: {str(e)}"


def update_sales(
    db: Session,
    user_id: UUID,
    sales_id: str,
    quantity: Optional[int] = None,
    sale_date: Optional[str] = None,
) -> str:
    """
    Mengubah data transaksi penjualan yang sudah ada.
    
    Args:
        db: Database session
        user_id: User ID
        sales_id: UUID string dari penjualan
        quantity: Jumlah unit baru (optional)
        sale_date: Tanggal penjualan baru (optional)
        
    Returns:
        String konfirmasi perubahan
    """
    try:
        sales_uuid = UUID(sales_id)
        sales = crud.get_sales_by_id(db, sales_id=sales_uuid, user_id=user_id)
        
        if quantity is not None and quantity <= 0:
            return "❌ Jumlah penjualan harus > 0"
        
        update_data = {}
        if quantity is not None:
            update_data["quantity"] = int(quantity)
        if sale_date is not None:
            update_data["sale_date"] = sale_date
        
        sales_update = SalesUpdate(**update_data)
        updated = crud.update_db_element(db=db, original_element=sales, element_update=sales_update)
        
        text_output = f"✅ PENJUALAN BERHASIL DIPERBARUI\n"
        text_output += f"Barang: {updated.goods.name}\n"
        text_output += f"Tanggal: {updated.sale_date.strftime('%d-%m-%Y') if hasattr(updated.sale_date, 'strftime') else updated.sale_date}\n"
        text_output += f"Jumlah: {updated.quantity} unit\n"
        text_output += f"Total: Rp {updated.total_profit:,.0f}\n"
        
        return text_output
        
    except ValueError:
        return f"❌ Format ID penjualan tidak valid"
    except Exception as e:
        return f"❌ Error mengubah penjualan: {str(e)}"


def delete_sales(db: Session, user_id: UUID, sales_id: str) -> str:
    """
    Menghapus transaksi penjualan.
    
    Args:
        db: Database session
        user_id: User ID
        sales_id: UUID string dari penjualan yang dihapus
        
    Returns:
        String konfirmasi penghapusan
    """
    try:
        sales_uuid = UUID(sales_id)
        sales = crud.get_sales_by_id(db, sales_id=sales_uuid, user_id=user_id)
        
        deleted = crud.delete_db_element(db=db, element=sales)
        
        return f"✅ Penjualan '{deleted.goods.name if deleted.goods else 'Barang'}' berhasil dihapus"
        
    except ValueError:
        return f"❌ Format ID penjualan tidak valid"
    except Exception as e:
        return f"❌ Error menghapus penjualan: {str(e)}"


# ============ FORECAST TOOLS ============

def get_forecast_data(
    db: Session,
    user_id: UUID,
    goods_id: Optional[str] = None,
    day_forecast: int = 7,
) -> str:
    """
    Mengambil data forecast dan rekomendasi restock.
    
    Args:
        db: Database session
        user_id: User ID
        goods_id: UUID string dari barang spesifik (optional, untuk single forecast)
        day_forecast: Jumlah hari forecast (default: 7)
        
    Returns:
        String berisi forecast data dan rekomendasi restok
    """
    try:
        from ..routers.forecast import forecast
        
        text_output = f"📈 FORECAST & REKOMENDASI RESTOK\n"
        text_output += "=" * 70 + "\n\n"
        
        if goods_id:
            # Forecast untuk barang spesifik
            goods_uuid = UUID(goods_id)
            goods = crud.get_goods_by_id(db, goods_id=goods_uuid, user_id=user_id)
            sales_dataset = crud.get_sales_dataset_by_goods(db, goods_id=goods_uuid, user_id=user_id)
            
            if len(sales_dataset) < 7:
                return f"⚠️  Barang '{goods.name}' tidak memiliki cukup data penjualan (minimal 7 hari) untuk forecast. Data saat ini: {len(sales_dataset)} hari.\n\nStok sekarang: {goods.stock_quantity} unit"
            
            forecast_result = forecast(sales_dataset, day_forecast=day_forecast)
            
            text_output += f"Barang: {goods.name}\n"
            text_output += f"Stok Saat Ini: {goods.stock_quantity} unit\n"
            text_output += f"Harga: Rp {goods.price:,.0f}\n\n"
            
            if forecast_result:
                text_output += f"🔮 PREDIKSI {day_forecast} HARI KE DEPAN:\n"
                text_output += f"Total Prediksi Terjual: {forecast_result.get('total_sales', 0)} unit\n"
                text_output += f"Rata-rata per hari: {forecast_result.get('total_sales', 0) // day_forecast} unit\n\n"
                
                text_output += f"📦 REKOMENDASI RESTOK:\n"
                text_output += f"Minimal Restok: {forecast_result.get('min_restock_quantity', 0)} unit\n"
                text_output += f"Restok Optimal: {forecast_result.get('restock_quantity', 0)} unit\n"
                text_output += f"Maksimal Restok: {forecast_result.get('max_restock_quantity', 0)} unit\n"
                
                if forecast_result.get('goods_mae'):
                    text_output += f"Akurasi Model: {100 - forecast_result.get('goods_mae', 0):.1f}%\n"
                
                # Show predictions
                text_output += f"\n📅 PREDIKSI HARIAN:\n"
                for pred in forecast_result.get('predictions', [])[:7]:
                    text_output += f"  {pred.get('date')}: {pred.get('total_sales')} unit (±{pred.get('max_sales') - pred.get('total_sales')} unit)\n"
        else:
            # Top 10 low stock goods
            low_stock_goods = crud.get_top_low_stock_goods(db=db, user_id=user_id, limit=10)
            
            if not low_stock_goods:
                return "✅ Semua barang stoknya cukup. Tidak ada peringatan stok rendah."
            
            text_output += f"⚠️  TOP 10 BARANG DENGAN STOK TERENDAH:\n\n"
            
            for idx, goods in enumerate(low_stock_goods, 1):
                sales_dataset = crud.get_sales_dataset_by_goods(db, goods_id=goods.id, user_id=user_id)
                
                text_output += f"{idx}. {goods.name}\n"
                text_output += f"   Stok Saat Ini: {goods.stock_quantity} unit\n"
                
                if len(sales_dataset) >= 7:
                    try:
                        forecast_result = forecast(sales_dataset, day_forecast=day_forecast)
                        text_output += f"   Prediksi Terjual ({day_forecast} hari): {forecast_result.get('total_sales', 0)} unit\n"
                        text_output += f"   Rekomendasi Restok: {forecast_result.get('restock_quantity', 0)} unit\n"
                    except:
                        text_output += f"   (Data penjualan tidak cukup untuk forecast)\n"
                else:
                    text_output += f"   ⚠️  Data penjualan hanya {len(sales_dataset)} hari (minimal 7 untuk forecast)\n"
                text_output += "\n"
        
        return text_output
        
    except ValueError:
        return f"❌ Format ID barang tidak valid"
    except Exception as e:
        return f"❌ Error mengambil forecast: {str(e)}"

