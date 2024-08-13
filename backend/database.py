import os
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client['cacao_knowledge_base']