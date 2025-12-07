import json
import logging
from os import environ
from typing import Any, Dict, Optional
from uuid import UUID

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.schema import AIMessage, HumanMessage, SystemMessage
from langchain_classic.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import SecretStr
from sqlmodel import Session

from ..utils.agent_tools import (
    add_goods,
    delete_goods,
    get_all_goods,
    get_forecast_data,
    get_goods_detail,
    update_goods,
    add_sales,
    get_all_sales,
    get_sales_detail,
    update_sales,
    delete_sales,
    is_request_valid,
)

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah AI Inventory & Sales Manager Assistant khusus untuk aplikasi manajemen barang dan penjualan UMKM.

TANGGUNG JAWAB ANDA:
- Membantu user mengelola barang/inventory (melihat, menambah, mengubah, menghapus)
- Membantu user mencatat penjualan dengan otomatis mengurangi stok barang
- Memberikan laporan forecast/prediksi restock barang yang hampir habis
- Memberikan saran restok terbaik berdasarkan data penjualan

BATASAN KETAT:
- HANYA membahas topik inventory, penjualan, dan forecast barang
- TOLAK pertanyaan yang diluar konteks bisnis inventory/penjualan
- Jangan memberikan informasi sensitif di luar domain ini
- Jika user bertanya hal yang tidak relevan, ingatkan dengan sopan untuk fokus pada manajemen barang/penjualan

INSTRUKSI PENGGUNAAN TOOLS:
- Selalu gunakan tools yang tersedia untuk operasi data
- Kembalikan hasil dalam bahasa Indonesia yang mudah dipahami
- Berikan konteks dan saran bermanfaat berdasarkan data
- Format angka dengan pemisah ribuan (Rp X.XXX)
- Jangan membuat data fiktif - gunakan tools untuk data real

