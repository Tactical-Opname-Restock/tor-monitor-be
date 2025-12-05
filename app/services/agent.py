from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.tools import Tool
from langchain_classic.schema import SystemMessage, HumanMessage, AIMessage
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from dotenv import load_dotenv
from os import environ
from sqlmodel import Session
from uuid import UUID
from typing import Optional
from pydantic import SecretStr
from ..utils.agent_tools import get_all_goods

load_dotenv()


class AgentService:
    def __init__(self, db: Optional[Session] = None):
        self.user_memories = {}
        self.db = db
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.2,
            api_key=SecretStr(environ["GROQ_KEY"]),
            max_tokens=1024,
        )

        # Setup tools untuk agent
        self.tools = self._setup_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Kamu adalah AI yang bisa memakai tools. Kamu membantu user mengelola barang dan penjualan mereka.",
                ),
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
            verbose=True,
        )

    def _setup_tools(self):
        """Setup semua tools yang tersedia untuk agent"""
        tools = []

        # Tool untuk mendapatkan semua barang
        def get_all_goods_wrapper(
            user_id: str, limit: int = 10, page_index: int = 1, q: Optional[str] = None
        ) -> str:
            if self.db is None:
                return "Error: Database session tidak tersedia"
            return get_all_goods(
                db=self.db,
                user_id=UUID(self.user_id) if isinstance(user_id, str) else user_id,
                limit=limit,
                page_index=page_index,
                q=q,
            )

        get_all_goods_tool = Tool(
            name="get_all_goods",
            func=get_all_goods_wrapper,
            description="Mengambil daftar semua barang (goods) milik user. Mengembalikan text list dengan detail barang seperti nama, kategori, harga, dan stok. Parameter: limit (optional, default 10), page_index (optional, default 1), q (optional, untuk pencarian)",
        )
        tools.append(get_all_goods_tool)

        return tools

    def get_memory(self, user_id: str):
        if user_id not in self.user_memories:
            self.user_memories[user_id] = []
        return self.user_memories[user_id]

    def chat(self, db: Session, user_id: str, prompt: str):
        self.db = db
        self.user_id = user_id
        memory = self.get_memory(user_id)

        messages = (
            [
                SystemMessage(
                    content="Kamu adalah asisten AI untuk mengelola barang dan penjualan."
                )
            ]
            + memory
            + [HumanMessage(content=prompt)]
        )

        response = self.agent_executor.invoke({"input": messages})

        output = response["output"]

        memory.append(HumanMessage(content=prompt))
        memory.append(AIMessage(content=output))

        if len(memory) > 6:
            memory.pop(0)
            memory.pop(0)

        return output
