from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["medivault"]
patients_collection = db["patients"]

# Print database info
print("\nDatabase Information:")
print("--------------------")
print(f"Database name: {db.name}")
print(f"Collections: {db.list_collection_names()}")

# Print collection info
print("\nPatients Collection Information:")
print("------------------------------")
print(f"Number of documents: {patients_collection.count_documents({})}")

# Print sample documents
print("\nSample Documents:")
print("----------------")
for doc in patients_collection.find().limit(5):
    print(doc) 