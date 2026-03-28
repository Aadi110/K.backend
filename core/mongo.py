import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)

try:
    client.server_info()
    print("You successfully connected to MongoDB!")
except Exception as e:
    print("connection failed", e)
    
db = client["kishan"]

if client:
    print("connection successful")
else:
    print("connection failed")
    
user_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]
