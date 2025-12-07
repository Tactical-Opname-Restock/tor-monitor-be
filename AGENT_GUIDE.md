# AI Agent untuk Inventory & Sales Management

## Overview

Agent AI ini dirancang khusus untuk membantu UMKM mengelola inventory dan penjualan mereka melalui chat interface. Agent memiliki kemampuan untuk:

- **Manajemen Barang**: Melihat, menambah, mengubah, menghapus barang
- **Pencatatan Penjualan**: Mencatat penjualan dan otomatis mengurangi stok
- **Forecast & Prediksi**: Memberikan prediksi penjualan dan rekomendasi restok
- **Saran Terbaik**: Menganalisis data dan memberikan rekomendasi berdasarkan pola penjualan

## Fitur Utama

### 1. Inventory Management

**Melihat Semua Barang**
```
User: "Tunjukin barang apa aja yang ada"
Agent: Menampilkan daftar lengkap dengan stok, kategori, harga
```

**Melihat Detail Barang Spesifik**
```
User: "Cek detail barang yang id nya [uuid]"
Agent: Menampilkan informasi lengkap satu barang
```

**Menambah Barang Baru**
```
User: "Tambahkan barang baru: Beras premium, kategori pangan, harga 15000, stok 50 unit"
Agent: Menambahkan barang dan menampilkan konfirmasi dengan ID
```

**Mengubah Data Barang**
```
User: "Ubah harga barang [id] menjadi 20000 dan tambah stok 10 unit"
Agent: Memperbarui data barang sesuai permintaan
```

**Menghapus Barang**
```
User: "Hapus barang [id] dari inventory"
Agent: Menghapus barang dengan konfirmasi
```

### 2. Sales Management

**Melihat History Penjualan**
```
User: "Berapa omset penjualan ku bulan ini?"
Agent: Menampilkan daftar penjualan dengan total omset
```

**Mencatat Penjualan Baru**
```
User: "Saya jual barang [id] sebanyak 5 unit hari ini"
Agent: Mencatat penjualan dan otomatis mengurangi stok barang
```

**Mengubah Data Penjualan**
```
User: "Koreksi penjualan [id] menjadi 10 unit"
Agent: Memperbarui data penjualan
```

### 3. Forecast & Rekomendasi

**Melihat Top 10 Barang Stok Rendah**
```
User: "Barang apa aja yang harus aku restok?"
Agent: Menampilkan top 10 dengan prediksi penjualan dan rekomendasi restok
```

**Forecast Barang Spesifik**
```
User: "Prediksi penjualan barang [id] untuk 7 hari ke depan"
Agent: Menampilkan prediksi harian dan rekomendasi jumlah restok
```

## Arsitektur & Implementasi

### System Prompt

Agent menggunakan system prompt ketat yang:
- Membatasi topik hanya ke inventory, penjualan, dan forecast
- Menolak pertanyaan diluar konteks bisnis
- Instruksi untuk format output yang user-friendly
- Mendorong penggunaan tools untuk data real

### Tools yang Tersedia

#### Goods/Inventory Tools
- `get_all_goods`: Mengambil daftar barang dengan search & pagination
- `get_goods_detail`: Detail lengkap satu barang
- `add_goods`: Menambah barang baru
- `update_goods`: Mengubah data barang
- `delete_goods`: Menghapus barang

#### Sales Tools
- `get_all_sales`: Mengambil history penjualan dengan search & pagination
- `get_sales_detail`: Detail lengkap satu transaksi
- `add_sales`: Mencatat penjualan (auto-deduksi stok)
- `update_sales`: Mengubah data penjualan
- `delete_sales`: Menghapus penjualan

#### Forecast Tools
- `get_forecast`: Forecast untuk top 10 barang stok rendah atau barang spesifik

### Context Validation

Fungsi `is_request_valid()` mengecek apakah request relevan dengan konteks:
- **Blocked keywords**: Politik, agama, hiburan, berita, hack, illegal, dll
- **Allowed keywords**: Barang, inventory, penjualan, forecast, harga, stok, dll
- Permissive untuk keyword yang tidak jelas (let agent filter)

### Memory Management

Agent mempertahankan conversation history per user:
- Menyimpan maksimal 6 pesan terakhir (3 exchange)
- Memory di-reset saat server restart
- Membantu agent memahami konteks percakapan sebelumnya

## Integrasi dengan Existing Code

