# app/main.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
import pyodbc
from sentence_transformers import SentenceTransformer, util
import numpy as np
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Set up CORS middleware to allow OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS
    allow_headers=["*"],  # Allows all headers
)

# Load the model for embedding
# model = SentenceTransformer('all-MiniLM-L6-v2')

# Database connection string (update with your actual values)
# DB_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=db;DATABASE=YourDatabaseName;UID=sa;PWD=YourPassword"

# In-memory storage for ticket embeddings
idea_data = {
    "texts": [],          # List of ticket texts
    "embeddings": []      # List of embeddings corresponding to each text
}

# Data model for incoming similarity request
class TicketRequest(BaseModel):
    description: str

# Function to load tickets from the database and store embeddings in memory
def load_tickets():
    global idea_data

#     with pyodbc.connect(DB_CONNECTION_STRING) as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT ticket_id, ticket_text FROM tickets")
#
#         # Fetch all tickets and compute embeddings once
#         idea_data["texts"] = [row[1] for row in cursor.fetchall()]
#         idea_data["embeddings"] = model.encode(idea_data["texts"], convert_to_tensor=True)

# Startup event to initialize ticket embeddings in memory
@app.on_event("startup")
async def startup_event():
    load_tickets()

# Similarity endpoint to find the most similar ticket
@app.post("/ideas/similarity")
async def get_ideas_similarity(request: TicketRequest):
    # Embed the input text
#     input_embedding = model.encode(request.text, convert_to_tensor=True)
#
#     # Calculate similarity scores with preloaded embeddings
#     similarities = util.cos_sim(input_embedding, idea_data["embeddings"]).squeeze()
#
#     # Find the ticket with the highest similarity
#     best_match_idx = np.argmax(similarities)
#     best_match_score = similarities[best_match_idx].item()

    return {
        "data": [
            {
                "id": "11",
                "status": "in production",
                "subject": "Transferring contracts",
                "description": "There are problems for transferring contracts from one supplier, we need to reduce time it takes for one supplier to request information",
                "similarity_score": 99,
                "created_at": 1731155600
            },
            {
                "id": "22",
                "status": "in development",
                "subject": "Introducing titan alloys in towers",
                "description": "There are new cool titan allows that could be used for building electricity towers, we should use them. They are expensive, but their longevity and maintenance is neglible",
                "similarity_score": 85,
                "created_at": 1699619600
            },
            {
                "id": "33",
                "status": "rejected",
                "subject": "Introduing network overlays under rivers",
                "description": "It would be cool to lay down network cables down the rivers. Most people live near rivers anyway. It would be cool to lay them down as it should be easy to put them in. It will also be easy to maintain unless it is winter. Now that I think about it it might be a bad idea, but please still consider it. Maybe we have a chance moving forward with this.",
                "similarity_score": 79,
                "created_at": 1573475600
            }
        ]
    }