TONE: Profesional, helpful, dan ramah untuk UMKM yang jarang teknologi."""


class AgentService:
    def __init__(self, db: Optional[Session] = None):
        self.user_memories = {}
        self.db = db
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.2,
            api_key=SecretStr(environ["GROQ_KEY"]),
            max_tokens=2048,
        )

        # Setup tools untuk agent
        self.tools = self._setup_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
                ("assistant", "{agent_scratchpad}"),
            ]
        )

        # bikin agent yang bisa call tool
        self.agent = create_tool_calling_agent(
            llm=self.llm, tools=self.tools, prompt=prompt
        )

        # bungkus agent supaya bisa diinvoke
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
        )

    def _setup_tools(self):
        """Setup semua tools yang tersedia untuk agent"""
        tools = []

        # ========== GOODS/INVENTORY TOOLS ==========

        def get_all_goods_wrapper(
            limit: int = 10, page_index: int = 1, search: Optional[str] = None
        ) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return get_all_goods(
                    db=self.db, user_id=UUID(self.user_id), limit=limit, page_index=page_index, q=search
                )
            except Exception as e:
                return f"Error mengambil data barang: {str(e)}"

        tools.append(
            Tool(
                name="get_all_goods",
                func=get_all_goods_wrapper,
                description="Mengambil daftar semua barang inventory. Gunakan untuk: melihat semua barang, cek stok, search barang. Parameters: limit (jumlah per halaman, default 10), page (halaman, default 1), search (optional, cari berdasarkan nama)",
            )
        )

        def get_goods_detail_wrapper(goods_id: str) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return get_goods_detail(db=self.db, user_id=UUID(self.user_id), goods_id=goods_id)
            except Exception as e:
                return f"Error mengambil detail barang: {str(e)}"

        tools.append(
            Tool(
                name="get_goods_detail",
                func=get_goods_detail_wrapper,
                description="Mengambil detail lengkap satu barang berdasarkan ID. Parameters: goods_id (UUID dari barang)",
            )
        )

        def add_goods_wrapper(name: str, category: Optional[str] = None, price: float = 0, stock: int = 0) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return add_goods(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    name=name,
                    category=category,
                    price=price,
                    stock_quantity=stock,
                )
            except Exception as e:
                return f"Error menambah barang: {str(e)}"

        tools.append(
            Tool(
                name="add_goods",
                func=add_goods_wrapper,
                description="Menambah barang baru ke inventory. Gunakan untuk: mencatat barang baru. Parameters: name (nama barang, wajib), category (kategori, optional), price (harga satuan, wajib), stock (jumlah stok awal, default 0)",
            )
        )

        def update_goods_wrapper(goods_id: str, name: Optional[str] = None, category: Optional[str] = None, price: Optional[float] = None, stock: Optional[int] = None) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return update_goods(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    goods_id=goods_id,
                    name=name,
                    category=category,
                    price=price,
                    stock_quantity=stock,
                )
            except Exception as e:
                return f"Error mengubah barang: {str(e)}"

        tools.append(
            Tool(
                name="update_goods",
                func=update_goods_wrapper,
                description="Mengubah data barang yang sudah ada. Gunakan untuk: ubah nama, kategori, harga, atau stok barang. Parameters: goods_id (UUID barang yang diubah), name (opsional), category (opsional), price (opsional), stock (opsional)",
            )
        )

        def delete_goods_wrapper(goods_id: str) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return delete_goods(db=self.db, user_id=UUID(self.user_id), goods_id=goods_id)
            except Exception as e:
                return f"Error menghapus barang: {str(e)}"

        tools.append(
            Tool(
                name="delete_goods",
                func=delete_goods_wrapper,
                description="Menghapus barang dari inventory. HATI-HATI: tidak bisa dibatalkan. Parameters: goods_id (UUID barang yang dihapus)",
            )
        )

        # ========== SALES TOOLS ==========

        def get_all_sales_wrapper(limit: int = 20, page: int = 1, search: Optional[str] = None) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return get_all_sales(
                    db=self.db, user_id=UUID(self.user_id), limit=limit, page=page, q=search
                )
            except Exception as e:
                return f"Error mengambil data penjualan: {str(e)}"

        tools.append(
            Tool(
                name="get_all_sales",
                func=get_all_sales_wrapper,
                description="Mengambil daftar semua transaksi penjualan. Gunakan untuk: melihat history penjualan, cek omset. Parameters: limit (default 20), page (default 1), search (cari berdasarkan nama barang, optional)",
            )
        )

        def get_sales_detail_wrapper(sales_id: str) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return get_sales_detail(db=self.db, user_id=UUID(self.user_id), sales_id=sales_id)
            except Exception as e:
                return f"Error mengambil detail penjualan: {str(e)}"

        tools.append(
            Tool(
                name="get_sales_detail",
                func=get_sales_detail_wrapper,
                description="Mengambil detail lengkap satu transaksi penjualan. Parameters: sales_id (UUID dari penjualan)",
            )
        )

        def add_sales_wrapper(goods_id: str, quantity: int, sale_date: str) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return add_sales(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    goods_id=goods_id,
                    quantity=quantity,
                    sale_date=sale_date,
                )
            except Exception as e:
                return f"Error mencatat penjualan: {str(e)}"

        tools.append(
            Tool(
                name="add_sales",
                func=add_sales_wrapper,
                description="Mencatat transaksi penjualan baru dan otomatis mengurangi stok barang. Parameters: goods_id (UUID barang yang dijual), quantity (jumlah unit terjual), sale_date (tanggal penjualan, format: YYYY-MM-DD atau hari ini jika kosong)",
            )
        )

        def update_sales_wrapper(sales_id: str, quantity: Optional[int] = None, sale_date: Optional[str] = None) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return update_sales(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    sales_id=sales_id,
                    quantity=quantity,
                    sale_date=sale_date,
                )
            except Exception as e:
                return f"Error mengubah penjualan: {str(e)}"

        tools.append(
            Tool(
                name="update_sales",
                func=update_sales_wrapper,
                description="Mengubah data transaksi penjualan yang sudah ada. Parameters: sales_id (UUID penjualan), quantity (opsional, jumlah unit), sale_date (opsional, tanggal)",
            )
        )

        def delete_sales_wrapper(sales_id: str) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return delete_sales(db=self.db, user_id=UUID(self.user_id), sales_id=sales_id)
            except Exception as e:
                return f"Error menghapus penjualan: {str(e)}"

        tools.append(
            Tool(
                name="delete_sales",
                func=delete_sales_wrapper,
                description="Menghapus transaksi penjualan. Parameters: sales_id (UUID penjualan yang dihapus)",
            )
        )

        # ========== FORECAST TOOLS ==========

        def get_forecast_wrapper(goods_id: Optional[str] = None, days: int = 7) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            try:
                return get_forecast_data(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    goods_id=goods_id,
                    day_forecast=days,
                )
            except Exception as e:
                return f"Error mengambil forecast: {str(e)}"

        tools.append(
            Tool(
                name="get_forecast",
                func=get_forecast_wrapper,
                description="Mengambil prediksi forecast dan rekomendasi stok untuk barang yang hampir habis. Gunakan untuk: lihat top 10 barang dengan stok terendah dan prediksi sales nya, atau forecast spesifik barang. Parameters: goods_id (optional, untuk forecast barang spesifik), days (jumlah hari forecast, default 7)",
            )
        )

        return tools

    def get_memory(self, user_id: str):
        if user_id not in self.user_memories:
            self.user_memories[user_id] = []
        return self.user_memories[user_id]

    def chat(self, db: Session, user_id: str, prompt: str) -> str:
        """Handle chat request dengan validasi konteks ketat"""
        # Cek apakah request valid dan dalam konteks
        if not is_request_valid(prompt):
            return (
                "Maaf, saya hanya bisa membantu dengan manajemen barang dan penjualan. "
                "Silakan tanyakan tentang inventory, sales, atau forecast barang Anda. 😊"
            )

        self.db = db
        self.user_id = user_id
        memory = self.get_memory(user_id)

        try:
            messages = (
                [SystemMessage(content=SYSTEM_PROMPT)]
                + memory
                + [HumanMessage(content=prompt)]
            )

            response = self.agent_executor.invoke({"input": messages})
            output = response.get("output", "Terjadi kesalahan saat memproses permintaan")

            memory.append(HumanMessage(content=prompt))
            memory.append(AIMessage(content=output))

            # Keep only last 6 messages (3 exchanges)
            if len(memory) > 6:
                memory.pop(0)
                memory.pop(0)

            return output

        except Exception as e:
            logger.error(f"Error in agent chat: {str(e)}")
            return f"Terjadi kesalahan: {str(e)}. Silakan coba lagi atau hubungi support."
