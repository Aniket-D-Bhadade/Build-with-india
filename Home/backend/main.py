from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re
import logging
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not MONGO_URI or not GEMINI_API_KEY:
    logger.error("Missing required environment variables")
    raise ValueError("Missing required environment variables")

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI)
    # Test the connection
    client.server_info()
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

db = client["medivault"]
patients_collection = db["patients"]

# Configure Gemini AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Successfully configured Gemini AI")
except Exception as e:
    logger.error(f"Failed to configure Gemini AI: {str(e)}")
    raise

# FastAPI App
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Data Model
class Query(BaseModel):
    command: str

# Convert Natural Language to MongoDB Query
def convert_to_query(command: str):
    try:
        logger.info(f"Converting command to query: {command}")
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(
            f"""
            Convert the following natural language command into a valid MongoDB query.
            Only return a JSON object with no extra text, no explanations, and no markdown formatting.
            For timestamps, use the current date in ISO format.
            
            JSON Format:
            {{
                "operation": "<insert/find/update/delete>",
                "query": <MongoDB query object>
            }}

            Example 1:
            User input: "Add a patient named John Smith"
            Correct JSON:
            {{
                "operation": "insert",
                "query": {{"name": "John Smith", "created_at": "2024-03-10T12:00:00Z"}}
            }}

            Example 2:
            User input: "Store the data of Aniket bhadade"
            Correct JSON:
            {{
                "operation": "insert",
                "query": {{"name": "Aniket bhadade", "created_at": "2024-03-10T12:00:00Z"}}
            }}

            Command: {command}
            """
        )

        raw_response = response.text.strip()
        logger.info(f"Raw AI Response: {raw_response}")

        # Clean up the JSON string
        clean_json = re.sub(r"```json|```", "", raw_response).strip()
        clean_json = clean_json.replace("ISODate()", '"2024-03-10T12:00:00Z"')
        
        try:
            query_dict = json.loads(clean_json)
            logger.info(f"Parsed query: {query_dict}")
            
            # Ensure created_at is present for insert operations
            if query_dict.get("operation") == "insert" and "created_at" not in query_dict.get("query", {}):
                query_dict["query"]["created_at"] = "2024-03-10T12:00:00Z"
                
            return query_dict
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return f"AI response is not valid JSON. Debug: {clean_json}"

        # Validate required keys
        if not isinstance(query_dict, dict) or "operation" not in query_dict or "query" not in query_dict:
            logger.error(f"Invalid query format: {query_dict}")
            return f"Invalid query format received from AI. Debug: {clean_json}"

        return query_dict

    except Exception as e:
        logger.error(f"Query conversion error: {str(e)}")
        return f"Query Conversion Error: {str(e)}"

# Process Natural Language Query
@app.post("/process_command/", response_class=PlainTextResponse)
async def process_command(query: Query):
    try:
        logger.info(f"Processing command: {query.command}")
        query_data = convert_to_query(query.command)

        # If AI response is invalid, return for debugging
        if isinstance(query_data, str):
            logger.error(f"Invalid query data: {query_data}")
            return query_data

        operation = query_data.get("operation")
        query_body = query_data.get("query")

        if operation == "insert":
            result = patients_collection.insert_one(query_body)
            logger.info(f"Inserted document with ID: {result.inserted_id}")
            return "✅ Patient data has been successfully stored in the database."

        elif operation == "find":
            results = list(patients_collection.find(query_body, {"_id": 0}))
            logger.info(f"Found {len(results)} matching records")
            return (
                "🔍 Matching patient records:\n" + "\n".join(str(record) for record in results)
                if results else "❌ No matching patient records found."
            )

        elif operation == "delete":
            result = patients_collection.delete_many(query_body)
            logger.info(f"Deleted {result.deleted_count} records")
            return f"🗑️ {result.deleted_count} patient record(s) deleted."

        elif operation == "update":
            update_data = query_data.get("update", {})
            result = patients_collection.update_many(query_body, {"$set": update_data})
            logger.info(f"Updated {result.modified_count} records")
            return f"✏️ {result.modified_count} patient record(s) updated."

        else:
            logger.error(f"Invalid operation type: {operation}")
            return "⚠️ Invalid operation type. Please provide a valid command."

    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return f"❌ An error occurred while processing the command: {str(e)}"