### Database & CRUD
Agent menggunakan existing CRUD functions dari `app/db/crud.py`:
```python
# Goods operations
get_all_goods()
get_goods_by_id()
get_goods_with_relations()
get_top_low_stock_goods()

# Sales operations
get_all_sales()
get_sales_by_id()
create_sales_with_stock_deduction()
update_db_element()
delete_db_element()

# Forecast operations
get_sales_dataset_by_goods()
create_restock_inference()
get_restock_inference_by_goods_and_date()
```

### Services & Models
Agent mengintegrasikan dengan:
- `app/services/forecast.py`: Model prediksi penjualan
- `app/db/models.py`: SQLModel entities (Goods, Sales, etc)
- `app/schemas/`: Pydantic models untuk validation

## Output Format

### Goods Output
```
📊 INVENTORY BARANG (Total: 10)
Halaman 1 • 10 item per halaman
======================================================================

1. Beras Premium ✅ OK
   ID: uuid-xxx
   Kategori: Pangan
   Harga: Rp 15.000
   Stok: 50 unit
   Dibuat: 07-12-2025
```

### Sales Output
```
💰 HISTORY PENJUALAN (Total: 5)
Halaman 1 • 20 item per halaman
======================================================================

1. Beras Premium
   ID Penjualan: uuid-xxx
   Tanggal: 07-12-2025
   Qty: 5 unit × Rp 15.000
   Total: Rp 75.000
   Dicatat: 07-12-2025 14:30

💵 TOTAL OMSET: Rp 75.000
```

### Forecast Output
```
📈 FORECAST & REKOMENDASI RESTOK
======================================================================

⚠️  TOP 10 BARANG DENGAN STOK TERENDAH:

1. Beras Premium
   Stok Saat Ini: 5 unit
   Prediksi Terjual (7 hari): 21 unit
   Rekomendasi Restok: 30 unit

2. Garam Halus
   Stok Saat Ini: 2 unit
   Prediksi Terjual (7 hari): 10 unit
   Rekomendasi Restok: 15 unit
```

## Error Handling

Agent menangani berbagai error dengan graceful:
- Invalid UUID format
- Barang/penjualan tidak ditemukan
- Insufficient stock
- Database errors
- Semua error dikomunikasikan dalam bahasa user-friendly

## Limitations & Future Improvements

### Current Limitations
1. Memory hanya di-server (reset saat restart)
2. Forecast butuh minimal 7 hari data penjualan
3. Max 1024 tokens per response (dapat ditingkatkan)

### Future Improvements
1. Persist conversation history ke database
2. Multi-language support
3. Advanced analytics dashboard
4. Real-time inventory alerts
5. Supplier integration
6. Budget optimization
7. Trend analysis & seasonality detection

## Development Notes

### Testing
```bash
# Run all tests
uv run pytest tests/ -q

# Run specific test
uv run pytest tests/test_chat.py -xvs
```

### Running Agent Locally
```bash
# Start server dengan auto-reload
uv run uvicorn app.main:app --reload

# Test agent via chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chat_message": "Tunjukin barang apa aja"}'
```

## Configuration

### System Prompt Tuning
Edit `SYSTEM_PROMPT` di `app/services/agent.py` untuk:
- Mengubah tone/personality
- Menambah instruksi baru
- Menyesuaikan dengan kebutuhan domain spesifik

### Tool Parameters
Setiap tool dapat dikonfigurasi di `_setup_tools()`:
- Default values
- Descriptions
- Parameter documentation

### LLM Settings
```python
# Model & temperature dapat diubah
self.llm = ChatGroq(
    model="openai/gpt-oss-120b",  # Model name
    temperature=0.2,               # Lower = lebih deterministic
    max_tokens=2048,               # Panjang response max
)
```

## Support & Troubleshooting

### Agent tidak merespons
1. Check GROQ_KEY di .env
2. Verify database connection
3. Check server logs untuk error details

### Tools tidak berfungsi
1. Verify user_id valid
2. Check data di database
3. Run tests untuk isolate issue

### Memory issues
1. Conversation history di-reset saat server restart
2. Untuk persistent memory, integrate dengan database

## References

- **Agent Service**: `app/services/agent.py`
- **Agent Tools**: `app/utils/agent_tools.py`
- **Chat Router**: `app/routers/chat.py`
- **CRUD Functions**: `app/db/crud.py`
- **Tests**: `tests/test_chat.py`
