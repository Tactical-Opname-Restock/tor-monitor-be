import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from os import environ

from .routers import auth, goods, sales

load_dotenv()
logger = logging.getLogger(__name__)
logging.info("Starting FastAPI app")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081" if environ.get("DEV_KEY") == "dev" else "*"
    ],  # Allow only this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth.router)
app.include_router(goods.router)
app.include_router(sales.router)
