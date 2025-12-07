from datetime import datetime
import json
import logging
from os import environ
from typing import Optional
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
    add_sales,
    get_all_sales,
    get_sales_detail,
    delete_sales,
    is_request_valid,
)

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah AI Inventory & Sales Manager Assistant khusus untuk aplikasi manajemen barang dan penjualan UMKM.

TANGGUNG JAWAB ANDA:
- Membantu user mengelola barang/inventory (melihat, menambah, menghapus)
- Membantu user mencatat penjualan dengan otomatis mengurangi stok barang
- Memberikan laporan forecast/prediksi restock barang yang hampir habis
- Memberikan saran restok terbaik berdasarkan data penjualan
- Jika anda tidak tau produk yang dimaksud oleh user bisa menggunakan tools get_all_goods yang tersedia
- Pastikan jika tidak tau id produk pastikan menggunakan tools yang tersedia

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
        self.user_id = None
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.2,
            api_key=SecretStr(environ["GROQ_KEY"]),
            max_tokens=1024,
        )

        self.tools = self._setup_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
                ("assistant", "{agent_scratchpad}"),
            ]
        )

        self.agent = create_tool_calling_agent(
            llm=self.llm, tools=self.tools, prompt=prompt
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,
            max_execution_time=30,
            early_stopping_method="force",
        )

    def _setup_tools(self):
        """Setup semua tools yang tersedia untuk agent - simplified for LangChain compatibility"""
        tools = []

        def get_all_goods_tool(name=None) -> str:
            try:
                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                return get_all_goods(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    limit=5,
                    page_index=1,
                    q=name if name else None,
                )
            except Exception as e:
                logger.error(f"Error in get_all_goods: {str(e)}")
                return f"❌ Error mengambil data barang: {str(e)}"

        tools.append(
            Tool(
                name="get_all_goods",
                func=get_all_goods_tool,
                description="Mengambil daftar semua barang inventory. Params: name: str if you need filtering",
            )
        )

        def get_goods_detail_tool(goods_id: str = "") -> str:
            try:
                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                if not goods_id:
                    return "❌ Goods ID wajib diisi"
                return get_goods_detail(
                    db=self.db, user_id=UUID(self.user_id), goods_id=goods_id
                )
            except Exception as e:
                logger.error(f"Error in get_goods_detail: {str(e)}")
                return f"❌ Error mengambil detail barang: {str(e)}"

        tools.append(
            Tool(
                name="get_goods_detail",
                func=get_goods_detail_tool,
                description="Mengambil detail lengkap satu barang berdasarkan ID. Parameters: goods_id (UUID)",
            )
        )

        def add_goods_tool(
            tools_input,
        ) -> str:
            try:
                data = json.loads(tools_input)

                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                if not data["name"] or data["price"] <= 0:
                    return "❌ Name dan price wajib diisi dengan nilai valid"
                cat = (
                    data["category"]
                    if data["category"] and data["category"].strip()
                    else None
                )
                return add_goods(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    name=data["name"],
                    category=cat,
                    price=data["price"],
                    stock_quantity=data["stock_quantity"],
                )
            except Exception as e:
                logger.error(f"Error in add_goods: {str(e)}")
                return f"❌ Error menambah barang: {str(e)}"

        tools.append(
            Tool(
                name="add_goods",
                func=add_goods_tool,
                description="Menambah barang baru ke inventory. Parameters: name (wajib), price (wajib), stock_quantity (default 0), category (optional)",
            )
        )

        def delete_goods_tool(goods_id: str = "") -> str:
            try:
                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                if not goods_id:
                    return "❌ Goods ID wajib diisi"
                return delete_goods(
                    db=self.db, user_id=UUID(self.user_id), goods_id=goods_id
                )
            except Exception as e:
                logger.error(f"Error in delete_goods: {str(e)}")
                return f"❌ Error menghapus barang: {str(e)}"

        tools.append(
            Tool(
                name="delete_goods",
                func=delete_goods_tool,
                description="Menghapus barang dari inventory. Parameters: goods_id (UUID)",
            )
        )

        def get_all_sales_tool(name=None) -> str:
            try:
                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                return get_all_sales(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    limit=10,
                    page_index=1,
                    q=name,
                )
            except Exception as e:
                logger.error(f"Error in get_all_sales: {str(e)}")
                return f"❌ Error mengambil data penjualan: {str(e)}"

        tools.append(
            Tool(
                name="get_all_sales",
                func=get_all_sales_tool,
                description="Mengambil daftar semua transaksi penjualan. Gunakan untuk: melihat history penjualan, cek omset.",
            )
        )

        def get_sales_detail_tool(sales_id: str = "") -> str:
            try:
                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                if not sales_id:
                    return "❌ Sales ID wajib diisi"
                return get_sales_detail(
                    db=self.db, user_id=UUID(self.user_id), sales_id=sales_id
                )
            except Exception as e:
                logger.error(f"Error in get_sales_detail: {str(e)}")
                return f"❌ Error mengambil detail penjualan: {str(e)}"

        tools.append(
            Tool(
                name="get_sales_detail",
                func=get_sales_detail_tool,
                description="Mengambil detail lengkap satu transaksi penjualan. Parameters: sales_id (UUID)",
            )
        )

        def add_sales_tool(tool_input) -> str:
            try:
                data = json.loads(tool_input)

                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                if not data["goods_id"] or data["quantity"] <= 0:
                    return "❌ Goods ID dan quantity wajib diisi dengan nilai valid"
                date_v = (
                    data["sale_date"]
                    if data["sale_date"] and data["sale_date"].strip()
                    else str(datetime.now())
                )
                return add_sales(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    goods_id=data["goods_id"],
                    quantity=data["quantity"],
                    sale_date=date_v,
                )
            except Exception as e:
                logger.error(f"Error in add_sales: {str(e)}")
                return f"❌ Error mencatat penjualan: {str(e)}"

        tools.append(
            Tool(
                name="add_sales",
                func=add_sales_tool,
                description="Mencatat transaksi penjualan baru. Parameters: goods_id (wajib), quantity (wajib), sale_date (YYYY-MM-DD, optional)",
            )
        )

        def delete_sales_tool(sales_id: str = "") -> str:
            try:
                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                if not sales_id:
                    return "❌ Sales ID wajib diisi"
                return delete_sales(
                    db=self.db, user_id=UUID(self.user_id), sales_id=sales_id
                )
            except Exception as e:
                logger.error(f"Error in delete_sales: {str(e)}")
                return f"❌ Error menghapus penjualan: {str(e)}"

        tools.append(
            Tool(
                name="delete_sales",
                func=delete_sales_tool,
                description="Menghapus transaksi penjualan. Parameters: sales_id (UUID)",
            )
        )

        def get_forecast_tool(goods_id=None) -> str:
            try:
                if not self.db or not self.user_id:
                    return "❌ Database atau user ID tidak tersedia"
                return get_forecast_data(
                    db=self.db,
                    user_id=UUID(self.user_id),
                    goods_id=goods_id,
                    day_forecast=7,
                )
            except Exception as e:
                logger.error(f"Error in get_forecast: {str(e)}")
                return f"❌ Error mengambil forecast: {str(e)}"

        tools.append(
            Tool(
                name="get_forecast",
                func=get_forecast_tool,
                description="Mengambil prediksi forecast dan rekomendasi stok untuk barang yang hampir habis. Menampilkan top 10 barang dengan stok terendah. Berikan id jika ingin spesifik kepada suatu barang",
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
            output = response.get(
                "output", "Terjadi kesalahan saat memproses permintaan"
            )

            memory.append(HumanMessage(content=prompt))
            memory.append(AIMessage(content=output))

            # Keep only last 6 messages (3 exchanges)
            if len(memory) > 6:
                memory.pop(0)
                memory.pop(0)

            return output

        except Exception as e:
            logger.error(f"Error in agent chat: {str(e)}")
            return (
                f"Terjadi kesalahan: {str(e)}. Silakan coba lagi atau hubungi support."
            )
